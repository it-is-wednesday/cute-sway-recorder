#!/usr/bin/env python3

import signal
import subprocess
import sys
from pathlib import Path
from subprocess import DEVNULL
from typing import Union

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import (
    QApplication,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStyle,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from .common import SelectedArea, SelectedScreen
from .config_area import ConfigArea

STATUS_DELAY = '<font color="indianred">Starting in {}...</font>'
STATUS_RECORDING = '<font color="Red">RECORDING</font>'
STATUS_NOT_RECORDING = "Not recording"
STOP_RECORDING = "Stop recording"


def wf_recorder(
    selection: Union[SelectedArea, SelectedScreen],
    file_dst,
    flags,
    include_audio: bool = False,
) -> subprocess.Popen:
    """
    Launches a `wf-recorder` process and returns a Popen object representing it. Records a portion
    of a screen or a whole screen.

    Saves the recording to file_dst, which is a path-like object.
    Append user submitted flags to the end of params
    Note: user can't enter parameters with spaces, e.g., --audio device1 device2
    """
    Path(file_dst).parent.mkdir(parents=True, exist_ok=True)
    flags = flags.strip().split()

    params = ["wf-recorder", "-f", file_dst]
    if include_audio:
        params.append("--audio")
    if isinstance(selection, SelectedArea):
        params.append("--geometry")
        params.append(selection)
    if isinstance(selection, SelectedScreen):
        params.append("--output")
        params.append(selection)
    params.extend(flags)  # adds all items of flags to the end of params
    return subprocess.Popen(params)


class CuteRecorderQtApplication(QMainWindow):
    """
    Regular class handling state-y GUI stuff
    """

    def __init__(self):
        QMainWindow.__init__(self)
        self.recorder_proc = None

        self.delay_timer = QTimer()
        self.delay_timer.setInterval(1000)
        self.delay_timer.timeout.connect(self.on_delay_timer_tick)

        self.setWindowTitle("Cute Sway Recorder")
        self.config_area = ConfigArea(self)

        ## Create labels
        self.lbl_status = QLabel("Not recording")

        ## Create buttons
        self.btn_start_recording = QPushButton("Start recording")
        self.btn_stop_recording = QPushButton(STOP_RECORDING)

        ## Connect buttons on-click actions
        self.btn_start_recording.clicked.connect(self.btn_onclick_start_recording)
        self.btn_stop_recording.clicked.connect(self.btn_onclick_stop_recording)
        self.btn_stop_recording.setEnabled(False)

        ## Verify executable dependencies
        self.cmd_available_or_exit("wf-recorder")
        self.cmd_available_or_exit("slurp")

        ## Setup layout
        self.setup_layout()

        ## Define whole-screen icon (not showing yet)
        self.icon = QSystemTrayIcon(self)
        self.icon.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))
        self.icon.activated.connect(self.tray_icon_activated_handler)

    def on_delay_timer_tick(self):
        self.delay_time_left -= 1
        if self.delay_time_left <= 0:
            self.delay_timer.stop()
            self.start_recording()
            self.btn_stop_recording.setText(STOP_RECORDING)
            return
        self.lbl_status.setText(STATUS_DELAY.format(self.delay_time_left))

    def setup_layout(self):
        recording_btns = QHBoxLayout()
        recording_btns.addWidget(self.btn_start_recording)
        recording_btns.addWidget(self.btn_stop_recording)

        lbl_recording_box = QGroupBox()
        lbl_recording_layout = QVBoxLayout()
        lbl_recording_layout.addWidget(self.lbl_status, alignment=Qt.AlignCenter)
        lbl_recording_box.setLayout(lbl_recording_layout)

        layout = QVBoxLayout()
        layout.addWidget(lbl_recording_box)
        layout.addLayout(self.config_area)
        layout.addLayout(recording_btns)

        wid = QWidget()
        wid.setLayout(layout)
        self.setCentralWidget(wid)

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
                parent=self,
            )
            warning.exec()
            sys.exit(1)

    def tray_icon_activated_handler(self, reason):
        # tray icon was clicked
        if reason == QSystemTrayIcon.Trigger:
            self.show()
            self.icon.hide()
            self.btn_onclick_stop_recording()

    def btn_onclick_start_recording(self):
        self.config = self.config_area.create_config()
        if not self.config:
            return

        if self.config.file_dest.exists():
            resp = QMessageBox.question(
                self,
                "File exists",
                f"Override {self.config.file_dest}?",
                QMessageBox.Yes,
                QMessageBox.No,
            )
            if resp == QMessageBox.No:
                self.lbl_status.setText(STATUS_NOT_RECORDING)
                return

        # disable all buttons other than stop record
        self.btn_stop_recording.setEnabled(True)
        self.btn_start_recording.setEnabled(False)
        self.config_area.set_buttons_enabled(False)

        if self.config.delay > 0:
            self.delay_time_left = self.config.delay
            self.delay_timer.start()
            self.lbl_status.setText(STATUS_DELAY.format(self.delay_time_left))
            self.btn_stop_recording.setText("Cancel countdown")
        else:
            self.start_recording()

    def start_recording(self):
        if not self.config:
            return
        conf = self.config

        self.lbl_status.setText(STATUS_RECORDING)

        # show tray icon if recording whole screen
        if isinstance(conf.selection, SelectedScreen):
            self.hide()
            self.icon.show()

        # launch wf-recorder
        self.recorder_proc = wf_recorder(
            conf.selection,
            conf.file_dest,
            conf.flags,
            include_audio=conf.include_audio,
        )

    def btn_onclick_stop_recording(self):
        self.btn_stop_recording.setEnabled(False)
        self.btn_start_recording.setEnabled(True)
        self.config_area.set_buttons_enabled(True)

        if self.delay_timer.isActive():
            self.delay_timer.stop()
            self.lbl_status.setText(STATUS_NOT_RECORDING)
            return

        if self.recorder_proc:
            self.recorder_proc.send_signal(signal.SIGINT)

        self.lbl_status.setText('<font color="Green">Saved!</font>')


def main():
    subprocess.run(
        ["swaymsg", 'for_window [app_id="cute-sway-recorder"] floating enable']
    )
    app = QApplication(sys.argv)
    app.setApplicationDisplayName("Cute Sway Recorder")
    app.setDesktopFileName("cute-sway-recorder")
    window = CuteRecorderQtApplication()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
