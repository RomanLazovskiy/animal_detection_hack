import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget
from tabs.detection_tab import DetectionTab
from tabs.classification_tab import ClassificationTab
from tabs.metadata_tab import MetadataTab
from tabs.reports_tab import ReportsTab
from utils.logger import setup_logging
import logging

# Настройка логирования
setup_logging()
logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        logger.debug("Initializing MainWindow")
        self.setWindowTitle("Классификация парнокопытных")

        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        self.detection_tab = DetectionTab()
        self.classification_tab = ClassificationTab()
        self.metadata_tab = MetadataTab()
        self.reports_tab = ReportsTab()

        self.tab_widget.addTab(self.detection_tab, "Детекция")
        self.tab_widget.addTab(self.classification_tab, "Классификация")
        self.tab_widget.addTab(self.metadata_tab, "Метаданные")
        self.tab_widget.addTab(self.reports_tab, "Отчеты")

if __name__ == "__main__":
    logger.debug("Starting application")
    app = QApplication(sys.argv)
    logger.debug(f"sys.argv: {sys.argv}")
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
