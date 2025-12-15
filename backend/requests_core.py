from __future__ import annotations

import pandas as pd
from datetime import datetime

from shared.paths import data_dir

REQUESTS_FILE = data_dir() / 'EnrollmentRequests.csv'
COLUMNS = ['RequestId', 'Name', 'Contact', 'Message', 'Timestamp', 'Status']


def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    df = df.reindex(columns=COLUMNS, fill_value='').copy()
    if df.empty:
        return pd.DataFrame(columns=COLUMNS)

    if 'RequestId' not in df or df['RequestId'].isna().all():
        df['RequestId'] = range(1, len(df) + 1)
    else:
        df['RequestId'] = pd.to_numeric(df['RequestId'], errors='coerce')
        max_id = df['RequestId'].dropna().max()
        max_id = 0 if pd.isna(max_id) else int(max_id)
        next_id = max_id + 1
        for idx in df[df['RequestId'].isna()].index:
            df.at[idx, 'RequestId'] = next_id
            next_id += 1
        df['RequestId'] = df['RequestId'].astype(int)
    return df


def load_requests() -> pd.DataFrame:
    if REQUESTS_FILE.exists():
        df = pd.read_csv(REQUESTS_FILE)
        return _normalize(df)
    return pd.DataFrame(columns=COLUMNS)


def save_requests(df: pd.DataFrame) -> None:
    df.to_csv(REQUESTS_FILE, index=False)


def add_request(name: str, contact: str, message: str) -> None:
    name = name.strip()
    contact = contact.strip()
    message = message.strip()
    if not name:
        raise ValueError('Name is required.')
    if not contact:
        raise ValueError('Contact info is required.')
    if not message:
        raise ValueError('Please describe your request.')

    df = load_requests()
    next_id = int(df['RequestId'].max()) + 1 if not df.empty else 1
    new_row = pd.DataFrame([{
        'RequestId': next_id,
        'Name': name,
        'Contact': contact,
        'Message': message,
        'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'Status': 'Pending',
    }])
    df = pd.concat([df, new_row], ignore_index=True)
    save_requests(df)


def update_request_status(request_id: int, status: str) -> None:
    df = load_requests()
    mask = df['RequestId'] == request_id
    if not mask.any():
        raise ValueError(f'Request ID {request_id} not found.')
    df.loc[mask, 'Status'] = status
    save_requests(df)
