from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

from PySide6.QtWidgets import QCheckBox, QMessageBox, QVBoxLayout

from common import SelectedArea, SelectedScreen
from groupbox_file_dest import FileDestGroupbox
from groupbox_selection import SelectionGroupbox


@dataclass
class Config:
    selection: Union[SelectedScreen, SelectedArea]
    file_dest: Path
    include_audio: bool


class ConfigArea(QVBoxLayout):
    def __init__(self, window):
        super().__init__()
        self.window = window

        self.selection_box = SelectionGroupbox(window)
        self.file_dest_box = FileDestGroupbox(window)

        self.checkbox_use_audio = QCheckBox("Record audio")

        self.addWidget(self.selection_box)
        self.addWidget(self.file_dest_box)

        self.addWidget(self.checkbox_use_audio)

    def create_config(self) -> Optional[Config]:
        """
        If no area or screen was selected, returns None
        """
        s = self.selection_box.get_selection()
        if s:
            selection = s
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
            self.file_dest_box.file_dest,
            self.checkbox_use_audio.isChecked(),
        )

    def set_buttons_enabled(self, enabled: bool):
        self.selection_box.set_buttons_enabled(enabled)
        self.file_dest_box.set_buttons_enabled(enabled)
