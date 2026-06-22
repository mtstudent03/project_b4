import os
from dotenv import load_dotenv
from processors.instagram_extract import parse_ig
from processors.youtube_extract import parse_yt
from processors.kindle_extract import parse_kindle
from processors.library_merger import library_merger
import pandas as pd

yt_file = os.path.join('..','data','watch_history.html')
kindle_file = os.path.join('..','data','Kindle.Devices.ReadingSession.csv')
ig_file = os.path.join('..','data','your_instagram_activity')

load_dotenv()
API_KEY = os.getenv('YT_API_KEY')

def process_all_users(base_directory, yt_api_key=None):
    all_user_data = []

    user_ids = [d for d in os.listdir(base_directory) if os.path.isdir(os.path.join(base_directory, d))]

    for user_id in user_ids:
        print(f"\nProcessing data for User ID: {user_id}...")
        user_folder = os.path.join(base_directory, user_id)

        ig_path = os.path.join(user_folder, "your_instagram_activity")
        yt_path = os.path.join(user_folder, "youtube_data.json")
        reading_path = os.path.join(user_folder, "Kindle.Devices.ReadingSession.csv")

        try:
            ig_df = parse_ig(ig_path)
        except Exception as e:
            print(f"   [Skipped Instagram for {user_id}: {e}]")
            ig_df = pd.DataFrame()

        try:
            yt_df = parse_yt(yt_path, api_key=yt_api_key)
        except Exception as e:
            print(f"   [Skipped YouTube for {user_id}: {e}]")
            yt_df = pd.DataFrame()

        try:
            reading_df = parse_kindle(reading_path)
        except Exception as e:
            print(f"   [Skipped Kindle for {user_id}: {e}]")
            reading_df = pd.DataFrame()

        user_master = library_merger(yt_df, reading_df, ig_df)

        if not user_master.empty:
            user_master = user_master.reset_index().rename(columns={'index': 'date'})
            user_master.insert(0, 'id', user_id)  # Inserts 'id' as the very first column

            all_user_data.append(user_master)

    if all_user_data:
        final_global_df = pd.concat(all_user_data, ignore_index=True)
        final_global_df = final_global_df.sort_values(by=['id', 'date']).reset_index(drop=True)
        return final_global_df
    else:
        return pd.DataFrame()


def main():
    data_dir = os.path.join('..','data')

    master_df = process_all_users(data_dir, yt_api_key=API_KEY)

    print("\n--- GLOBAL LIBRARY ---")
    print(master_df)

if __name__ == "__main__":
    main()

