from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QFileDialog, QMessageBox
from backend.inference import process_image_detection, detection_model, process_video
from utils.display import display_image
from utils.logger import logger

class DetectionTab(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.detection_button = QPushButton("Загрузить файл для детекции")
        self.detection_button.clicked.connect(self.load_file_detection)
        self.layout.addWidget(self.detection_button)

    def load_file_detection(self):
        logger.debug("Loading file for detection")
        file_path, _ = QFileDialog.getOpenFileName(self, "Открыть файл", "",
                                                   "Все файлы (*.*);;Изображения (*.png *.jpg *.jpeg);;Видео (*.mp4 *.avi)")
        if not file_path:
            logger.debug("No file selected for detection")
            return

        logger.debug(f"File selected for detection: {file_path}")

        if file_path.endswith(('.png', '.jpg', '.jpeg')):
            img, detections = process_image_detection(detection_model, file_path)
            display_image(self, img, detections)
        elif file_path.endswith(('.mp4', '.avi')):
            process_video(detection_model, file_path)
        else:
            self.show_error("Неподдерживаемый формат файла!")
            logger.error("Unsupported file format for detection")

    def show_error(self, message):
        logger.error(f"Error: {message}")
        QMessageBox.critical(self, "Ошибка", message)
