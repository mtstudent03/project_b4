import pandas as pd
import json
from bs4 import BeautifulSoup as bs

def parse_kindle(path):
    df = pd.read_csv(path)
    df['start_timestamp'] = pd.to_datetime(df['start_timestamp'], errors='coerce', utc=True)
    df['date'] = df['start_timestamp'].dt.date
    df['reading_minutes'] = df['total_reading_millis'] / 60000
    df.drop(columns=['device_serial_number', 'preferred_marketplace','ASIN','purchased_marketplace','device_family','device_serial_number','device_software_version','content_type', 'total_reading_millis', 'end_timestamp', 'start_timestamp'], inplace=True)
    df.dropna( inplace=True )
    df_daily = df.groupby('date')[['number_of_page_flips', 'reading_minutes']].sum()

    return df_daily

kindle_data = parse_kindle("Kindle.Devices.ReadingSession.csv")

print(kindle_data)