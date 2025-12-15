import cv2
import numpy as np
from PIL import Image
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from shared.paths import assets_dir, data_dir, models_dir

DATA_DIR = data_dir()
MODELS_DIR = models_dir()
DATASET_DIR = DATA_DIR / 'dataset'
CASCADE_PATH = assets_dir() / 'haarcascade_frontalface_default.xml'
MODEL_PATH = MODELS_DIR / 'trainer.yml'
FACE_SIZE = (200, 200)


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

        # Most dataset images are already cropped face ROIs.
        # If the cascade can't find a face in the ROI, fall back to using the full frame.
        if len(faces) == 0:
            h, w = enhanced.shape[:2]
            faces = [(0, 0, w, h)]

        for (x, y, w, h) in faces:
            roi = enhanced[y:y + h, x:x + w]
            roi = cv2.resize(roi, FACE_SIZE)
            face_samples.append(roi)
            ids.append(label)

    if not ids:
        raise RuntimeError('No faces were detected inside the dataset. Ensure captures are clear.')

    return face_samples, ids


def main():
    print('\n[INFO] Training faces. Grab a coffee—this may take a bit...')
    faces, ids = get_images_and_labels(DATASET_DIR)

    # NOTE: Keep these parameters in sync with backend.attendance_core.run_recognition.
    # Using neighbors=16 explodes histogram size (2^16 bins per cell) and creates multi-GB models.
    recognizer = cv2.face.LBPHFaceRecognizer_create(radius=2, neighbors=8, grid_x=8, grid_y=8)
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