from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QEventLoop, QCoreApplication
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QFileDialog, QMessageBox, QProgressDialog
from backend.inference import process_archive_classification, classification_model, process_images_classification
from utils.display import display_plot
from utils.file_operations import save_classification_results, export_to_excel, load_history_files
from utils.logger import logger
import tempfile
import os
import threading

class ClassificationWorker(QThread):
    progress_changed = pyqtSignal(int)
    classification_done = pyqtSignal(dict, list)
    error_occurred = pyqtSignal(str)

    def __init__(self, file_paths, model, extract_to):
        super().__init__()
        self.file_paths = file_paths
        self.model = model
        self.extract_to = extract_to
        self._is_running = True
        self.stop_event = threading.Event()

    def run(self):
        class_counts = {}
        image_classifications = []

        try:
            for i, file_path in enumerate(self.file_paths):
                if self.stop_event.is_set():
                    break

                if file_path.endswith('.zip'):
                    new_class_counts, new_image_classifications = process_archive_classification(
                        self.model, file_path, self.extract_to, self.stop_event)
                elif file_path.endswith(('.png', '.jpg', '.jpeg')):
                    new_class_counts, new_image_classifications = process_images_classification(
                        self.model, [file_path], self.stop_event)
                else:
                    continue

                # Update class_counts
                for key, value in new_class_counts.items():
                    class_counts[key] = class_counts.get(key, 0) + value
                image_classifications.extend(new_image_classifications)
                self.progress_changed.emit(i + 1)

            if not self.stop_event.is_set():
                self.classification_done.emit(class_counts, image_classifications)

        except Exception as e:
            logger.error(f"Error during classification: {e}")
            self.error_occurred.emit(str(e))

    def stop(self):
        self.stop_event.set()
        self.wait()

class ClassificationTab(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.classification_button = QPushButton("Загрузить файл для классификации")
        self.classification_button.clicked.connect(self.load_file_classification)
        self.layout.addWidget(self.classification_button)

    def load_file_classification(self):
        logger.debug("Loading file for classification")
        file_paths, _ = QFileDialog.getOpenFileNames(self, "Открыть файлы", "",
                                                     "Все файлы (*.*);;Архивы (*.zip);;Изображения (*.png *.jpg *.jpeg)")
        if not file_paths:
            logger.debug("No files selected for classification")
            return

        logger.debug(f"Files selected for classification: {file_paths}")

        self.progress_dialog = QProgressDialog("Обработка изображений...", "Отмена", 0, len(file_paths), self)
        self.progress_dialog.setWindowTitle("Прогресс обработки")
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.canceled.connect(self.cancel_classification)
        self.progress_dialog.show()

        self.worker = ClassificationWorker(file_paths, classification_model, tempfile.mkdtemp())
        self.worker.progress_changed.connect(self.update_progress)
        self.worker.classification_done.connect(self.on_classification_done)
        self.worker.error_occurred.connect(self.on_classification_error)
        self.worker.start()

    def update_progress(self, value):
        self.progress_dialog.setValue(value)
        QCoreApplication.processEvents(QEventLoop.AllEvents, 100)

    def cancel_classification(self):
        if self.worker.isRunning():
            self.worker.stop()

    def on_classification_done(self, class_counts, image_classifications):
        self.progress_dialog.close()
        if not class_counts:
            self.show_error("Ошибка при классификации: См. логи для подробностей")
            return

        save_classification_results(class_counts, image_classifications)
        display_plot(self, class_counts)

        main_window = self.window()
        main_window.metadata_tab.load_history_files()
        main_window.reports_tab.load_report_files()

        history_files = load_history_files()
        latest_history_file = sorted(history_files)[-1]
        export_to_excel(latest_history_file)
        main_window.reports_tab.load_report_files()

    def on_classification_error(self, message):
        self.progress_dialog.close()
        self.show_error(f"Ошибка при классификации: {message}")

    def show_error(self, message):
        logger.error(f"Error: {message}")
        QMessageBox.critical(self, "Ошибка", message)
