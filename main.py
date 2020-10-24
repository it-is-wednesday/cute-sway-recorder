#!/usr/bin/env python3
import sys
import subprocess
import signal
from datetime import datetime
from pathlib import Path
from PySide2.QtWidgets import (
    QApplication,
    QPushButton,
    QLabel,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QFileDialog,
    QMessageBox,
)


def select_area() -> str:
    """
    Launch slurp to capture a region of the screen, returns its output in the following format:
    <x>,<y> <width>x<height>
    """
    cmd = ["slurp", "-f", "%x,%y %wx%h"]
    return subprocess.run(cmd, capture_output=True).stdout.decode().strip()


def make_file_dst() -> str:
    """
    Create a sensible (as much as possible, you know) default name for videos that weren't given a
    specific destination path.
    """
    date = format(datetime.now(), "%Y-%m-%d_%H-%M-%S")
    pathstr = f"~/Videos/cute-wayland-recording-{date}.mp4"
    return str(Path(pathstr).expanduser().absolute())


def start_recording(area: str, file_dst) -> subprocess.Popen:
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

    return subprocess.Popen(["wf-recorder", "--geometry", area, "-f", file_dst])


class CuteRecorderQtApplication:
    """
    Regular class handling state-y GUI stuff
    """

    def __init__(self):
        self.app = QApplication(sys.argv)

        self.recorder_proc = None
        self.selected_area = None
        self.file_dst = make_file_dst()

        self.btns_row = QHBoxLayout()

        # button - launch area selection via slurp
        self.btn_select_area = QPushButton("Select an area")
        self.btn_select_area.clicked.connect(self.btn_onclick_select_area)
        self.btns_row.addWidget(self.btn_select_area)

        # button - launch wf-recorder
        self.btn_start_recording = QPushButton("Start recording")
        self.btn_start_recording.clicked.connect(self.btn_onclick_start_recording)
        self.btns_row.addWidget(self.btn_start_recording)

        # button - send interrupt to wf-recorder process
        self.btn_stop_recording = QPushButton("Stop recording")
        self.btn_stop_recording.clicked.connect(self.btn_onclick_stop_recording)
        self.btns_row.addWidget(self.btn_stop_recording)

        # button - pick file destination for wf-recorder output
        self.btn_pick_dest = QPushButton("Pick file destination")
        self.btn_pick_dest.clicked.connect(self.btn_onclick_pick_dst)
        self.btns_row.addWidget(self.btn_pick_dest)

        self.layout = QVBoxLayout()
        self.layout.addLayout(self.btns_row)

        # Label - selected screen area
        self.lbl_selected_area = QLabel("Selected area: None")
        self.layout.addWidget(self.lbl_selected_area)

        # Label - file destination
        self.lbl_file_dst = QLabel("Saving to ~/Videos")
        self.layout.addWidget(self.lbl_file_dst)

        # Label - recording status
        self.lbl_is_recording = QLabel("Not recording")
        self.layout.addWidget(self.lbl_is_recording)

        self.window = QWidget()
        self.window.setLayout(self.layout)
        self.window.show()

    def btn_onclick_select_area(self):
        self.selected_area = select_area()
        self.lbl_selected_area.setText(f"Selected area: {self.selected_area}")

    def btn_onclick_start_recording(self):
        if self.selected_area is None:
            warning = QMessageBox(
                QMessageBox.Critical,
                "No area selected",
                "Kindly select an area :)",
                parent=self.window,
            )
            warning.open()
            return

        self.recorder_proc = start_recording(self.selected_area, self.file_dst)
        self.lbl_is_recording.setText('<font color="Red">RECORDING</font>')
        self.lbl_file_dst.setText(f"Saving as: {self.file_dst}")

    def btn_onclick_stop_recording(self):
        self.recorder_proc.send_signal(signal.SIGINT)
        self.lbl_is_recording.setText("Done recording - successfuly saved!")
        self.lbl_file_dst.setText(f"Saved to: {self.file_dst}")

    def btn_onclick_pick_dst(self):
        dst = QFileDialog.getSaveFileName(parent=self.window)[0]
        self.file_dst = dst
        self.lbl_file_dst.setText(f"Saving as: {dst}")

    def exec(self):
        return self.app.exec_()


def main():
    app = CuteRecorderQtApplication()
    app.exec()


if __name__ == "__main__":
    main()
