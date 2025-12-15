from __future__ import annotations

from collections import Counter, deque
import cv2
import pandas as pd
import math
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, Tuple, cast

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / 'data'
ASSETS_DIR = ROOT_DIR / 'assets'
MODELS_DIR = ROOT_DIR / 'models'
DATASET_DIR = DATA_DIR / 'dataset'
CASCADE_PATH = ASSETS_DIR / 'haarcascade_frontalface_default.xml'
MODEL_PATH = MODELS_DIR / 'trainer.yml'
USER_DETAILS_FILE = DATA_DIR / 'UserDetails.csv'
ATTENDANCE_FILE = DATA_DIR / 'Attendance.csv'
CLAHE = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
FACE_SIZE = (200, 200)
FaceMap = Dict[int, str]
StatusCallback = Callable[[str], None]
LogCallback = Callable[[str, str], None]
USER_COLUMNS = ['Id', 'Name']


def _lbph_match_quality(distance: float, threshold: float) -> float:
    """Map LBPH distance (lower is better) into a 0-100 display value.

    LBPH's `predict()` returns a distance-like score (lower is better), not a probability.
    This mapping is calibrated to the current decision threshold:
    - distance = 0      => 100%
    - distance = threshold => ~50%
    """

    threshold = float(threshold) if threshold and threshold > 0 else 100.0
    # exp(-ln(2) * d/t) gives 50% at d=t.
    quality = 100.0 * math.exp(-math.log(2.0) * (float(distance) / threshold))
    return max(0.0, min(100.0, quality))


def load_user_records(raise_if_missing: bool = False) -> pd.DataFrame:
    if not USER_DETAILS_FILE.exists():
        if raise_if_missing:
            raise FileNotFoundError('UserDetails.csv not found. Run 01_create_dataset.py first.')
        return pd.DataFrame(columns=USER_COLUMNS)

    df = pd.read_csv(USER_DETAILS_FILE)
    if 'Id' not in df.columns or 'Name' not in df.columns:
        raise ValueError('UserDetails.csv is missing required columns.')

    df = df.reindex(columns=USER_COLUMNS).copy()
    df['NumericId'] = pd.to_numeric(df['Id'], errors='coerce')
    invalid_rows = df[df['NumericId'].isna()]
    if not invalid_rows.empty:
        dropped = ', '.join(invalid_rows['Id'].astype(str).tolist())
        print(f"[WARN] Dropping invalid user IDs: {dropped}")
    df = df.dropna(subset=['NumericId'])
    df['Id'] = df['NumericId'].astype(int)
    df['Name'] = df['Name'].fillna('').astype(str)
    df = df.drop(columns=['NumericId'])
    return df.reset_index(drop=True)


def load_user_details() -> FaceMap:
    df = load_user_records(raise_if_missing=True)
    if df.empty:
        raise ValueError('No valid numeric user IDs found. Recreate your users.')
    ids = df['Id'].tolist()
    names = df['Name'].tolist()
    return cast(FaceMap, dict(zip(ids, names)))


def load_attendance() -> pd.DataFrame:
    columns = ['Id', 'Name', 'Date', 'Time']
    if ATTENDANCE_FILE.exists():
        df = pd.read_csv(ATTENDANCE_FILE)
        df = df.reindex(columns=columns, fill_value='')
        df = df.dropna(how='all')
        return df
    return pd.DataFrame(columns=columns)


def _persist_attendance(df: pd.DataFrame) -> None:
    df.to_csv(ATTENDANCE_FILE, index=False)


def delete_user_profile(user_id: int) -> dict[str, int]:
    df = load_user_records(raise_if_missing=True)
    if df.empty:
        raise ValueError('No users available to delete.')

    if user_id not in df['Id'].values:
        raise ValueError(f'User ID {user_id} not found.')

    updated_df = df[df['Id'] != user_id]
    updated_df.to_csv(USER_DETAILS_FILE, index=False)

    samples_removed = 0
    if DATASET_DIR.exists():
        for image_path in DATASET_DIR.glob(f'User.{user_id}.*.jpg'):
            try:
                image_path.unlink(missing_ok=True)
                samples_removed += 1
            except OSError as exc:
                print(f'[WARN] Unable to delete {image_path.name}: {exc}')

    return {'samples_removed': samples_removed}


def log_attendance_entry(
    user_id: int,
    user_name: str,
    attendance_df: pd.DataFrame,
) -> Tuple[pd.DataFrame, bool, str]:
    now = datetime.now()
    date_str = now.strftime('%Y-%m-%d')
    time_str = now.strftime('%H:%M:%S')

    duplicate = (
        (attendance_df['Id'] == user_id) &
        (attendance_df['Date'] == date_str)
    )
    if duplicate.any():
        return attendance_df, False, time_str

    new_entry = pd.DataFrame([{
        'Id': user_id,
        'Name': user_name,
        'Date': date_str,
        'Time': time_str,
    }])

    updated = pd.concat([attendance_df, new_entry], ignore_index=True)
    _persist_attendance(updated)
    return updated, True, time_str


