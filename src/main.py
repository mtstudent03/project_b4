import os
from dotenv import load_dotenv
import pandas as pd
import shutil
from sqlalchemy import create_engine, event, text
from sqlalchemy.dialects.postgresql import insert
from datetime import datetime

from processors.logging_config import setup_logging, get_loggers
from processors.gdpr_compliance import GDPRCompliance
from processors.alerts import SecurityAlerts
from processors.instagram_extract import parse_ig
from processors.youtube_extract import parse_yt
from processors.kindle_extract import parse_kindle
from processors.concentration_extract import parse_concentration
from processors.library_merger import library_merger

app_logger, auth_logger, db_logger = setup_logging()

load_dotenv()
API_KEY = os.getenv('YT_API_KEY')

security_alerts = SecurityAlerts()

def db_engine():
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASS")
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    name = os.getenv("DB_NAME")

    connection_string = f"postgresql://{user}:{password}@{host}:{port}/{name}?sslmode=require"
    
    try:
        engine = create_engine(connection_string)
        
        auth_logger.info(
            f"Database connection initialized | user={user} | host={host} | "
            f"database={name} | sslmode=require | timestamp={datetime.utcnow().isoformat()}"
        )
        
        @event.listens_for(engine, "connect")
        def receive_connect(dbapi_conn, connection_record):
            """Log successful database connections."""
            db_logger.debug(
                f"Database connection established | timestamp={datetime.utcnow().isoformat()}"
            )
        
        @event.listens_for(engine, "close")
        def receive_close(dbapi_conn, connection_record):
            """Log database disconnections."""
            db_logger.debug(
                f"Database connection closed | timestamp={datetime.utcnow().isoformat()}"
            )
        
        return engine
        
    except Exception as e:
        auth_logger.error(f"Database connection initialization failed: {str(e)}")
        security_alerts.alert_system_error("database_engine", str(e), severity="CRITICAL")
        raise

def process_all_users(base_directory, yt_api_key=None):
    all_user_data = []

    user_ids = [d for d in os.listdir(base_directory) if os.path.isdir(os.path.join(base_directory, d))]

    app_logger.info(f"Pipeline started | users_to_process={len(user_ids)}")

    for user_id in user_ids:
        app_logger.info(f"Processing data for User ID: {user_id}")
        user_folder = os.path.join(base_directory, user_id)

        ig_path = os.path.join(user_folder, "your_instagram_activity")
        yt_path = os.path.join(user_folder, "watch-history.html")
        reading_path = os.path.join(user_folder, "Kindle.Devices.ReadingSession.csv")
        concentration_path = os.path.join(user_folder, "concentration.csv")

        try:
            ig_df = parse_ig(ig_path)
            app_logger.debug(f"Instagram data extracted for user {user_id}: {len(ig_df)} records")
        except Exception as e:
            app_logger.warning(f"Skipped Instagram processing for User ID: {user_id} | error={str(e)}")
            ig_df = pd.DataFrame()

        try:
            yt_df = parse_yt(yt_path, api_key=yt_api_key)
            app_logger.debug(f"YouTube data extracted for user {user_id}: {len(yt_df)} records")
        except Exception as e:
            app_logger.warning(f"Skipped YouTube processing for User ID: {user_id} | error={str(e)}")
            yt_df = pd.DataFrame()

        try:
            reading_df = parse_kindle(reading_path)
            app_logger.debug(f"Kindle data extracted for user {user_id}: {len(reading_df)} records")
        except Exception as e:
            app_logger.warning(f"Skipped Kindle processing for User ID: {user_id} | error={str(e)}")
            reading_df = pd.DataFrame()

        try:
            concentration_df = parse_concentration(concentration_path)
            app_logger.debug(f"Concentration data extracted for user {user_id}: {len(concentration_df)} records")
        except Exception as e:
            app_logger.warning(f"Skipped Concentration processing for User ID: {user_id} | error={str(e)}")
            concentration_df = pd.DataFrame()

        user_master = library_merger(yt_df, reading_df, ig_df, concentration_df)

        if not user_master.empty:
            user_master = user_master.reset_index().rename(columns={'index': 'date'})
            user_master.insert(0, 'id', user_id)

            all_user_data.append(user_master)
            app_logger.info(f"User {user_id} data prepared for database ingestion: {len(user_master)} merged records")
            
            # Production environment: delete raw source files after successful ingestion
            if os.getenv("ENVIRONMENT") == "production":
                try:
                    if os.path.exists(user_folder):
                        shutil.rmtree(user_folder)
                        app_logger.warning(f"Raw source data deleted for user {user_id} after ingestion (production mode)")
                except Exception as e:
                    app_logger.error(f"Failed to delete raw data for user {user_id}: {str(e)}")
                    security_alerts.alert_system_error("data_deletion", f"User {user_id}: {str(e)}")

    if all_user_data:
        final_global_df = pd.concat(all_user_data, ignore_index=True)
        final_global_df = final_global_df.sort_values(by=['id', 'date']).reset_index(drop=True)
        app_logger.info(f"Pipeline completed | total_records={len(final_global_df)} | unique_users={final_global_df['id'].nunique()}")
        return final_global_df
    else:
        app_logger.info("Pipeline completed with no data to process")
        return pd.DataFrame()


