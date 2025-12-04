import cv2
import numpy as np
from PIL import Image
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / 'data'
ASSETS_DIR = ROOT_DIR / 'assets'
MODELS_DIR = ROOT_DIR / 'models'
DATASET_DIR = DATA_DIR / 'dataset'
CASCADE_PATH = ASSETS_DIR / 'haarcascade_frontalface_default.xml'
MODEL_PATH = MODELS_DIR / 'trainer.yml'


def get_images_and_labels(dataset_dir: Path):
    image_paths = sorted(dataset_dir.glob('User.*.jpg'))
    if not image_paths:
        raise FileNotFoundError('Dataset is empty. Run 01_create_dataset.py first.')

    detector = cv2.CascadeClassifier(str(CASCADE_PATH))
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    face_samples, ids = [], []

    for image_path in image_paths:
        try:
            pil_img = Image.open(image_path).convert('L')
        except IOError:
            print(f'[WARN] Could not read {image_path}, skipping...')
            continue

        img_numpy = np.array(pil_img, 'uint8')
        enhanced = clahe.apply(img_numpy)

        try:
            label = int(image_path.stem.split('.')[1])
        except (IndexError, ValueError):
            print(f'[WARN] Unexpected filename format: {image_path.name}, skipping...')
            continue

        faces = detector.detectMultiScale(
            enhanced,
            scaleFactor=1.1,
            minNeighbors=6,
            minSize=(80, 80)
        )
        if len(faces) == 0:
            continue

        for (x, y, w, h) in faces:
            face_samples.append(enhanced[y:y + h, x:x + w])
            ids.append(label)

    if not ids:
        raise RuntimeError('No faces were detected inside the dataset. Ensure captures are clear.')

    return face_samples, ids


def main():
    print('\n[INFO] Training faces. Grab a coffee—this may take a bit...')
    faces, ids = get_images_and_labels(DATASET_DIR)

    recognizer = cv2.face.LBPHFaceRecognizer_create(radius=2, neighbors=16, grid_x=8, grid_y=8)
    recognizer.train(faces, np.array(ids))
    MODEL_PATH.parent.mkdir(exist_ok=True)
    recognizer.write(str(MODEL_PATH))

    print(f"\n[INFO] Trained profiles: {len(np.unique(ids))}")
    print(f'[INFO] Model saved to {MODEL_PATH}')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(f'[ERROR] {exc}')