import pandas as pd

def parse_kindle(path):
    df = pd.read_csv(path)
    df['start_timestamp'] = pd.to_datetime(df['start_timestamp'], errors='coerce', utc=True)
    df['date'] = df['start_timestamp'].dt.date
    df['reading_minutes'] = df['total_reading_millis'] / 60000

    df = df[df['device_family'] != 'Kindle for Mac']
    df = df.drop(columns=['device_serial_number', 'preferred_marketplace', 'ASIN', 'purchased_marketplace', 'device_family', 'device_software_version', 'content_type', 'total_reading_millis', 'end_timestamp', 'start_timestamp'])
    df = df.dropna()

    result = df.groupby('date').agg(page_flips=('number_of_page_flips', 'sum'),reading_time=('reading_minutes', 'sum'))
    result.index = pd.to_datetime(result.index)

    return result