#!/usr/bin/env python3
#
import json
import random
import re
import signal
import string
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from subprocess import DEVNULL
from typing import Optional
from PySide6.QtCore import Qt

from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QStyle,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from cute_sway_recorder.screen_selection import ScreenSelectionDialog

PATTERN_FILE_WITH_SUFFIX = re.compile(r".*\..*")


def available_screens():
    """
    Returns a list of all available outputs via `swaymsg -t get_outputs`, e.g.:
    ['eDP-1', 'HDMI-A-1']
    """
    out = subprocess.check_output(["swaymsg", "-t", "get_outputs"], text=True)
    return [o["name"] for o in json.loads(out)]


def set_buttons_state(*btns, enabled: bool):
    for b in btns:
        b.setEnabled(enabled)


def shrink_home(path: str) -> str:
    """
    Removes the tilde from path
    /home/user/x -> ~/x
    """
    return path.replace(str(Path.home()), "~")


def select_area() -> Optional[str]:
    """
    Launch slurp to capture a region of the screen, returns its output in the following format:
    <x>,<y> <width>x<height>

    If slurp is cancelled (by hitting escape), returns None
    """
    cmd = ["slurp", "-f", "%x,%y %wx%h"]
    proc = subprocess.run(cmd, capture_output=True)
    if proc.returncode == 0:
        return proc.stdout.decode().strip()
    return None


def make_default_file_dst() -> str:
    """
    Create a sensible (as much as possible, you know) default name for videos that weren't given a
    specific destination path.

    Example result: /home/user/Videos/cute-sway-recording-2021-10-10_09-30-48.mp4
    """
    identifier = "".join(random.choices(string.ascii_letters, k=5))
    pathstr = f"~/Videos/cute-{identifier}.mp4"
    return str(Path(pathstr).expanduser().absolute())


def start_recording(
    file_dst, include_audio: bool = False, area: str = None, screen: str = None
) -> subprocess.Popen:
    """
    Launches a `wf-recorder` process and returns a Popen object representing
    it.

    area is a description of a rectangular area on the screen, of the
    following format: <x>,<y> <width>x<height>
    Same output as the `slurp` command (https://github.com/emersion/slurp).

    If area is None, record the whole monitor. If there's more than one monitor, then param screen
    decides which one to record. screen can be taken from `swaymsg -t get_outputs`.
    e.g.: HDMI-A-1

    Note that only one of area and screen should be passed, since area encompasses the screen info
    as well (by specifying coordinates larger than the first monitor size).

    Saves the recording to file_dst, which is a path-like object.
    """
    if area and screen:
        raise ValueError("Only one of area and screen should be passed")

    if file_dst is None:
        file_dst = Path().absolute()
    else:
        Path(file_dst).parent.mkdir(parents=True, exist_ok=True)

    params = ["wf-recorder", "-f", file_dst]
    if include_audio:
        params.append("--audio")
    if area:
        params.append("--geometry")
        params.append(area)
    if screen:
        params.append("--output")
        params.append(screen)
    return subprocess.Popen(params)


