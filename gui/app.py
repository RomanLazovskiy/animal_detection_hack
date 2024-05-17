import sys
import os
import tempfile
import json
import platform
from PyQt5.QtWidgets import QVBoxLayout, QWidget, QMainWindow, QTabWidget, QPushButton, QFileDialog, QApplication, \
    QMessageBox, QGraphicsScene, QGraphicsView, QDialog, QListWidget, QListWidgetItem, QTextEdit
from PyQt5.QtGui import QPixmap, QImage, QPainter, QPen, QFont
from PyQt5.QtCore import Qt
from PIL import Image
import matplotlib.pyplot as plt
from io import BytesIO

from backend.inference import process_image_detection, detection_model, process_video, \
    process_archive_classification, classification_model, process_images_classification, save_classification_results, \
    load_history_files, load_classification_history, export_to_excel, metadata_directory, reports_directory, \
    load_report_files


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Классификация парнокопытных")

        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        self.detection_tab = QWidget()
        self.classification_tab = QWidget()
        self.metadata_tab = QWidget()
        self.reports_tab = QWidget()

        self.tab_widget.addTab(self.detection_tab, "Детекция")
        self.tab_widget.addTab(self.classification_tab, "Классификация")
        self.tab_widget.addTab(self.metadata_tab, "Метаданные")
        self.tab_widget.addTab(self.reports_tab, "Отчеты")

        self.detection_layout = QVBoxLayout()
        self.classification_layout = QVBoxLayout()
        self.metadata_layout = QVBoxLayout()
        self.reports_layout = QVBoxLayout()

        self.detection_tab.setLayout(self.detection_layout)
        self.classification_tab.setLayout(self.classification_layout)
        self.metadata_tab.setLayout(self.metadata_layout)
        self.reports_tab.setLayout(self.reports_layout)

        self.detection_button = QPushButton("Загрузить файл для детекции")
        self.detection_button.clicked.connect(self.load_file_detection)
        self.detection_layout.addWidget(self.detection_button)

        self.classification_button = QPushButton("Загрузить файл для классификации")
        self.classification_button.clicked.connect(self.load_file_classification)
        self.classification_layout.addWidget(self.classification_button)

        self.metadata_list = QListWidget()
        self.metadata_layout.addWidget(self.metadata_list)

        self.view_json_button = QPushButton("Просмотреть выбранный JSON")
        self.view_json_button.clicked.connect(self.view_selected_json)
        self.metadata_layout.addWidget(self.view_json_button)

        self.view_plot_button = QPushButton("Просмотреть график классификации")
        self.view_plot_button.clicked.connect(self.load_selected_classification_history)
        self.metadata_layout.addWidget(self.view_plot_button)

        self.export_excel_button = QPushButton("Экспортировать выбранный JSON в Excel")
        self.export_excel_button.clicked.connect(self.export_selected_to_excel)
        self.metadata_layout.addWidget(self.export_excel_button)

        self.clear_metadata_button = QPushButton("Очистить метаданные")
        self.clear_metadata_button.clicked.connect(self.clear_metadata)
        self.metadata_layout.addWidget(self.clear_metadata_button)

        self.reports_list = QListWidget()
        self.reports_layout.addWidget(self.reports_list)

        self.open_report_button = QPushButton("Открыть отчет")
        self.open_report_button.clicked.connect(self.open_report)
        self.reports_layout.addWidget(self.open_report_button)

        self.clear_reports_button = QPushButton("Очистить отчеты")
        self.clear_reports_button.clicked.connect(self.clear_reports)
        self.reports_layout.addWidget(self.clear_reports_button)

        self.font_size = 24  # Задаем размер шрифта по умолчанию

        self.load_history_files()
        self.load_report_files()

    def load_history_files(self):
        self.metadata_list.clear()
        history_files = load_history_files()
        for filename in history_files:
            item = QListWidgetItem(filename)
            self.metadata_list.addItem(item)

    def load_report_files(self):
        self.reports_list.clear()
        report_files = load_report_files()
        for filename in report_files:
            item = QListWidgetItem(filename)
            self.reports_list.addItem(item)

    def display_plot(self, class_counts):
        buf = BytesIO()
        fig, ax = plt.subplots()
        labels = list(class_counts.keys())
        counts = list(class_counts.values())
        ax.bar(labels, counts)
        ax.set_xlabel('Класс')
        ax.set_ylabel('Количество')
        ax.set_title('Результаты классификации')
        plt.savefig(buf, format='png')
        buf.seek(0)

        qimage = QImage()
        qimage.loadFromData(buf.read())

        scene = QGraphicsScene()
        pixmap_item = scene.addPixmap(QPixmap.fromImage(qimage))

        view = QGraphicsView(scene)

        dialog = QDialog(self)
        dialog.setWindowTitle("Результаты классификации")
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
        dialog.setWindowTitle("Результаты детекции")
        dialog.setLayout(QVBoxLayout())
        dialog.layout().addWidget(view)
        dialog.exec_()

    def load_file_detection(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Открыть файл", "",
                                                   "Все файлы (*.*);;Изображения (*.png *.jpg *.jpeg);;Видео (*.mp4 *.avi)")
        if not file_path:
            return

        if file_path.endswith(('.png', '.jpg', '.jpeg')):
            img, detections = process_image_detection(detection_model, file_path)
            self.display_image(img, detections)
        elif file_path.endswith(('.mp4', '.avi')):
            process_video(detection_model, file_path)
        else:
            self.show_error("Неподдерживаемый формат файла!")

    def load_file_classification(self):
        file_paths, _ = QFileDialog.getOpenFileNames(self, "Открыть файлы", "",
                                                     "Все файлы (*.*);;Архивы (*.zip);;Изображения (*.png *.jpg *.jpeg)")
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
                    self.show_error("Неподдерживаемый формат файла для классификации!")
                    return
                class_counts.update(new_class_counts)
                image_classifications.extend(new_image_classifications)

        save_classification_results(class_counts, image_classifications)
        self.display_plot(class_counts)
        self.load_history_files()  # Обновляем список файлов истории
        self.load_report_files()  # Обновляем список отчетов

    def load_selected_classification_history(self):
        selected_items = self.metadata_list.selectedItems()
        if not selected_items:
            self.show_error("Файл истории не выбран!")
            return

        filename = selected_items[0].text()
        data = load_classification_history(filename)
        class_counts = data["class_counts"]
        self.display_plot(class_counts)

    def view_selected_json(self):
        selected_items = self.metadata_list.selectedItems()
        if not selected_items:
            self.show_error("Файл истории не выбран!")
            return

        filename = selected_items[0].text()
        json_path = os.path.join(metadata_directory, filename)
        with open(json_path, 'r') as json_file:
            json_data = json.load(json_file)

        dialog = QDialog(self)
        dialog.setWindowTitle("Просмотр JSON")
        layout = QVBoxLayout()
        text_edit = QTextEdit()
        text_edit.setPlainText(json.dumps(json_data, indent=4))
        layout.addWidget(text_edit)
        dialog.setLayout(layout)
        dialog.exec_()

    def export_selected_to_excel(self):
        selected_items = self.metadata_list.selectedItems()
        if not selected_items:
            self.show_error("Файл истории не выбран!")
            return

        filename = selected_items[0].text()
        excel_path = export_to_excel(filename)
        QMessageBox.information(self, "Экспорт успешен", f"Данные экспортированы в Excel файл:\n{excel_path}")
        self.load_report_files()  # Обновляем список отчетов

    def open_report(self):
        selected_items = self.reports_list.selectedItems()
        if not selected_items:
            self.show_error("Отчет не выбран!")
            return

        filename = selected_items[0].text()
        report_path = os.path.join(reports_directory, filename)

        # Determine the OS and use the appropriate command
        if platform.system() == "Windows":
            os.system(f'start "" "{report_path}"')
        elif platform.system() == "Darwin":  # macOS
            os.system(f'open "{report_path}"')
        else:  # Linux and other Unix-like systems
            os.system(f'xdg-open "{report_path}"')

    def clear_metadata(self):
        reply = QMessageBox.question(self, 'Очистить метаданные', "Вы уверены, что хотите очистить все метаданные?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            for filename in os.listdir(metadata_directory):
                file_path = os.path.join(metadata_directory, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            self.load_history_files()  # Обновляем список файлов истории

    def clear_reports(self):
        reply = QMessageBox.question(self, 'Очистить отчеты', "Вы уверены, что хотите очистить все отчеты?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            for filename in os.listdir(reports_directory):
                file_path = os.path.join(reports_directory, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            self.load_report_files()  # Обновляем список отчетов

    def show_error(self, message):
        QMessageBox.critical(self, "Ошибка", message)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
