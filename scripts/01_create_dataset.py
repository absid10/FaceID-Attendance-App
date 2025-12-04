import argparse

import cv2
import pandas as pd
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / 'data'
ASSETS_DIR = ROOT_DIR / 'assets'
DATASET_DIR = DATA_DIR / 'dataset'
CASCADE_PATH = ASSETS_DIR / 'haarcascade_frontalface_default.xml'
USER_DETAILS_FILE = DATA_DIR / 'UserDetails.csv'
SAMPLES_PER_USER = 80
BLUR_THRESHOLD = 60.0  # Higher value => stricter sharpness requirement


def prompt_user_metadata():
    while True:
        face_id = input('\nEnter a numeric User ID: ').strip()
        if face_id.isdigit():
            break
        print('[WARN] The ID must be numeric.')

    face_name = input('Enter a User Name: ').strip()
    if not face_name:
        raise ValueError('User name cannot be empty.')
    return int(face_id), face_name


def register_user(face_id: int, face_name: str) -> None:
    new_user = pd.DataFrame([{'Id': face_id, 'Name': face_name}])
    if USER_DETAILS_FILE.exists():
        df = pd.read_csv(USER_DETAILS_FILE)
        if face_id in df['Id'].values:
            df.loc[df['Id'] == face_id, 'Name'] = face_name
            df.to_csv(USER_DETAILS_FILE, index=False)
            print(f'[INFO] Updated existing user {face_id} -> {face_name}.')
            return
        new_user.to_csv(USER_DETAILS_FILE, mode='a', header=False, index=False)
    else:
        new_user.to_csv(USER_DETAILS_FILE, index=False)
    print(f'[INFO] Registered user {face_name} with ID {face_id}.')


def is_frame_sharp(gray_roi) -> bool:
    variance = cv2.Laplacian(gray_roi, cv2.CV_64F).var()
    return variance >= BLUR_THRESHOLD


def parse_args():
    parser = argparse.ArgumentParser(description='Capture face samples for attendance model.')
    parser.add_argument('--id', type=int, dest='face_id', help='Numeric user ID to enroll.')
    parser.add_argument('--name', type=str, dest='face_name', help='User name to enroll.')
    parser.add_argument('--samples', type=int, default=SAMPLES_PER_USER,
                        help='Number of samples to capture (default: 80).')
    return parser.parse_args()


def main():
    args = parse_args()
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    if args.face_id is not None and args.face_name:
        face_id, face_name = args.face_id, args.face_name.strip()
        if not face_name:
            raise ValueError('Provided --name cannot be empty.')
        print(f"[INFO] Auto-enrolling {face_name} (ID {face_id})")
    else:
        face_id, face_name = prompt_user_metadata()
    target_samples = args.samples if args.samples > 0 else SAMPLES_PER_USER

    cam = cv2.VideoCapture(0)
    cam.set(3, 640)
    cam.set(4, 480)

    face_detector = cv2.CascadeClassifier(str(CASCADE_PATH))
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))

    print('\n[INFO] Initializing face capture. Keep your face inside the box...')
    count = 0

    while True:
        ret, frame = cam.read()
        if not ret:
            print('[ERROR] Camera feed unavailable. Exiting capture loop.')
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        enhanced = clahe.apply(gray)
        faces = face_detector.detectMultiScale(
            enhanced,
            scaleFactor=1.2,
            minNeighbors=6,
            minSize=(80, 80)
        )

        for (x, y, w, h) in faces:
            face_roi = enhanced[y:y + h, x:x + w]
            if not is_frame_sharp(face_roi):
                continue

            count += 1
            file_path = DATASET_DIR / f'User.{face_id}.{count}.jpg'
            cv2.imwrite(str(file_path), face_roi)

            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
            cv2.putText(frame, f'Samples: {count}/{target_samples}', (20, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.imshow('Dataset Capture', frame)

        if cv2.waitKey(50) & 0xFF == 27:
            print('[INFO] Capture interrupted by user.')
            break

        if count >= target_samples:
            print('[INFO] Target sample count reached.')
            break

    cam.release()
    cv2.destroyAllWindows()

    if count:
        register_user(face_id, face_name)
        print(f"\n[INFO] Saved {count} usable samples to {DATASET_DIR}.")
    else:
        print('[WARN] No samples captured. User was not registered.')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(f'[ERROR] {exc}')