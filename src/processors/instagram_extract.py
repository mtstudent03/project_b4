import pandas as pd
import os
import json

def find_timestamps(data, timestamps):
    timestamp_keys = {'timestamp', 'timestamp_ms', 'timestamp_value'}
    if isinstance(data, dict):
        for key, value in data.items():
            if key in timestamp_keys and isinstance(value, (int, str)):
                timestamps.append(value)
            else:
                find_timestamps(value, timestamps)
    elif isinstance(data, list):
        for item in data:
            find_timestamps(item, timestamps)

def extract_instagram_timestamps(root_folder):

    timestamps = []

    for dirpath, _, filenames in os.walk(root_folder):
        for filename in filenames:
            if filename.endswith('.json'):
                file_path = os.path.join(dirpath, filename)

                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        json_data = json.load(f)
                        find_timestamps(json_data, timestamps)
                except (json.JSONDecodeError, PermissionError, UnicodeDecodeError):
                    continue

    df = pd.DataFrame(timestamps, columns=['timestamp'])

    if not df.empty:
        def parse_ts(val):
            try:
                t = float(val)
                return pd.Timestamp(t, unit='ms') if t > 1e10 else pd.Timestamp(t, unit='s')
            except (ValueError, TypeError):
                return pd.NaT
        df['timestamp'] = df['timestamp'].apply(parse_ts)
        df = df.dropna().sort_values(by='timestamp').reset_index(drop=True)

    return df

def detect_user_sessions(df, threshold_minutes=30):

    if df.empty or 'timestamp' not in df.columns:
        return pd.DataFrame()

    df = df.sort_values(by='timestamp').reset_index(drop=True)

    df['date'] = df['timestamp'].dt.date

    df['time_diff'] = df['timestamp'].diff()
    threshold_delta = pd.Timedelta(minutes=threshold_minutes)
    df['new_session_trigger'] = df['time_diff'] > threshold_delta
    df['session_id'] = df['new_session_trigger'].cumsum()

    session_summary = df.groupby(['date', 'session_id']).agg(
        session_start=('timestamp', 'min'),
        session_end=('timestamp', 'max'),
        activity_count=('timestamp', 'count')
    ).reset_index()

    session_summary['duration'] = session_summary['session_end'] - session_summary['session_start']

    daily_library = session_summary.groupby('date').agg(
        ig_time=('duration', 'sum'),
    ).reset_index()

    return daily_library

def parse_ig(path):
    df_timestamps = extract_instagram_timestamps(path)

    if df_timestamps.empty:
        print("No timestamps found.")
        return pd.DataFrame()
    else:
        daily_library_df = detect_user_sessions(df_timestamps, threshold_minutes=20)

        final_ig = daily_library_df.groupby('date')[['ig_time']].sum()

        final_ig['ig_time'] = final_ig['ig_time'].dt.total_seconds() / 60.0
        final_ig.index = pd.to_datetime(final_ig.index)

        return final_ig