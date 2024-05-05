from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union
from PySide6 import QtCore

from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QSpinBox,
    QStyle,
    QVBoxLayout,
    QLineEdit,
)

from .common import SelectedArea, SelectedScreen
from .group_file_dest import FileDestGroup
from .group_selection import SelectionGroup


@dataclass
class Config:
    selection: Union[SelectedScreen, SelectedArea]
    file_dest: Path
    include_audio: bool
    delay: int
    flags: str


class ConfigArea(QVBoxLayout):
    def __init__(self, window):
        super().__init__()
        self.window = window

        self.selection_box = SelectionGroup(window)
        self.file_dest_box = FileDestGroup(window)

        self.checkbox_use_audio = QCheckBox("Record audio")
        self.delay_spinbox = QSpinBox()
        self.flags = QLineEdit()

        self.setup_layout()

    def setup_layout(self):
        self.addLayout(self.selection_box)
        self.addLayout(self.file_dest_box)

        bottom = QHBoxLayout()
        bottom.addWidget(QLabel("Delay (secs):"))
        bottom.addWidget(self.delay_spinbox)
        bottom.addWidget(self.checkbox_use_audio)
        bottom.addStretch()
        self.addLayout(bottom)

        flags = QHBoxLayout()
        flags.addWidget(QLabel("Flags:"))
        flags.addWidget(self.flags)
        self.addLayout(flags)

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
            self.delay_spinbox.value(),
            self.flags.text(),
        )

    def set_buttons_enabled(self, enabled: bool):
        self.selection_box.set_buttons_enabled(enabled)
        self.file_dest_box.set_buttons_enabled(enabled)
        self.delay_spinbox.setEnabled(enabled)
        self.checkbox_use_audio.setEnabled(enabled)
