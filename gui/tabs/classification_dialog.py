from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PyQt5.QtGui import QPixmap
import os

class ClassificationDialog(QDialog):
    def __init__(self, image_path, class_options, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Выберите класс")
        self.selected_class = None

        layout = QVBoxLayout()
        self.setLayout(layout)

        pixmap = QPixmap(image_path)

        image_label = QLabel()
        image_label.setPixmap(pixmap)
        layout.addWidget(image_label)

        # Adding filename label
        filename = os.path.basename(image_path)
        filename_label = QLabel(f"Название фото: {filename}")
        layout.addWidget(filename_label)

        button_layout = QHBoxLayout()

        # Mapping class names to Russian names
        self.class_names_mapping = {
            'roedeer': 'Косуля',
            'muskdeer': 'Кабарга',
            'deer': 'Олень'
        }

        for class_option in class_options:
            russian_name = self.class_names_mapping.get(class_option, class_option)
            button = QPushButton(russian_name)
            button.clicked.connect(self.on_class_selected)
            button_layout.addWidget(button)

        layout.addLayout(button_layout)

    def on_class_selected(self):
        button = self.sender()
        russian_class_name = button.text()
        # Find the English class name from the mapping
        self.selected_class = next((key for key, value in self.class_names_mapping.items() if value == russian_class_name), russian_class_name)
        self.accept()
