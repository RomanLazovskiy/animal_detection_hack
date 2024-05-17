import zipfile
import os
from ultralytics import YOLO
from PIL import Image, ImageDraw
import cv2
import numpy as np

# Загрузка моделей YOLOv8
detection_model = YOLO('yolov8n.pt')
classification_model = YOLO('yolov8n-cls.pt')

# Функция для выполнения инференса
def run_inference(model, img):
    results = model(img)
    return results

# Функция для обработки изображения для детекции и рисования bbox
def process_image_detection(model, image_path):
    img = Image.open(image_path).convert("RGB")
    outputs = run_inference(model, img)
    draw = ImageDraw.Draw(img)
    for output in outputs:
        if output.boxes is not None:
            for result in output.boxes:
                label = int(result.cls.numpy().item())
                label_name = model.names[label]
                box = result.xyxy.numpy().tolist()[0]
                draw.rectangle(box, outline="red", width=2)
                draw.text((box[0], box[1]), label_name, fill="red")
    return img

# Функция для обработки изображений для классификации
def process_images_classification(model, image_paths):
    class_counts = {}
    for image_path in image_paths:
        img = Image.open(image_path).convert("RGB")
        outputs = run_inference(model, img)
        for output in outputs:
            if output.probs is not None:
                label = int(output.probs.top1)
                label_name = model.names[label]
                class_counts[label_name] = class_counts.get(label_name, 0) + 1
    return class_counts

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
        for output in outputs:
            if output.boxes is not None:
                for result in output.boxes:
                    label = int(result.cls.numpy().item())
                    label_name = model.names[label]
                    box = result.xyxy.numpy().tolist()[0]
                    draw.rectangle(box, outline="red", width=2)
                    draw.text((box[0], box[1]), label_name, fill="red")
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
