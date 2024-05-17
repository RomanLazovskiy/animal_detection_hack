import sys
import tempfile
import json
from PyQt5.QtWidgets import QVBoxLayout, QWidget, QMainWindow, QTabWidget, QPushButton, QFileDialog, QApplication, \
    QMessageBox, QGraphicsScene, QGraphicsView, QDialog, QListWidget, QListWidgetItem, QTextEdit
from PyQt5.QtGui import QPixmap, QImage, QPainter, QPen, QFont
from PyQt5.QtCore import Qt
from PIL import Image
import matplotlib.pyplot as plt
from io import BytesIO

from backend.inference import process_image_detection, detection_model, process_video, \
    process_archive_classification, classification_model, process_images_classification, save_classification_results, \
    load_history_files, load_classification_history, history_directory
import os


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YOLOv8 Object Detection and Classification")

        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        self.detection_tab = QWidget()
        self.classification_tab = QWidget()
        self.history_tab = QWidget()

        self.tab_widget.addTab(self.detection_tab, "Detection")
        self.tab_widget.addTab(self.classification_tab, "Classification")
        self.tab_widget.addTab(self.history_tab, "History")

        self.detection_layout = QVBoxLayout()
        self.classification_layout = QVBoxLayout()
        self.history_layout = QVBoxLayout()

        self.detection_tab.setLayout(self.detection_layout)
        self.classification_tab.setLayout(self.classification_layout)
        self.history_tab.setLayout(self.history_layout)

        self.detection_button = QPushButton("Load File for Detection")
        self.detection_button.clicked.connect(self.load_file_detection)
        self.detection_layout.addWidget(self.detection_button)

        self.classification_button = QPushButton("Load File for Classification")
        self.classification_button.clicked.connect(self.load_file_classification)
        self.classification_layout.addWidget(self.classification_button)

        self.history_list = QListWidget()
        self.history_layout.addWidget(self.history_list)

        self.view_json_button = QPushButton("View Selected JSON")
        self.view_json_button.clicked.connect(self.view_selected_json)
        self.history_layout.addWidget(self.view_json_button)

        self.view_plot_button = QPushButton("View Selected Classification Plot")
        self.view_plot_button.clicked.connect(self.load_selected_classification_history)
        self.history_layout.addWidget(self.view_plot_button)

        self.clear_history_button = QPushButton("Clear History")
        self.clear_history_button.clicked.connect(self.clear_history)
        self.history_layout.addWidget(self.clear_history_button)

        self.font_size = 24  # Задаем размер шрифта по умолчанию

        self.load_history_files()

    def load_history_files(self):
        self.history_list.clear()
        history_files = load_history_files()
        for filename in history_files:
            item = QListWidgetItem(filename)
            self.history_list.addItem(item)

    def display_plot(self, class_counts):
        buf = BytesIO()
        fig, ax = plt.subplots()
        labels = list(class_counts.keys())
        counts = list(class_counts.values())
        ax.bar(labels, counts)
        ax.set_xlabel('Class')
        ax.set_ylabel('Count')
        ax.set_title('Classification Results')
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

    def display_image(self, img, detections):
        original_width, original_height = img.size
        img = img.convert("RGBA")
        img_resized = img.resize((600, 600), Image.Resampling.LANCZOS)
        resized_width, resized_height = img_resized.size

        width_ratio = resized_width / original_width
        height_ratio = resized_height / original_height

        data = img_resized.tobytes("raw", "RGBA")
        qimage = QImage(data, img_resized.size[0], img_resized.size[1], QImage.Format_RGBA8888)
        pixmap = QPixmap.fromImage(qimage)

        painter = QPainter(pixmap)

        # Рисуем bbox
        pen = QPen(Qt.red)
        pen.setWidth(2)
        painter.setPen(pen)
        for (xyxy, label_name) in detections:
            x0, y0, x1, y1 = xyxy
            x0 *= width_ratio
            y0 *= height_ratio
            x1 *= width_ratio
            y1 *= height_ratio
            painter.drawRect(int(x0), int(y0), int(x1 - x0), int(y1 - y0))

        # Рисуем метки класса
        pen = QPen(Qt.green)
        painter.setPen(pen)
        font = QFont()
        font.setFamily('Arial')
        font.setBold(True)
        font.setPointSize(self.font_size)
        painter.setFont(font)
        for (xyxy, label_name) in detections:
            x0, y0, x1, y1 = xyxy
            x0 *= width_ratio
            y0 *= height_ratio
            painter.drawText(int(x0), int(y0) - 10, label_name)

        painter.end()

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
            img, detections = process_image_detection(detection_model, file_path)
            self.display_image(img, detections)
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
        image_classifications = []

        with tempfile.TemporaryDirectory() as extract_to:
            for file_path in file_paths:
                if file_path.endswith('.zip'):
                    new_class_counts, new_image_classifications = process_archive_classification(classification_model,
                                                                                                 file_path, extract_to)
                elif file_path.endswith(('.png', '.jpg', '.jpeg')):
                    new_class_counts, new_image_classifications = process_images_classification(classification_model,
                                                                                                [file_path])
                else:
                    self.show_error("Unsupported file format for classification!")
                    return
                class_counts.update(new_class_counts)
                image_classifications.extend(new_image_classifications)

        save_classification_results(class_counts, image_classifications)
        self.display_plot(class_counts)
        self.load_history_files()  # Обновляем список файлов истории

    def load_selected_classification_history(self):
        selected_items = self.history_list.selectedItems()
        if not selected_items:
            self.show_error("No history file selected!")
            return

        filename = selected_items[0].text()
        data = load_classification_history(filename)
        class_counts = data["class_counts"]
        self.display_plot(class_counts)

    def view_selected_json(self):
        selected_items = self.history_list.selectedItems()
        if not selected_items:
            self.show_error("No history file selected!")
            return

        filename = selected_items[0].text()
        json_path = os.path.join(history_directory, filename)
        with open(json_path, 'r') as json_file:
            json_data = json.load(json_file)

        dialog = QDialog(self)
        dialog.setWindowTitle("View JSON")
        layout = QVBoxLayout()
        text_edit = QTextEdit()
        text_edit.setPlainText(json.dumps(json_data, indent=4))
        layout.addWidget(text_edit)
        dialog.setLayout(layout)
        dialog.exec_()

    def clear_history(self):
        reply = QMessageBox.question(self, 'Clear History', "Are you sure you want to clear all history files?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            for filename in os.listdir(history_directory):
                file_path = os.path.join(history_directory, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            self.load_history_files()  # Обновляем список файлов истории

    def show_error(self, message):
        QMessageBox.critical(self, "Error", message)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
