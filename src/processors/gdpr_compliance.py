import logging
from datetime import datetime
from sqlalchemy import text

db_logger = logging.getLogger("db")

class GDPRCompliance:
    
    def __init__(self, engine):
        self.engine = engine
    
    def delete_user_data(self, user_id):
        try:
            db_logger.info(f"GDPR deletion request initiated for user ID: {user_id}")
            
            with self.engine.begin() as conn:
                # Delete all records for the user from user_metrics
                result = conn.execute(
                    text("DELETE FROM user_metrics WHERE id = :user_id"),
                    {"user_id": user_id}
                )
                
                rows_deleted = result.rowcount
                
                if rows_deleted > 0:
                    db_logger.warning(
                        f"GDPR deletion completed: user_id={user_id}, "
                        f"rows_deleted={rows_deleted}, timestamp={datetime.utcnow().isoformat()}"
                    )
                    return {
                        "status": "success",
                        "user_id": user_id,
                        "rows_deleted": rows_deleted,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                else:
                    db_logger.info(f"GDPR deletion request for non-existent user: {user_id}")
                    return {
                        "status": "not_found",
                        "user_id": user_id,
                        "rows_deleted": 0,
                        "message": "No data found for this user"
                    }
                    
        except Exception as e:
            db_logger.error(
                f"GDPR deletion failed for user_id={user_id}: {str(e)}"
            )
            return {
                "status": "error",
                "user_id": user_id,
                "error": str(e)
            }
    
    def get_user_data(self, user_id):
        try:
            db_logger.info(f"Data portability request for user ID: {user_id}")
            
            with self.engine.connect() as conn:
                result = conn.execute(
                    text("SELECT * FROM user_metrics WHERE id = :user_id ORDER BY date"),
                    {"user_id": user_id}
                )
                
                rows = result.fetchall()
                db_logger.info(f"Data portability: retrieved {len(rows)} records for user {user_id}")
                
                return [dict(row._mapping) for row in rows]
                
        except Exception as e:
            db_logger.error(f"Data retrieval failed for user_id={user_id}: {str(e)}")
            return []
    
    def enforce_retention_policy(self, retention_days=365):
        try:
            db_logger.info(f"Enforcing data retention policy: {retention_days} days")
            
            with self.engine.begin() as conn:
                result = conn.execute(
                    text(
                        "DELETE FROM user_metrics WHERE date < CURRENT_DATE - INTERVAL ':days days'"
                    ),
                    {"days": retention_days}
                )
                
                rows_deleted = result.rowcount
                db_logger.info(f"Retention policy enforcement: deleted {rows_deleted} expired records")
                
                return {
                    "status": "success",
                    "rows_deleted": rows_deleted,
                    "retention_days": retention_days
                }
                
        except Exception as e:
            db_logger.error(f"Retention policy enforcement failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
