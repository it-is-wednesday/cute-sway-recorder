import random
import re
import string
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

from PySide6.QtWidgets import QCheckBox, QFileDialog, QGridLayout, QLabel, QMessageBox, QPushButton

from common import SelectedArea, SelectedScreen, available_screens, set_buttons_state
from screen_selection import ScreenSelectionDialog

PATTERN_FILE_WITH_SUFFIX = re.compile(r".*\..*")


@dataclass
class Config:
    selection: Union[SelectedScreen, SelectedArea]
    file_dest: Path
    include_audio: bool


def shrink_home(path: str) -> str:
    """
    Removes the tilde from path
    /home/user/x -> ~/x
    """
    return path.replace(str(Path.home()), "~")


def select_area() -> Optional[SelectedArea]:
    """
    Launch slurp to capture a region of the screen, returns its output in the following format:
    <x>,<y> <width>x<height>

    If slurp is cancelled (by hitting escape), returns None
    """
    cmd = ["slurp", "-f", "%x,%y %wx%h"]
    proc = subprocess.run(cmd, capture_output=True)
    if proc.returncode == 0:
        return SelectedArea(proc.stdout.decode().strip())
    return None


def make_default_file_dest() -> Path:
    """
    Create a sensible (as much as possible, you know) default name for videos that weren't given a
    specific destination path.

    Example result: /home/user/Videos/cute-NOwPn.mp4
    """
    identifier = "".join(random.choices(string.ascii_letters, k=5))
    pathstr = f"~/Videos/cute-{identifier}.mp4"
    return Path(pathstr).expanduser().absolute()


class ConfigArea(QGridLayout):
    def __init__(self, window):
        super().__init__()

        self.lbl_whole_screen_notice = QLabel(
            '<font color="salmon">This window will be minimized. <br/>'
            "Click the tray icon to stop recording</font>"
        )
        self.lbl_whole_screen_notice.hide()

        self.window = window
        self.file_dest = make_default_file_dest()
        self.selected_screen: Optional[SelectedScreen] = None
        self.selected_area = None

        self.lbl_selected_area = QLabel("Selected area: None")
        self.lbl_file_dst = QLabel()
        self.update_file_dest_label()

        self.btn_select_area = QPushButton("Select an area")
        self.btn_select_whole_screen = QPushButton("Select whole screen")
        self.btn_pick_dest = QPushButton("Pick file destination")
        self.btn_generate_random_dest = QPushButton("Random name")
        self.checkbox_use_audio = QCheckBox("Record audio")

        self.btn_select_area.clicked.connect(self.btn_onclick_select_area)
        self.btn_select_whole_screen.clicked.connect(self.btn_onclick_select_whole_screen)
        self.btn_pick_dest.clicked.connect(self.btn_onclick_pick_dst)
        self.btn_generate_random_dest.clicked.connect(self.btn_onclick_generate_random_dest)

        self.addWidget(self.lbl_selected_area, 0, 0)
        self.addWidget(self.btn_select_area, 0, 1)
        self.addWidget(self.btn_select_whole_screen, 0, 2)

        self.addWidget(self.lbl_file_dst, 1, 0)
        self.addWidget(self.btn_pick_dest, 1, 1)
        self.addWidget(self.btn_generate_random_dest, 1, 2)

        self.addWidget(self.checkbox_use_audio, 2, 0)

        self.addWidget(self.lbl_whole_screen_notice, 3, 0)

    def create_config(self) -> Optional[Config]:
        """
        If no area or screen was selected, returns None
        """
        if self.selected_area:
            selection = self.selected_area
        elif self.selected_screen:
            selection = self.selected_screen
        # show error message and return if no area was selected
        else:
            warning = QMessageBox(
                QMessageBox.Critical,
                "No area selected",
                "Kindly select an area or pick a screen :)",
                parent=self.window,
            )
            warning.exec()
            return
        return Config(
            selection,
            self.file_dest,
            self.checkbox_use_audio.isChecked(),
        )

    def btn_onclick_select_area(self):
        self.selected_area = select_area() or self.selected_area
        self.selected_screen = None
        self.lbl_selected_area.setText(f"Selected area: {self.selected_area}")
        self.lbl_whole_screen_notice.hide()

    def btn_onclick_select_whole_screen(self):
        screens = available_screens()
        if len(screens) > 1:
            selected_screen_idx = ScreenSelectionDialog(screens, parent=self.window).exec()
            if selected_screen_idx == -1:
                return
            self.selected_screen = SelectedScreen(screens[selected_screen_idx])
        self.selected_area = None
        self.lbl_selected_area.setText(f"Selected screen: {self.selected_screen}")
        self.lbl_whole_screen_notice.show()

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

    def disable_all_buttons(self):
        set_buttons_state(
            self.btn_pick_dest,
            self.btn_generate_random_dest,
            self.btn_select_area,
            self.btn_select_whole_screen,
            enabled=False,
        )

    def enable_all_buttons(self):
        set_buttons_state(
            self.btn_pick_dest,
            self.btn_generate_random_dest,
            self.btn_select_area,
            self.btn_select_whole_screen,
            enabled=True,
        )
