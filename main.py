import pandas as pd
import re
import requests
import collections
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv('YT_API_KEY')

def parse_kindle(path):
    df = pd.read_csv(path)
    df['start_timestamp'] = pd.to_datetime(df['start_timestamp'], errors='coerce', utc=True)
    df['date'] = df['start_timestamp'].dt.date
    df['reading_minutes'] = df['total_reading_millis'] / 60000
    df.drop(df[df['device_family'] == 'Kindle for Mac'].index, inplace=True) # This is only necessary in my case because for some reason my Kindle app on MacOS bugged out and reported a lot of false data
    df.drop(columns=['device_serial_number', 'preferred_marketplace','ASIN','purchased_marketplace','device_family','device_serial_number','device_software_version','content_type', 'total_reading_millis', 'end_timestamp', 'start_timestamp'], inplace=True)
    df.dropna( inplace=True )
    df_daily = df.groupby('date')[['number_of_page_flips', 'reading_minutes']].sum()

    return df_daily

def parse_watch_history(path):
    watch_history = {}
    pattern = re.compile(
        r'watch\?v=([a-zA-Z0-9_-]{11})".*?'
        r'<br>([A-Za-z]{3}\s+\d{1,2},\s+\d{4})'
    )
    with open(path, encoding="utf-8") as f:
        matches = pattern.findall(f.read())
        for video_id, date in matches:
            watch_history[video_id] = date
    return watch_history

def api_get_duration(video_ids, api_key):
    url = "https://www.googleapis.com/youtube/v3/videos"
    durations = {}

    for i in range(0, len(video_ids), 50):
        chunk = video_ids[i : i + 50]
        params = {"part": "contentDetails", "id": ",".join(chunk), "key": api_key}
        r = requests.get(url, params=params).json()

        if "items" in r:
            for item in r["items"]:
                durations[item["id"]] = item["contentDetails"]["duration"]

    return durations

def iso_to_seconds(iso_duration):
    if not iso_duration:
        return 0
    match = re.match(
        r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso_duration
    )
    if not match:
        return 0
    hours = int(match.group(1)) if match.group(1) else 0
    minutes = int(match.group(2)) if match.group(2) else 0
    seconds = int(match.group(3)) if match.group(3) else 0
    return (hours * 3600) + (minutes * 60) + seconds

def parse_yt(path, api_key):
    #raw_history = parse_watch_history(path)
    raw_history = {'7DhPmHuajj4': 'Jan 16, 2024',
                   'W4jMTrrpSGQ': 'Jan 16, 2024',
                   'SWcYm29TUh8': 'Jan 16, 2024',
                   '-6Us2pnBRT4': 'Jan 16, 2024',
                   'wHXjuD97vFA': 'Jan 16, 2024',
                   'KXLREps3blw': 'Jan 16, 2024'}

    video_ids = list(raw_history.keys())
    video_durations = api_get_duration(video_ids, api_key)


    final_output = collections.defaultdict(list)

    for video_id, date in raw_history.items():
        # Look up the duration (defaults to None if video was deleted/private)
        duration = video_durations.get(video_id)
        if duration:
            final_output[date].append(duration)

    final_output = dict(final_output)

    processed_rows = []

    for date_str, durations in final_output.items():
        # Convert all durations for this day into seconds and sum them up
        total_seconds_for_day = sum(iso_to_seconds(d) for d in durations)

        processed_rows.append(
            {
                "Date": pd.to_datetime(date_str),  # Converts string to a real datetime object
                "Watchtime": total_seconds_for_day / 60,  # Keeps a raw number column for sorting/plotting
            }
        )

    df_yt = pd.DataFrame(processed_rows)
    df_yt = df_yt.sort_values(by="Date", ascending=False).reset_index(drop=True)

    return df_yt

