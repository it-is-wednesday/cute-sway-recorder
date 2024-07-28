import random
import re
import string
from pathlib import Path

from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
)

from .common import CONFIG_BUTTON_WIDTH

PATTERN_FILE_WITH_SUFFIX = re.compile(r".*\..*")


def shrink_home(path: str) -> str:
    """
    Removes the tilde from path
    /home/user/x -> ~/x
    """
    return path.replace(str(Path.home()), "~")


def make_random_file_stem() -> str:
    """
    Create a default basename (no extension, no path) for default videos to be used by
    make_default_file_dest and "Random Name"
    Example result: cute-sbh42
    """
    identifier = "".join(random.choices(string.ascii_letters, k=5))
    return f"cute-{identifier}"

def make_default_file_dest() -> Path:
    """
    Create a sensible (as much as possible, you know) default name for videos that weren't given a
    specific destination path.

    Example result: /home/user/Videos/cute-NOwPn.mp4
    """
    identifier = make_random_file_stem()
    pathstr = f"~/Videos/{identifier}.mp4"
    return Path(pathstr).expanduser().absolute()


class FileDestGroup(QHBoxLayout):
    def __init__(self, window):
        super().__init__()
        self.window = window

        self.file_dest = make_default_file_dest()

        self.lbl_file_dst = QLabel()
        self.update_file_dest_label()

        self.btn_pick_dest = QPushButton("Pick path")
        self.btn_generate_random_dest = QPushButton("Random name")

        self.btn_pick_dest.clicked.connect(self.btn_onclick_pick_dst)
        self.btn_generate_random_dest.clicked.connect(
            self.btn_onclick_generate_random_dest
        )

        self.setup_layout()

    def setup_layout(self):
        self.btn_generate_random_dest.setFixedWidth(CONFIG_BUTTON_WIDTH)
        self.btn_pick_dest.setFixedWidth(CONFIG_BUTTON_WIDTH)

        self.addWidget(self.lbl_file_dst)
        self.addWidget(self.btn_pick_dest)
        self.addWidget(self.btn_generate_random_dest)

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
        self.lbl_file_dst.setText(f"{shrink_home(str(self.file_dest))}")

    def btn_onclick_generate_random_dest(self):
        # try to just change the stem to a random stem
        if self.file_dest.stem:
            stem = make_random_file_stem()
            suffix = self.file_dest.suffix or ".mp4"
            # NOTE: if python version is >3.9, switch to Path.with_stem
            self.file_dest = self.file_dest.with_name(stem).with_suffix(suffix)
        else:
            # this should never happen for a valid file_dest
            # in this case, reset file dest to default
            self.file_dest = make_default_file_dest()
        self.update_file_dest_label()

    def set_buttons_enabled(self, enabled: bool):
        self.btn_pick_dest.setEnabled(enabled)
        self.btn_generate_random_dest.setEnabled(enabled)
