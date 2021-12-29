#!/usr/bin/env python3

from pathlib import Path
import signal
import subprocess
import sys
from subprocess import DEVNULL
from typing import Union

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
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

from config_area import ConfigArea
from common import SelectedArea, SelectedScreen


def start_recording(
    selection: Union[SelectedArea, SelectedScreen],
    file_dst,
    include_audio: bool = False,
) -> subprocess.Popen:
    """
    Launches a `wf-recorder` process and returns a Popen object representing it. Records a portion
    of a screen or a whole screen.

    Saves the recording to file_dst, which is a path-like object.
    """
    Path(file_dst).parent.mkdir(parents=True, exist_ok=True)

    params = ["wf-recorder", "-f", file_dst]
    if include_audio:
        params.append("--audio")
    if isinstance(selection, SelectedArea):
        params.append("--geometry")
        params.append(selection)
    if isinstance(selection, SelectedScreen):
        params.append("--output")
        params.append(selection)
    return subprocess.Popen(params)


class CuteRecorderQtApplication:
    """
    Regular class handling state-y GUI stuff
    """

    def __init__(self):
        self.recorder_proc = None

        self.app = QApplication(sys.argv)
        self.app.setApplicationDisplayName("Cute Sway Recorder")
        self.app.setDesktopFileName("cute-sway-recorder")

        ## Create labels
        self.lbl_is_recording = QLabel("Not recording")

        ## Create buttons
        self.btn_start_recording = QPushButton("Start recording")
        self.btn_stop_recording = QPushButton("Stop recording")

        ## Connect buttons on-click actions
        self.btn_start_recording.clicked.connect(self.btn_onclick_start_recording)
        self.btn_stop_recording.clicked.connect(self.btn_onclick_stop_recording)
        self.btn_stop_recording.setEnabled(False)

        ## Show window
        self.window = QWidget()
        self.config_area = ConfigArea(self.window)
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
        recording_btns = QHBoxLayout()
        recording_btns.addWidget(self.btn_start_recording)
        recording_btns.addWidget(self.btn_stop_recording)

        lbl_recording_box = QGroupBox()
        lbl_recording_layout = QVBoxLayout()
        lbl_recording_layout.addWidget(self.lbl_is_recording, alignment=Qt.AlignCenter)
        lbl_recording_box.setLayout(lbl_recording_layout)

        layout = QVBoxLayout()
        layout.addWidget(lbl_recording_box)
        layout.addLayout(self.config_area)
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

    def btn_onclick_start_recording(self):
        config = self.config_area.create_config()
        if not config:
            return

        # confirm dest file override
        if config.file_dest.exists():
            resp = QMessageBox.question(
                self.window,
                "File exists",
                f"Override {config.file_dest}?",
                QMessageBox.Yes,
                QMessageBox.No,
            )
            if resp == QMessageBox.No:
                self.lbl_is_recording.setText("Not recording")
                return

        # show tray icon if recording whole screen
        if isinstance(config.selection, SelectedScreen):
            self.window.hide()
            self.icon.show()

        # disable all buttons other than stop record
        self.btn_stop_recording.setEnabled(True)
        self.btn_start_recording.setEnabled(False)
        self.config_area.set_buttons_enabled(False)

        # launch wf-recorder
        self.recorder_proc = start_recording(
            config.selection,
            config.file_dest,
            include_audio=config.include_audio,
        )

    def btn_onclick_stop_recording(self):
        self.btn_stop_recording.setEnabled(False)
        self.btn_start_recording.setEnabled(True)
        self.config_area.set_buttons_enabled(True)

        if self.recorder_proc:
            self.recorder_proc.send_signal(signal.SIGINT)

        self.lbl_is_recording.setText('<font color="Green">Saved!</font>')

    def exec(self):
        return self.app.exec()


def main():
    subprocess.run(["swaymsg", 'for_window [app_id="cute-sway-recorder"] floating enable'])
    app = CuteRecorderQtApplication()
    app.exec()


if __name__ == "__main__":
    main()
