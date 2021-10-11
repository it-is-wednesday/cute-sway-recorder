#!/usr/bin/env python3
#
import json
import signal
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from subprocess import DEVNULL

from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QGridLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QStyle,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

FULLSCREEN_SELECTED_TEXT = """Selected area: whole screen. <br/>
<font color="salmon">this window will be minimized. <br/>
click the tray icon to stop recording</font>"""


def set_buttons_state(*btns, enabled: bool):
    for b in btns:
        b.setEnabled(enabled)


def shrink_home(path: str) -> str:
    """
    Removes the tilde from path
    /home/user/x -> ~/x
    """
    return path.replace(str(Path.home()), "~")


def select_area() -> str:
    """
    Launch slurp to capture a region of the screen, returns its output in the following format:
    <x>,<y> <width>x<height>
    """
    cmd = ["slurp", "-f", "%x,%y %wx%h"]
    return subprocess.run(cmd, capture_output=True).stdout.decode().strip()


def get_screen_dimensions() -> str:
    """
    Get dimensions of currently focused screen via swaymsg. Returns a string in the same format as
    `select_area()`.

    If no screen if focused (?), raises ValueError
    """
    outputs = subprocess.check_output(["swaymsg", "-t", "get_outputs"])
    outputs = json.loads(outputs)

    for o in outputs:
        if o["focused"] == True:
            rect = o["rect"]
            return f"0,0 {rect['width']}x{rect['height']}"

    raise ValueError("No focused screen found with `swaymsg -t get_outputs`")


def make_file_dst() -> str:
    """
    Create a sensible (as much as possible, you know) default name for videos that weren't given a
    specific destination path.

    Example result: /home/user/Videos/cute-sway-recording-2021-10-10_09-30-48.mp4
    """
    date = format(datetime.now(), "%Y-%m-%d_%H-%M-%S")
    pathstr = f"~/Videos/cute-sway-recording-{date}.mp4"
    return str(Path(pathstr).expanduser().absolute())


def start_recording(area: str, file_dst, include_audio: bool = False) -> subprocess.Popen:
    """
    Launches a `wf-recorder` process and returns a Popen object representing
    it.

    `area` is a description of a rectangular area on the screen, of the
    following format: <x>,<y> <width>x<height>
    Same output as the `slurp` command (https://github.com/emersion/slurp).

    Saves the recording to `file_dst`, which is a path-like object.
    """
    if file_dst is None:
        file_dst = Path().absolute()
    else:
        Path(file_dst).parent.mkdir(parents=True, exist_ok=True)

    params = ["wf-recorder", "--geometry", area, "-f", file_dst]
    if include_audio:
        params.append("--audio")
    return subprocess.Popen(params)


class CuteRecorderQtApplication:
    """
    Regular class handling state-y GUI stuff
    """

    def __init__(self):
        self.is_whole_screen_selected = False

        self.app = QApplication(sys.argv)
        self.app.setApplicationDisplayName("Cute Sway Recorder")
        self.app.setDesktopFileName("cute-sway-recorder")

        self.selected_area = None
        self.lbl_selected_area = QLabel("Selected area: None")

        self.file_dst = make_file_dst()
        self.lbl_file_dst = QLabel("Saving to ~/Videos")

        self.recorder_proc = None
        self.lbl_is_recording = QLabel("Not recording")

        self.btn_select_area = QPushButton("Select an area")
        self.btn_select_area.clicked.connect(self.btn_onclick_select_area)

        self.btn_select_whole_screen = QPushButton("Select whole screen")
        self.btn_select_whole_screen.clicked.connect(self.btn_onclick_select_whole_screen)

        self.btn_start_recording = QPushButton("Start recording")
        self.btn_start_recording.clicked.connect(self.btn_onclick_start_recording)

        self.btn_stop_recording = QPushButton("Stop recording")
        self.btn_stop_recording.clicked.connect(self.btn_onclick_stop_recording)
        self.btn_stop_recording.setEnabled(False)

        self.btn_pick_dest = QPushButton("Pick file destination")
        self.btn_pick_dest.clicked.connect(self.btn_onclick_pick_dst)

        self.checkbox_use_audio = QCheckBox("Record audio")

        self.btns_grid = QGridLayout()
        self.btns_grid.addWidget(self.btn_select_area, 0, 0)
        self.btns_grid.addWidget(self.btn_select_whole_screen, 0, 1)

        self.btns_grid.addWidget(self.btn_start_recording, 1, 0)
        self.btns_grid.addWidget(self.btn_stop_recording, 1, 1)

        self.btns_grid.addWidget(self.btn_pick_dest, 2, 0)
        self.btns_grid.addWidget(self.checkbox_use_audio, 2, 1)

        self.layout = QVBoxLayout()
        self.layout.addLayout(self.btns_grid)
        self.layout.addWidget(self.lbl_selected_area)
        self.layout.addWidget(self.lbl_file_dst)
        self.layout.addWidget(self.lbl_is_recording)

        self.window = QWidget()
        self.window.setWindowTitle("Cute Sway Recorder")
        self.window.setLayout(self.layout)
        self.window.show()

        self.cmd_available_or_exit("wf-recorder")
        self.cmd_available_or_exit("slurp")

        self.icon = QSystemTrayIcon(self.window)
        self.icon.setIcon(self.window.style().standardIcon(QStyle.SP_MediaStop))
        self.icon.activated.connect(self.tray_icon_activated_handler)

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
        self.selected_area = select_area()
        self.lbl_selected_area.setText(f"Selected area: {self.selected_area}")
        self.is_whole_screen_selected = False

    def btn_onclick_select_whole_screen(self):
        self.selected_area = get_screen_dimensions()
        self.lbl_selected_area.setText(FULLSCREEN_SELECTED_TEXT)
        self.is_whole_screen_selected = True

    def btn_onclick_start_recording(self):
        if self.selected_area is None:
            warning = QMessageBox(
                QMessageBox.Critical,
                "No area selected",
                "Kindly select an area :)",
                parent=self.window,
            )
            warning.exec()
            return

        if self.is_whole_screen_selected:
            self.window.hide()
            self.icon.show()

        self.btn_stop_recording.setEnabled(True)
        set_buttons_state(
            self.btn_pick_dest,
            self.btn_select_area,
            self.btn_select_whole_screen,
            self.btn_start_recording,
            enabled=False,
        )

        self.recorder_proc = start_recording(
            self.selected_area, self.file_dst, include_audio=self.checkbox_use_audio.isChecked()
        )
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
        self.lbl_is_recording.setText("Done recording - successfuly saved!")
        self.lbl_file_dst.setText(f"Saved to: {shrink_home(self.file_dst)}")

    def btn_onclick_pick_dst(self):
        dst = QFileDialog.getSaveFileName(parent=self.window)[0] + ".mp4"
        self.file_dst = dst
        self.lbl_file_dst.setText(f"Saving as: {shrink_home(dst)}")

    def exec(self):
        return self.app.exec()


def main():
    subprocess.run(["swaymsg", 'for_window [app_id="cute-sway-recorder"] floating enable'])
    app = CuteRecorderQtApplication()
    app.exec()


if __name__ == "__main__":
    main()