def run_recognition(
    *,
    camera_index: int = 0,
    session_seconds: int = 90,
    # NOTE: OpenCV LBPH returns a distance-like score where LOWER is better.
    # We treat any raw_conf <= min_confidence as a match.
    min_confidence: float = 90.0,
    stable_frames: int = 4,
    stable_window: int = 8,
    stop_on_success: bool = True,
    display_window: bool = True,
    idle_hint_seconds: int = 20,
    status_callback: StatusCallback | None = None,
    log_callback: LogCallback | None = None,
) -> None:
    user_map = load_user_details()
    attendance_df = load_attendance()

    # Keep parameters aligned with scripts/02_train_model.py.
    recognizer = cv2.face.LBPHFaceRecognizer_create(radius=2, neighbors=8, grid_x=8, grid_y=8)
    recognizer.read(str(MODEL_PATH))
    face_cascade = cv2.CascadeClassifier(str(CASCADE_PATH))

    cam = cv2.VideoCapture(camera_index)
    cam.set(3, 640)
    cam.set(4, 480)

    start_time = datetime.now()
    last_activity_time = start_time
    last_status_msg = 'Camera online. Press ESC or Q in the OpenCV window to stop early.'

    def emit_status(message: str) -> None:
        nonlocal last_status_msg
        last_status_msg = message
        if status_callback:
            status_callback(message)

    def emit_log(name: str, timestamp: str) -> None:
        if log_callback:
            log_callback(name, timestamp)

    emit_status(last_status_msg)

    successful_log = False
    # Smooth out per-frame jitter: require N consistent matches in the last M frames.
    recent_matches: deque[int] = deque(maxlen=max(1, stable_window))
    recent_distances: dict[int, deque[float]] = {}

    try:
        while (datetime.now() - start_time).total_seconds() < session_seconds:
            ret, frame = cam.read()
            if not ret:
                emit_status('Camera feed unavailable. Exiting...')
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            enhanced = CLAHE.apply(gray)
            faces = face_cascade.detectMultiScale(
                enhanced,
                scaleFactor=1.1,
                minNeighbors=6,
                minSize=(80, 80)
            )

            for (x, y, w, h) in faces:
                roi = enhanced[y:y + h, x:x + w]
                roi = cv2.resize(roi, FACE_SIZE)
                label, raw_conf = recognizer.predict(roi)
                raw_conf_f = float(raw_conf)
                match_quality = _lbph_match_quality(raw_conf_f, min_confidence)

                # Track only plausible labels to stabilize decisions.
                if label in user_map:
                    recent_matches.append(label)
                    if label not in recent_distances:
                        recent_distances[label] = deque(maxlen=max(1, stable_window))
                    recent_distances[label].append(raw_conf_f)

                stable_label: int | None = None
                stable_distance: float | None = None
                if stable_frames > 1 and len(recent_matches) >= stable_frames:
                    label_counts = Counter(recent_matches)
                    candidate, count = label_counts.most_common(1)[0]
                    if count >= stable_frames:
                        distances = list(recent_distances.get(candidate, []))
                        if distances:
                            avg_dist = sum(distances) / len(distances)
                            stable_label = candidate
                            stable_distance = avg_dist

                effective_label = stable_label if stable_label is not None else label
                effective_distance = stable_distance if stable_distance is not None else raw_conf_f

                if effective_distance <= min_confidence and effective_label in user_map:
                    attendance_df, logged, time_str = log_attendance_entry(
                        effective_label,
                        user_map[effective_label],
                        attendance_df,
                    )
                    if logged:
                        emit_log(user_map[effective_label], time_str)
                        emit_status(f'Logged {user_map[effective_label]} @ {time_str}')
                        last_activity_time = datetime.now()
                        successful_log = True
                        if stop_on_success:
                            break
                    else:
                        emit_status(f'{user_map[effective_label]} already logged today.')
                    name_to_draw = user_map[effective_label]
                else:
                    name_to_draw = 'Unknown'
                    if effective_label in user_map:
                        effective_quality = _lbph_match_quality(effective_distance, min_confidence)
                        emit_status(
                            f'{user_map[effective_label]} detected (match {effective_quality:.0f}%). Need clearer view to log.'
                        )
                    else:
                        emit_status('Unknown face — enroll first or adjust lighting.')

                if display_window:
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    cv2.putText(frame, name_to_draw, (x + 5, y - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                    # Show match quality for the current face box.
                    cv2.putText(frame, f'{match_quality:.0f}%', (x + 5, y + h - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

            if display_window:
                idle_seconds = (datetime.now() - last_activity_time).total_seconds()
                if idle_hint_seconds > 0 and idle_seconds > idle_hint_seconds and not successful_log:
                    hint_text = 'No log yet — adjust pose or press Q to exit.'
                else:
                    hint_text = 'Press ESC or Q to exit at any time.'

                frame_height, frame_width = frame.shape[:2]
                overlay_height = 70
                cv2.rectangle(frame,
                              (0, frame_height - overlay_height),
                              (frame_width, frame_height),
                              (12, 20, 40), -1)
                cv2.putText(frame,
                            last_status_msg[:64],
                            (12, frame_height - overlay_height + 28),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.6,
                            (255, 255, 255),
                            1)
                cv2.putText(frame,
                            hint_text,
                            (12, frame_height - 18),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.55,
                            (56, 189, 248),
                            1)

                cv2.imshow('Attendance Camera', frame)
                key = cv2.waitKey(10) & 0xFF
                if key in (27, ord('q'), ord('Q')):
                    emit_status('Capture stopped by user input.')
                    break

            if successful_log and stop_on_success:
                emit_status('Attendance logged. Closing camera...')
                break
    finally:
        cam.release()
        if display_window:
            cv2.destroyAllWindows()
        if successful_log:
            emit_status('Camera session finished — log saved.')
        else:
            emit_status('Camera session finished.')