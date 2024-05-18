from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QListWidget, QDialog, QTextEdit, QMessageBox, QListWidgetItem
from utils.file_operations import load_history_files, load_classification_history, export_to_excel, clear_directory, metadata_directory
from utils.display import display_plot
from utils.logger import logger
import json
import os
import platform

class MetadataTab(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.metadata_list = QListWidget()
        self.layout.addWidget(self.metadata_list)

        self.view_json_button = QPushButton("Просмотреть выбранный JSON")
        self.view_json_button.clicked.connect(self.view_selected_json)
        self.layout.addWidget(self.view_json_button)

        self.view_plot_button = QPushButton("Просмотреть график классификации")
        self.view_plot_button.clicked.connect(self.load_selected_classification_history)
        self.layout.addWidget(self.view_plot_button)

        self.export_excel_button = QPushButton("Экспортировать выбранный JSON в Excel")
        self.export_excel_button.clicked.connect(self.export_selected_to_excel)
        self.layout.addWidget(self.export_excel_button)

        self.clear_metadata_button = QPushButton("Очистить метаданные")
        self.clear_metadata_button.clicked.connect(self.clear_metadata)
        self.layout.addWidget(self.clear_metadata_button)

        self.load_history_files()

    def load_history_files(self):
        logger.debug("Loading history files")
        try:
            self.metadata_list.clear()
            history_files = load_history_files()
            for filename in history_files:
                item = QListWidgetItem(filename)
                self.metadata_list.addItem(item)
        except Exception as e:
            logger.error(f"Error loading history files: {e}")
            self.show_error(f"Ошибка загрузки файлов истории: {e}")

    def load_selected_classification_history(self):
        selected_items = self.metadata_list.selectedItems()
        if not selected_items:
            self.show_error("Файл истории не выбран!")
            return

        filename = selected_items[0].text()
        logger.debug(f"Selected classification history file: {filename}")
        try:
            data = load_classification_history(filename)
            class_counts = data["class_counts"]
            display_plot(self, class_counts)
        except Exception as e:
            logger.error(f"Error loading classification history: {e}")
            self.show_error(f"Ошибка загрузки истории классификации: {e}")

    def view_selected_json(self):
        selected_items = self.metadata_list.selectedItems()
        if not selected_items:
            self.show_error("Файл истории не выбран!")
            return

        filename = selected_items[0].text()
        json_path = os.path.join(metadata_directory, filename)
        logger.debug(f"Viewing selected JSON file: {json_path}")
        try:
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
        except Exception as e:
            logger.error(f"Error viewing JSON file: {e}")
            self.show_error(f"Ошибка при просмотре JSON файла: {e}")

    def export_selected_to_excel(self):
        selected_items = self.metadata_list.selectedItems()
        if not selected_items:
            self.show_error("Файл истории не выбран!")
            return

        filename = selected_items[0].text()
        logger.debug(f"Exporting selected JSON to Excel: {filename}")
        try:
            excel_path = export_to_excel(filename)
            QMessageBox.information(self, "Экспорт успешен", f"Данные экспортированы в Excel файл:\n{excel_path}")
            # Обновляем список отчетов
            main_window = self.window()
            main_window.reports_tab.load_report_files()
            # Открываем созданный отчет
            self.open_report(excel_path)
        except Exception as e:
            logger.error(f"Error exporting to Excel: {e}")
            self.show_error(f"Ошибка экспорта в Excel: {e}")

    def open_report(self, report_path):
        logger.debug(f"Opening report: {report_path}")
        try:
            # Determine the OS and use the appropriate command
            if os.name == "nt":  # Windows
                os.startfile(report_path)
            elif os.name == "posix":
                if platform.system() == "Darwin":  # macOS
                    os.system(f'open "{report_path}"')
                else:  # Linux and other Unix-like systems
                    os.system(f'xdg-open "{report_path}"')
        except Exception as e:
            logger.error(f"Error opening report: {e}")
            self.show_error(f"Ошибка открытия отчета: {e}")

    def clear_metadata(self):
        if clear_directory(metadata_directory, self):
            self.load_history_files()

    def show_error(self, message):
        logger.error(f"Error: {message}")
        QMessageBox.critical(self, "Ошибка", message)
