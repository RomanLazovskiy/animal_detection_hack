from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen, QFont
from PyQt5.QtWidgets import QGraphicsScene, QGraphicsView, QDialog, QVBoxLayout
from PyQt5.QtCore import Qt
import matplotlib.pyplot as plt
from io import BytesIO
from PIL import Image

def display_plot(parent, class_counts):
    buf = BytesIO()
    fig, ax = plt.subplots()

    # Словарь для перевода названий классов на русский
    animal_dict = {'roedeer': 'Косуля', 'deer': 'Олень', 'muskdeer': 'Кабарга'}

    # Преобразуем названия классов и получим их количество
    labels = [animal_dict.get(label, label) for label in class_counts.keys()]
    counts = list(class_counts.values())

    # Построение графика
    bars = ax.bar(labels, counts)

    # Добавление текста с количеством каждого класса на график
    for bar, count in zip(bars, counts):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() - 5,
                str(count), ha='center', va='bottom', color='black', fontsize=10, fontweight='bold')

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

    dialog = QDialog(parent)
    dialog.setWindowTitle("Результаты классификации")
    dialog.setLayout(QVBoxLayout())
    dialog.layout().addWidget(view)
    dialog.exec_()

def display_image(parent, img, detections):
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
    font.setPointSize(24)
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

    dialog = QDialog(parent)
    dialog.setWindowTitle("Результаты детекции")
    dialog.setLayout(QVBoxLayout())
    dialog.layout().addWidget(view)
    dialog.exec_()
