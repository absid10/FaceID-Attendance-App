from __future__ import annotations

import pandas as pd

from backend.storage import Storage

_STORAGE = Storage()
_STORAGE.migrate_from_csv_if_needed()
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
    df = _STORAGE.requests_df()
    return _normalize(df)


def save_requests(df: pd.DataFrame) -> None:
    # Requests are stored in SQLite; CSV is not the source of truth.
    return


def add_request(name: str, contact: str, message: str) -> None:
    _STORAGE.add_request(name=name, contact=contact, message=message)


def update_request_status(request_id: int, status: str) -> None:
    _STORAGE.update_request_status(request_id, status)
