import subprocess
from typing import Optional, Union
from PySide6.QtWidgets import QGroupBox, QLabel, QPushButton, QVBoxLayout

from common import SelectedArea, SelectedScreen, available_screens
from screen_selection import ScreenSelectionDialog


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


class SelectionGroupbox(QGroupBox):
    def __init__(self, window):
        super().__init__(title="What are we recording?")
        self.window = window

        self.title

        layout = QVBoxLayout()

        self.lbl_whole_screen_notice = QLabel(
            '<font color="salmon">This window will be minimized. <br/>'
            "Click the tray icon to stop recording</font>"
        )
        self.lbl_whole_screen_notice.hide()

        self.selected_screen: Optional[SelectedScreen] = None
        self.selected_area = None

        self.lbl_selected_area = QLabel("Selected area: None")

        self.btn_select_area = QPushButton("Select an area")
        self.btn_select_whole_screen = QPushButton("Select whole screen")

        self.btn_select_area.clicked.connect(self.btn_onclick_select_area)
        self.btn_select_whole_screen.clicked.connect(self.btn_onclick_select_whole_screen)

        layout.addWidget(self.lbl_selected_area)
        layout.addWidget(self.btn_select_area)
        layout.addWidget(self.btn_select_whole_screen)
        layout.addWidget(self.lbl_whole_screen_notice)

        self.setLayout(layout)

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

    def get_selection(self) -> Union[SelectedArea, SelectedScreen, None]:
        return self.selected_area or self.selected_screen
