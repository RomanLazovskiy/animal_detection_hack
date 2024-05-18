import zipfile
import os
import json
from datetime import datetime
from ultralytics import YOLO
from PIL import Image, ImageDraw, UnidentifiedImageError
import cv2
import numpy as np
import pandas as pd

# Загрузка моделей YOLOv8
model_directory = os.path.join(os.path.dirname(__file__), '..', 'models')
detection_model_path = os.path.join(model_directory, 'best_detect.pt')
classification_model_path = os.path.join(model_directory, 'best_clasify.pt')

detection_model = YOLO(detection_model_path)
classification_model = YOLO(classification_model_path)

# Функция для выполнения инференса
def run_inference(model, img, stop_event=None):
    results = model.predict(source=img)
    if stop_event and stop_event.is_set():
        raise InterruptedError("Inference was stopped.")
    return results

# Функция для обработки изображения для детекции и возвращения bbox и меток
def process_image_detection(model, image_path, stop_event=None):
    img = Image.open(image_path).convert("RGB")
    outputs = run_inference(model, img, stop_event)

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
def process_images_classification(model, image_paths, stop_event=None):
    class_counts = {}
    image_classifications = []
    for image_path in image_paths:
        if stop_event and stop_event.is_set():
            raise InterruptedError("Inference was stopped.")
        try:
            img = Image.open(image_path).convert("RGB")
        except UnidentifiedImageError:
            print(f"Cannot identify image file {image_path}, skipping.")
            continue
        outputs = run_inference(model, img, stop_event)
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
def process_video(model, video_path, stop_event=None):
    cap = cv2.VideoCapture(video_path)
    while cap.isOpened():
        if stop_event and stop_event.is_set():
            raise InterruptedError("Inference was stopped.")
        ret, frame = cap.read()
        if not ret:
            break

        img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        outputs = run_inference(model, img, stop_event)
        draw = ImageDraw.Draw(img)
        detections = []

        if not outputs:
            print("No outputs from model")
            continue

        for result in outputs:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    label = int(box.cls)
                    label_name = model.names[label]
                    xyxy = box.xyxy[0].tolist()
                    detections.append((xyxy, label_name))
                    # Draw bounding box and label
                    draw.rectangle(xyxy, outline="red", width=2)
                    draw.text((xyxy[0], xyxy[1]), label_name, fill="red")

        frame_with_detections = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        cv2.imshow('frame', frame_with_detections)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

# Функция для обработки архива для классификации
def process_archive_classification(model, archive_path, extract_to, stop_event=None):
    with zipfile.ZipFile(archive_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)

    image_paths = []
    for root, _, files in os.walk(extract_to):
        for file in files:
            if file.endswith(('.png', '.jpg', '.jpeg')):
                image_paths.append(os.path.join(root, file))

    return process_images_classification(model, image_paths, stop_event)