class CuteRecorderQtApplication:
    """
    Regular class handling state-y GUI stuff
    """

    def __init__(self):
        self.selected_area = None
        self.recorder_proc = None
        self.selected_screen = None
        self.file_dst = make_default_file_dst()
        self.is_whole_screen_selected = False

        self.app = QApplication(sys.argv)
        self.app.setApplicationDisplayName("Cute Sway Recorder")
        self.app.setDesktopFileName("cute-sway-recorder")

        ## Create labels
        self.lbl_selected_area = QLabel("Selected area: None")
        self.lbl_file_dst = QLabel(f"Saving to {shrink_home(self.file_dst)}")
        self.lbl_is_recording = QLabel("Not recording")
        self.lbl_whole_screen_notice = QLabel(
            '<font color="salmon">This window will be minimized. <br/>'
            "Click the tray icon to stop recording</font>"
        )
        self.lbl_whole_screen_notice.hide()

        ## Create buttons
        self.btn_select_area = QPushButton("Select an area")
        self.btn_select_whole_screen = QPushButton("Select whole screen")
        self.btn_start_recording = QPushButton("Start recording")
        self.btn_stop_recording = QPushButton("Stop recording")
        self.btn_pick_dest = QPushButton("Pick file destination")
        self.checkbox_use_audio = QCheckBox("Record audio")

        ## Connect buttons on-click actions
        self.btn_select_area.clicked.connect(self.btn_onclick_select_area)
        self.btn_select_whole_screen.clicked.connect(self.btn_onclick_select_whole_screen)
        self.btn_start_recording.clicked.connect(self.btn_onclick_start_recording)
        self.btn_stop_recording.clicked.connect(self.btn_onclick_stop_recording)
        self.btn_stop_recording.setEnabled(False)
        self.btn_pick_dest.clicked.connect(self.btn_onclick_pick_dst)

        ## Show window
        self.window = QWidget()
        self.window.setWindowTitle("Cute Sway Recorder")
        self.window.setLayout(self.layout())
        self.window.show()

        ## Verify executable dependencies
        self.cmd_available_or_exit("wf-recorder")
        self.cmd_available_or_exit("slurp")

        ## Define whole-screen icon (not showing yet)
        self.icon = QSystemTrayIcon(self.window)
        self.icon.setIcon(self.window.style().standardIcon(QStyle.SP_MediaStop))
        self.icon.activated.connect(self.tray_icon_activated_handler)

    def layout(self):
        grid = QGridLayout()

        grid.addWidget(self.lbl_selected_area, 0, 0)
        grid.addWidget(self.btn_select_area, 0, 1)
        grid.addWidget(self.btn_select_whole_screen, 0, 2)

        grid.addWidget(self.lbl_file_dst, 1, 0)
        grid.addWidget(self.btn_pick_dest, 1, 1, 1, 2)

        recording_btns = QHBoxLayout()
        recording_btns.addWidget(self.btn_start_recording)
        recording_btns.addWidget(self.btn_stop_recording)

        lbl_recording_box = QGroupBox()
        lbl_recording_layout = QVBoxLayout()
        lbl_recording_layout.addWidget(self.lbl_is_recording, alignment=Qt.AlignCenter)
        lbl_recording_box.setLayout(lbl_recording_layout)

        layout = QVBoxLayout()
        layout.addWidget(self.lbl_whole_screen_notice)
        layout.addWidget(lbl_recording_box)
        layout.addLayout(grid)
        layout.addWidget(self.checkbox_use_audio)
        layout.addLayout(recording_btns)
        return layout

    def cmd_available_or_exit(self, cmd: str):
        """
        Show an error popup if cmd is not available in PATH, then exit.
        Availability is checked via `which`
        """
        proc = subprocess.run(["which", cmd], stderr=DEVNULL, stdout=DEVNULL)
        if proc.returncode != 0:
            warning = QMessageBox(
                QMessageBox.Critical,
                "Executable not found",
                f"<code>{cmd}</code> not in PATH please install it :(",
                parent=self.window,
            )
            warning.exec()
            sys.exit(1)

    def tray_icon_activated_handler(self, reason):
        # tray icon was clicked
        if reason == QSystemTrayIcon.Trigger:
            self.window.show()
            self.icon.hide()
            self.btn_onclick_stop_recording()

    def btn_onclick_select_area(self):
        self.selected_area = select_area() or self.selected_area
        self.selected_screen = None
        self.lbl_selected_area.setText(f"Selected area: {self.selected_area}")
        self.is_whole_screen_selected = False
        self.lbl_whole_screen_notice.hide()

    def btn_onclick_select_whole_screen(self):
        screens = available_screens()
        if len(screens) > 1:
            selected_screen_idx = ScreenSelectionDialog(screens, parent=self.window).exec()
            if selected_screen_idx == -1:
                return
            self.selected_screen = screens[selected_screen_idx]
        self.selected_area = None
        self.lbl_selected_area.setText(f"Selected screen: {self.selected_screen}")
        self.lbl_whole_screen_notice.show()
        self.is_whole_screen_selected = True

    def btn_onclick_start_recording(self):
        # confirm dest file override
        if Path(self.file_dst).exists():
            resp = QMessageBox.question(
                self.window,
                "File exists",
                f"Override {self.file_dst}?",
                QMessageBox.Yes,
                QMessageBox.No,
            )
            if resp == QMessageBox.No:
                self.lbl_is_recording.setText("Not recording")
                return

        # show error message and return if no area was selected
        if self.selected_area is None and self.selected_screen is None:
            warning = QMessageBox(
                QMessageBox.Critical,
                "No area selected",
                "Kindly select an area or pick a screen :)",
                parent=self.window,
            )
            warning.exec()
            return

        # show tray icon if recording fullscreen
        if self.is_whole_screen_selected:
            self.window.hide()
            self.icon.show()

        # disable all buttons other than stop record
        self.btn_stop_recording.setEnabled(True)
        set_buttons_state(
            self.btn_pick_dest,
            self.btn_select_area,
            self.btn_select_whole_screen,
            self.btn_start_recording,
            enabled=False,
        )

        # launch wf-recorder
        self.recorder_proc = start_recording(
            self.file_dst,
            include_audio=self.checkbox_use_audio.isChecked(),
            area=self.selected_area,
            screen=self.selected_screen,
        )

        # set respective labels
        self.lbl_is_recording.setText('<font color="Red">RECORDING</font>')
        self.lbl_file_dst.setText(f"Saving as: {shrink_home(self.file_dst)}")

    def btn_onclick_stop_recording(self):
        self.btn_stop_recording.setEnabled(False)
        set_buttons_state(
            self.btn_pick_dest,
            self.btn_select_area,
            self.btn_select_whole_screen,
            self.btn_start_recording,
            enabled=True,
        )
        self.recorder_proc.send_signal(signal.SIGINT)
        self.lbl_is_recording.setText(
            '<font color="Green">Done recording - successfuly saved!</font>'
        )
        self.lbl_file_dst.setText(f"Saved to: {shrink_home(self.file_dst)}")

    def btn_onclick_pick_dst(self):
        dest: str = QFileDialog.getSaveFileName(parent=self.window)[0]
        if dest == "":
            return
        if not PATTERN_FILE_WITH_SUFFIX.match(dest):
            dest = f"{dest}.mp4"
        self.file_dst = dest
        self.lbl_file_dst.setText(f"Saving as: {shrink_home(dest)}")

    def exec(self):
        return self.app.exec()


def main():
    subprocess.run(["swaymsg", 'for_window [app_id="cute-sway-recorder"] floating enable'])
    app = CuteRecorderQtApplication()
    app.exec()


if __name__ == "__main__":
    main()
