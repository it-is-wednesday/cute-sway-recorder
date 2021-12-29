import random
import re
import string
from pathlib import Path
from PySide6.QtCore import QSize

from PySide6.QtWidgets import QFileDialog, QGroupBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

PATTERN_FILE_WITH_SUFFIX = re.compile(r".*\..*")


def shrink_home(path: str) -> str:
    """
    Removes the tilde from path
    /home/user/x -> ~/x
    """
    return path.replace(str(Path.home()), "~")


def make_default_file_dest() -> Path:
    """
    Create a sensible (as much as possible, you know) default name for videos that weren't given a
    specific destination path.

    Example result: /home/user/Videos/cute-NOwPn.mp4
    """
    identifier = "".join(random.choices(string.ascii_letters, k=5))
    pathstr = f"~/Videos/cute-{identifier}.mp4"
    return Path(pathstr).expanduser().absolute()


class FileDestGroupbox(QGroupBox):
    def __init__(self, window):
        super().__init__()
        self.window = window

        self.file_dest = make_default_file_dest()

        self.lbl_file_dst = QLabel()
        self.update_file_dest_label()

        self.btn_pick_dest = QPushButton("Pick file\ndestination")
        self.btn_generate_random_dest = QPushButton("Random name")

        self.btn_pick_dest.clicked.connect(self.btn_onclick_pick_dst)
        self.btn_generate_random_dest.clicked.connect(self.btn_onclick_generate_random_dest)

        self.setup_layout()

    def setup_layout(self):
        buttons_size = QSize(115, 35)
        self.btn_pick_dest.setFixedSize(buttons_size)
        self.btn_generate_random_dest.setFixedSize(buttons_size)

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.btn_pick_dest)
        buttons_layout.addWidget(self.btn_generate_random_dest)

        layout = QVBoxLayout()
        layout.addWidget(self.lbl_file_dst)
        layout.addLayout(buttons_layout)

        self.setLayout(layout)

    def btn_onclick_pick_dst(self):
        dest: str = QFileDialog.getSaveFileName(parent=self.window)[0]
        if dest == "":
            return
        # add suffix if user hasn't given a suffix in the QFileDialog
        if not PATTERN_FILE_WITH_SUFFIX.match(dest):
            dest = f"{dest}.mp4"
        self.file_dest = Path(dest)
        self.update_file_dest_label()

    def update_file_dest_label(self):
        self.lbl_file_dst.setText(f"Saving as: {shrink_home(str(self.file_dest))}")

    def btn_onclick_generate_random_dest(self):
        self.file_dest = make_default_file_dest()
        self.update_file_dest_label()

    def set_buttons_enabled(self, enabled: bool):
        self.btn_pick_dest.setEnabled(enabled)
        self.btn_generate_random_dest.setEnabled(enabled)
