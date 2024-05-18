from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QListWidget, QListWidgetItem, QMessageBox
import os
import platform
from utils.file_operations import load_report_files, clear_directory, reports_directory
from utils.logger import logger

class ReportsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.reports_list = QListWidget()
        self.layout.addWidget(self.reports_list)

        self.open_report_button = QPushButton("Открыть отчет")
        self.open_report_button.clicked.connect(self.open_report)
        self.layout.addWidget(self.open_report_button)

        self.clear_reports_button = QPushButton("Очистить отчеты")
        self.clear_reports_button.clicked.connect(self.clear_reports)
        self.layout.addWidget(self.clear_reports_button)

        self.load_report_files()

    def load_report_files(self):
        logger.debug("Loading report files")
        try:
            self.reports_list.clear()
            report_files = load_report_files()
            for filename in report_files:
                item = QListWidgetItem(filename)
                self.reports_list.addItem(item)
        except Exception as e:
            logger.error(f"Error loading report files: {e}")
            self.show_error(f"Ошибка загрузки отчетов: {e}")

    def open_report(self):
        selected_items = self.reports_list.selectedItems()
        if not selected_items:
            self.show_error("Отчет не выбран!")
            return

        filename = selected_items[0].text()
        report_path = os.path.join(reports_directory, filename)
        self._open_report(report_path)

    def _open_report(self, report_path):
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

    def clear_reports(self):
        if clear_directory(reports_directory, self):
            self.load_report_files()

    def show_error(self, message):
        logger.error(f"Error: {message}")
        QMessageBox.critical(self, "Ошибка", message)
