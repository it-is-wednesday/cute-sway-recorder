from PySide6.QtWidgets import QDialog, QHBoxLayout, QPushButton


class ScreenSelectionDialog(QDialog):
    def __init__(self, available_screens, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout()
        self.setWindowTitle("Select screen")

        for i, screen in enumerate(available_screens):
            btn = QPushButton(text=screen)
            btn.clicked.connect(self.make_clicked_func(i))
            layout.addWidget(btn)

        self.setLayout(layout)

    def make_clicked_func(self, int_to_return):
        """
        Creates a function to be executed on button click. The function makes the dialog quit and
        return int_to_return to its parent (assuming the dialog was ran with .exec())
        """
        def new_func():
            self.done(int_to_return)
        return new_func
