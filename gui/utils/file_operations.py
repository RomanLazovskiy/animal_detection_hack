import os
import json
import datetime
from PyQt5.QtWidgets import QMessageBox
from utils.logger import logger
import pandas as pd

metadata_directory = "metadata"
reports_directory = "reports"

def ensure_directories_exist():
    if not os.path.exists(metadata_directory):
        os.makedirs(metadata_directory)
    if not os.path.exists(reports_directory):
        os.makedirs(reports_directory)

def get_timestamp():
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

def load_history_files():
    ensure_directories_exist()
    return [f for f in os.listdir(metadata_directory) if os.path.isfile(os.path.join(metadata_directory, f))]

def load_report_files():
    ensure_directories_exist()
    return [f for f in os.listdir(reports_directory) if os.path.isfile(os.path.join(reports_directory, f))]

def load_classification_history(filename):
    file_path = os.path.join(metadata_directory, filename)
    with open(file_path, 'r') as file:
        return json.load(file)

def save_classification_results(class_counts, image_classifications):
    ensure_directories_exist()
    result = {
        "class_counts": class_counts,
        "image_classifications": image_classifications
    }
    timestamp = get_timestamp()
    filename = os.path.join(metadata_directory, f"classification_results_{timestamp}.json")
    with open(filename, 'w') as file:
        json.dump(result, file)
    logger.debug(f"Saved classification results to {filename}")

def export_to_excel(filename):

    file_path = os.path.join(metadata_directory, filename)
    with open(file_path, 'r') as file:
        data = json.load(file)

    # Преобразование списка классов в строку
    animal_dict = {'roedeer': 'Косуля', 'deer': 'Олень', 'muskdeer': 'Кабарга'}
    for item in data["image_classifications"]:
        item["classes"] = ", ".join([animal_dict.get(cls, cls) for cls in item["classes"]])

    # Преобразование данных в DataFrame
    df = pd.DataFrame(data["image_classifications"])

    # Переименование столбцов и упорядочивание
    df = df.rename(columns={"image": "Изображение", "classes": "Класс"})
    df = df[["Изображение", "Класс"]]

    timestamp = get_timestamp()
    excel_path = os.path.join(reports_directory, f"{os.path.splitext(filename)[0]}_{timestamp}.xlsx")
    df.to_excel(excel_path, index=False)
    logger.debug(f"Exported {filename} to Excel at {excel_path}")
    return excel_path



def clear_directory(directory_path, parent):
    reply = QMessageBox.question(parent, 'Очистить файлы', f"Вы уверены, что хотите очистить все файлы в {directory_path}?",
                                 QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
    if reply == QMessageBox.Yes:
        logger.debug(f"Clearing directory: {directory_path}")
        for filename in os.listdir(directory_path):
            file_path = os.path.join(directory_path, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
        return True
    return False
