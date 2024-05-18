import zipfile
import os
import json
import tempfile
from datetime import datetime
from ultralytics import YOLO
from PIL import Image, ImageDraw
import cv2
import numpy as np
import pandas as pd

# Загрузка моделей YOLOv8
detection_model = YOLO('yolov8n.pt')
classification_model = YOLO('yolov8n-cls.pt')

# Функция для выполнения инференса
def run_inference(model, img):
    results = model.predict(source=img)
    return results


# Функция для обработки изображения для детекции и возвращения bbox и меток
def process_image_detection(model, image_path):
    img = Image.open(image_path).convert("RGB")
    outputs = run_inference(model, img)

    detections = []

    for result in outputs:
        boxes = result.boxes
        if boxes is not None:
            for box in boxes:
                label = int(box.cls)
                label_name = model.names[label]
                xyxy = box.xyxy[0].tolist()
                detections.append((xyxy, label_name))

    return img, detections


# Функция для обработки изображений для классификации
def process_images_classification(model, image_paths):
    class_counts = {}
    image_classifications = []
    for image_path in image_paths:
        img = Image.open(image_path).convert("RGB")
        outputs = run_inference(model, img)
        image_data = {"image": os.path.basename(image_path), "classes": []}
        for result in outputs:
            if result.probs is not None:
                label = int(result.probs.top1)
                label_name = model.names[label]
                class_counts[label_name] = class_counts.get(label_name, 0) + 1
                image_data["classes"].append(label_name)
        image_classifications.append(image_data)
    return class_counts, image_classifications


# Функция для обработки видео для детекции
def process_video(model, video_path):
    cap = cv2.VideoCapture(video_path)
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        outputs = run_inference(model, img)
        draw = ImageDraw.Draw(img)
        detections = []
        for result in outputs:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    label = int(box.cls)
                    label_name = model.names[label]
                    xyxy = box.xyxy[0].tolist()
                    detections.append((xyxy, label_name))
        frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        cv2.imshow('frame', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()


# Функция для обработки архива для классификации
def process_archive_classification(model, archive_path, extract_to):
    with zipfile.ZipFile(archive_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
    image_paths = [os.path.join(extract_to, f) for f in os.listdir(extract_to) if f.endswith(('.png', '.jpg', '.jpeg'))]
    return process_images_classification(model, image_paths)


# Функция для сохранения результатов классификации в JSON файл и генерации Excel файла
def save_classification_results(results, image_classifications):
    timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    json_filename = f"classification_{timestamp}.json"
    json_path = os.path.join(metadata_directory, json_filename)
    json_data = {
        "timestamp": timestamp,
        "class_counts": results,
        "image_classifications": image_classifications
    }
    with open(json_path, 'w') as json_file:
        json.dump(json_data, json_file, indent=4)

    excel_filename = json_filename.replace(".json", ".xlsx")
    excel_path = os.path.join(reports_directory, excel_filename)

    # Создаем DataFrame из данных JSON
    rows = []
    for item in json_data["image_classifications"]:
        for class_name in item["classes"]:
            rows.append({"Изображение": item["image"], "Класс": class_name})

    df = pd.DataFrame(rows)
    df.to_excel(excel_path, index=False)

    return json_path, excel_path


# Функция для загрузки всех JSON файлов из директории истории
def load_history_files():
    history_files = []
    for filename in os.listdir(metadata_directory):
        if filename.endswith(".json"):
            history_files.append(filename)
    return history_files


# Функция для загрузки всех Excel отчетов из директории истории
def load_report_files():
    report_files = []
    for filename in os.listdir(reports_directory):
        if filename.endswith(".xlsx"):
            report_files.append(filename)
    return report_files


# Функция для загрузки данных из выбранного JSON файла
def load_classification_history(filename):
    json_path = os.path.join(metadata_directory, filename)
    with open(json_path, 'r') as json_file:
        data = json.load(json_file)
    return data


# Функция для экспорта данных из JSON файла в Excel
def export_to_excel(json_filename):
    json_path = os.path.join(metadata_directory, json_filename)
    with open(json_path, 'r') as json_file:
        data = json.load(json_file)

    excel_filename = json_filename.replace(".json", ".xlsx")
    excel_path = os.path.join(reports_directory, excel_filename)

    # Создаем DataFrame из данных JSON
    rows = []
    for item in data["image_classifications"]:
        for class_name in item["classes"]:
            rows.append({"Изображение": item["image"], "Класс": class_name})

    df = pd.DataFrame(rows)
    df.to_excel(excel_path, index=False)
    return excel_path