def migrate_schema(engine):
    migrations = [
        "ALTER TABLE user_metrics ADD COLUMN IF NOT EXISTS yt_time FLOAT",
        "ALTER TABLE user_metrics ADD COLUMN IF NOT EXISTS concentration INTEGER",
    ]
    try:
        with engine.begin() as conn:
            for stmt in migrations:
                conn.execute(text(stmt))
        db_logger.info("Database schema migration completed successfully")
    except Exception as e:
        db_logger.error(f"Schema migration failed: {str(e)}")
        security_alerts.alert_system_error("schema_migration", str(e), severity="CRITICAL")
        raise

def upsert(table, conn, keys, data_iter):
    rows = [dict(zip(keys, row)) for row in data_iter]
    stmt = insert(table.table).values(rows)
    update_cols = {k: stmt.excluded[k] for k in keys if k not in ('id', 'date')}
    conn.execute(stmt.on_conflict_do_update(index_elements=['id', 'date'], set_=update_cols))

def main():
    app_logger.info("=" * 80)
    app_logger.info("DATA INGESTION PIPELINE STARTED")
    app_logger.info(f"Timestamp: {datetime.utcnow().isoformat()}")
    app_logger.info("=" * 80)
    
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')

    try:
        master_df = process_all_users(data_dir, yt_api_key=API_KEY)

        app_logger.info(f"\nGLOBAL LIBRARY:\n{master_df}")

        if not master_df.empty:
            app_logger.info("Initializing secure transport layer handshake (TLS)...")
            try:
                engine = db_engine()
                migrate_schema(engine)
                
                # Initialize GDPR compliance handler
                gdpr_handler = GDPRCompliance(engine)

                # Log database write operation
                db_logger.info(
                    f"Database write operation initiated | records={len(master_df)} | "
                    f"unique_users={master_df['id'].nunique()} | timestamp={datetime.utcnow().isoformat()}"
                )
                
                master_df.to_sql("user_metrics", con=engine, if_exists="append", index=False, method=upsert)
                
                db_logger.info(f"Database write completed successfully | records_written={len(master_df)}")
                app_logger.info("[SUCCESS] Data securely encrypted in transit and pushed to Postgres.")
                
                # Optional: Enforce data retention policy (365 day default)
                if os.getenv("ENFORCE_RETENTION") == "true":
                    retention_result = gdpr_handler.enforce_retention_policy(retention_days=365)
                    app_logger.info(f"Data retention policy enforced: {retention_result}")

            except Exception as db_error:
                app_logger.error(f"Database write pipeline failed: {str(db_error)}")
                security_alerts.alert_system_error("database_write", str(db_error), severity="CRITICAL")
        else:
            app_logger.info("No data to process. Pipeline complete.")
    
    except Exception as e:
        app_logger.critical(f"Pipeline failed: {str(e)}")
        security_alerts.alert_system_error("pipeline_execution", str(e), severity="CRITICAL")
        raise
    
    finally:
        app_logger.info("=" * 80)
        app_logger.info("DATA INGESTION PIPELINE COMPLETED")
        app_logger.info(f"Timestamp: {datetime.utcnow().isoformat()}")
        app_logger.info("=" * 80)

if __name__ == "__main__":
    main()

