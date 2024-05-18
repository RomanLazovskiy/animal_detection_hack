from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QFileDialog, QMessageBox
from backend.inference import process_archive_classification, classification_model, process_images_classification
from utils.display import display_plot
from utils.file_operations import save_classification_results, export_to_excel, load_history_files
from utils.logger import logger
import tempfile

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

        class_counts = {}
        image_classifications = []

        try:
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
                        logger.error("Unsupported file format for classification")
                        return
                    # Обновление словаря class_counts
                    for key, value in new_class_counts.items():
                        class_counts[key] = class_counts.get(key, 0) + value
                    image_classifications.extend(new_image_classifications)

            save_classification_results(class_counts, image_classifications)
            display_plot(self, class_counts)

            # Обновляем списки файлов в вкладках метаданных и отчетов
            main_window = self.window()
            main_window.metadata_tab.load_history_files()
            main_window.reports_tab.load_report_files()

            # Создаем Excel отчет
            history_files = load_history_files()
            latest_history_file = sorted(history_files)[-1]
            export_to_excel(latest_history_file)
            main_window.reports_tab.load_report_files()  # Обновляем список отчетов

        except Exception as e:
            logger.error(f"Error during classification: {e}")
            self.show_error(f"Ошибка при классификации: {e}")

    def show_error(self, message):
        logger.error(f"Error: {message}")
        QMessageBox.critical(self, "Ошибка", message)
