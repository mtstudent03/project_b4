import os
from dotenv import load_dotenv
import pandas as pd
import shutil
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import insert

from processors.instagram_extract import parse_ig
from processors.youtube_extract import parse_yt
from processors.kindle_extract import parse_kindle
from processors.concentration_extract import parse_concentration
from processors.library_merger import library_merger

load_dotenv()
API_KEY = os.getenv('YT_API_KEY')

def db_engine():
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASS")
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    name = os.getenv("DB_NAME")

    connection_string = f"postgresql://{user}:{password}@{host}:{port}/{name}?sslmode=require"
    return create_engine(connection_string)

def process_all_users(base_directory, yt_api_key=None):
    all_user_data = []

    user_ids = [d for d in os.listdir(base_directory) if os.path.isdir(os.path.join(base_directory, d))]

    for user_id in user_ids:
        print(f"\n[INFO] Processing data for User ID: {user_id}...")
        user_folder = os.path.join(base_directory, user_id)

        ig_path = os.path.join(user_folder, "your_instagram_activity")
        yt_path = os.path.join(user_folder, "watch-history.html")
        reading_path = os.path.join(user_folder, "Kindle.Devices.ReadingSession.csv")
        concentration_path = os.path.join(user_folder, "concentration.csv")

        try:
            ig_df = parse_ig(ig_path)
        except Exception:
            print(f"   [WARN] Skipped Instagram processing for User ID: {user_id}")
            ig_df = pd.DataFrame()

        try:
            yt_df = parse_yt(yt_path, api_key=yt_api_key)
        except Exception:
            print(f"   [WARN] Skipped YouTube processing for User ID: {user_id}")
            yt_df = pd.DataFrame()

        try:
            reading_df = parse_kindle(reading_path)
        except Exception:
            print(f"   [WARN] Skipped Kindle processing for User ID: {user_id}")
            reading_df = pd.DataFrame()

        try:
            concentration_df = parse_concentration(concentration_path)
        except Exception:
            print(f"   [WARN] Skipped Concentration processing for User ID: {user_id}")
            concentration_df = pd.DataFrame()

        user_master = library_merger(yt_df, reading_df, ig_df, concentration_df)

        if not user_master.empty:
            user_master = user_master.reset_index().rename(columns={'index': 'date'})
            user_master.insert(0, 'id', user_id)

            all_user_data.append(user_master)
            # if os.path.exists(user_folder):   #Only to be used in production environments
            #     shutil.rmtree(user_folder)    #Deletes the raw user data so only the encrypted form in the database remains

    if all_user_data:
        final_global_df = pd.concat(all_user_data, ignore_index=True)
        final_global_df = final_global_df.sort_values(by=['id', 'date']).reset_index(drop=True)
        return final_global_df
    else:
        return pd.DataFrame()


def migrate_schema(engine):
    migrations = [
        "ALTER TABLE user_metrics ADD COLUMN IF NOT EXISTS yt_time FLOAT",
        "ALTER TABLE user_metrics ADD COLUMN IF NOT EXISTS concentration INTEGER",
    ]
    with engine.begin() as conn:
        for stmt in migrations:
            conn.execute(text(stmt))

def upsert(table, conn, keys, data_iter):
    rows = [dict(zip(keys, row)) for row in data_iter]
    stmt = insert(table.table).values(rows)
    update_cols = {k: stmt.excluded[k] for k in keys if k not in ('id', 'date')}
    conn.execute(stmt.on_conflict_do_update(index_elements=['id', 'date'], set_=update_cols))

def main():
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')

    master_df = process_all_users(data_dir, yt_api_key=API_KEY)

    print("\n--- GLOBAL LIBRARY ---")
    print(master_df)

    if not master_df.empty:
        print("\n[INFO] Initializing secure transport layer handshake...")
        try:
            engine = db_engine()
            migrate_schema(engine)

            master_df.to_sql("user_metrics", con=engine, if_exists="append", index=False, method=upsert)
            print("[SUCCESS] Data securely encrypted in transit and pushed to Postgres.")


        except Exception as db_error:
            print(f"[WARN] Database write pipeline aborted: {db_error}")

if __name__ == "__main__":
    main()

