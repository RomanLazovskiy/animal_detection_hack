import shutil
import sys
import tempfile

from PyQt5.QtWidgets import QGridLayout, QWidget, QLabel, QMainWindow, QTabWidget, QVBoxLayout, QPushButton, \
    QFileDialog, QApplication, QMessageBox, QGraphicsScene, QGraphicsView, QDialog
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt
import os
from PIL import Image, ImageDraw

from backend.inference import process_image_detection, detection_model, process_video, \
    process_archive_classification, classification_model, process_images_classification


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YOLOv8 Object Detection and Classification")

        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        self.detection_tab = QWidget()
        self.classification_tab = QWidget()

        self.tab_widget.addTab(self.detection_tab, "Detection")
        self.tab_widget.addTab(self.classification_tab, "Classification")

        self.detection_layout = QVBoxLayout()
        self.classification_layout = QVBoxLayout()

        self.detection_tab.setLayout(self.detection_layout)
        self.classification_tab.setLayout(self.classification_layout)

        self.detection_button = QPushButton("Load File for Detection")
        self.detection_button.clicked.connect(self.load_file_detection)
        self.detection_layout.addWidget(self.detection_button)

        self.classification_button = QPushButton("Load File for Classification")
        self.classification_button.clicked.connect(self.load_file_classification)
        self.classification_layout.addWidget(self.classification_button)

    def display_plot(self, class_counts):
        import matplotlib.pyplot as plt
        from io import BytesIO

        buf = BytesIO()
        fig, ax = plt.subplots()
        labels = list(class_counts.keys())
        counts = list(class_counts.values())
        ax.bar(labels, counts)
        ax.set_xlabel('Class')
        ax.set_ylabel('Count')
        ax.set_title('Classification Results')  # Изменено на set_title
        plt.savefig(buf, format='png')
        buf.seek(0)

        qimage = QImage()
        qimage.loadFromData(buf.read())

        scene = QGraphicsScene()
        pixmap_item = scene.addPixmap(QPixmap.fromImage(qimage))

        view = QGraphicsView(scene)

        dialog = QDialog(self)
        dialog.setWindowTitle("Classification Results")
        dialog.setLayout(QVBoxLayout())
        dialog.layout().addWidget(view)
        dialog.exec_()

    def display_image(self, img):
        # Преобразуем изображение в формат, понятный PyQt5
        img = img.convert("RGBA")
        img_resized = img.resize((600, 600), Image.Resampling.LANCZOS)
        data = img_resized.tobytes("raw", "RGBA")
        qimage = QImage(data, img_resized.size[0], img_resized.size[1], QImage.Format_RGBA8888)
        pixmap = QPixmap.fromImage(qimage)

        scene = QGraphicsScene()
        scene.addPixmap(pixmap)

        view = QGraphicsView(scene)
        view.setFixedSize(600, 600)
        view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        dialog = QDialog(self)
        dialog.setWindowTitle("Detection Results")
        dialog.setLayout(QVBoxLayout())
        dialog.layout().addWidget(view)
        dialog.exec_()

    def load_file_detection(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open File", "",
                                                   "All Files (*.*);;Image Files (*.png *.jpg *.jpeg);;Video Files (*.mp4 *.avi)")
        if not file_path:
            return

        if file_path.endswith(('.png', '.jpg', '.jpeg')):
            img = process_image_detection(detection_model, file_path)
            self.display_image(img)
        elif file_path.endswith(('.mp4', '.avi')):
            process_video(detection_model, file_path)
        else:
            self.show_error("Unsupported file format!")

    def load_file_classification(self):
        file_paths, _ = QFileDialog.getOpenFileNames(self, "Open Files", "",
                                                     "All Files (*.*);;Zip Files (*.zip);;Image Files (*.png *.jpg *.jpeg)")
        if not file_paths:
            return

        class_counts = {}

        with tempfile.TemporaryDirectory() as extract_to:
            for file_path in file_paths:
                if file_path.endswith('.zip'):
                    class_counts.update(process_archive_classification(classification_model, file_path, extract_to))
                elif file_path.endswith(('.png', '.jpg', '.jpeg')):
                    class_counts.update(process_images_classification(classification_model, [file_path]))
                else:
                    self.show_error("Unsupported file format for classification!")
                    return

        self.display_plot(class_counts)

    def show_error(self, message):
        QMessageBox.critical(self, "Error", message)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
