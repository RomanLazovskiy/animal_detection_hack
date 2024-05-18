import os
import sys


from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt5 Test")
        self.setGeometry(100, 100, 280, 80)
        self.button = QPushButton('Hello, PyQt5!', self)
        self.button.setGeometry(50, 20, 180, 40)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec_())
