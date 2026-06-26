import logging
import os
from datetime import datetime
from collections import defaultdict, deque

app_logger = logging.getLogger("app")
auth_logger = logging.getLogger("auth")

class AlertThreshold:    
    def __init__(self, max_failures=5, time_window_minutes=15):
        self.max_failures = max_failures
        self.time_window_seconds = time_window_minutes * 60
        self.failure_timestamps = defaultdict(deque)
    
    def record_failure(self, identifier):
        current_time = datetime.utcnow()
        self.failure_timestamps[identifier].append(current_time)
        
        # Clean up old timestamps outside the window
        cutoff_time = (current_time.timestamp() - self.time_window_seconds)
        while self.failure_timestamps[identifier]:
            oldest = self.failure_timestamps[identifier][0]
            if oldest.timestamp() < cutoff_time:
                self.failure_timestamps[identifier].popleft()
            else:
                break
    
    def should_alert(self, identifier):
        return len(self.failure_timestamps[identifier]) >= self.max_failures

class SecurityAlerts:
    
    def __init__(self, alert_log_dir="../logs"):
        self.alert_log_dir = alert_log_dir
        if not os.path.exists(alert_log_dir):
            os.makedirs(alert_log_dir)
        
        self.auth_failures = AlertThreshold(max_failures=5, time_window_minutes=15)
        self.data_access = AlertThreshold(max_failures=10, time_window_minutes=30)
    
    def alert_authentication_failure(self, db_user, host=None, error_msg=None):
        identifier = f"{db_user}:{host}" if host else db_user
        self.auth_failures.record_failure(identifier)
        
        auth_logger.error(
            f"Authentication failure | user={db_user} | host={host} | error={error_msg}"
        )
        
        if self.auth_failures.should_alert(identifier):
            self._trigger_alert(
                alert_type="CRITICAL",
                title="Multiple Authentication Failures",
                details={
                    "user": db_user,
                    "host": host,
                    "failures_in_window": len(self.auth_failures.failure_timestamps[identifier]),
                    "threshold": self.auth_failures.max_failures,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
    
    def alert_data_access_anomaly(self, user_id, access_type, details=None):
        identifier = f"{user_id}:{access_type}"
        self.data_access.record_failure(identifier)
        
        db_logger = logging.getLogger("db")
        db_logger.warning(
            f"Data access event | user={user_id} | type={access_type} | details={details}"
        )
        
        if self.data_access.should_alert(identifier):
            self._trigger_alert(
                alert_type="WARNING",
                title="Unusual Data Access Pattern",
                details={
                    "user": user_id,
                    "access_type": access_type,
                    "pattern_details": details,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
    
    def alert_system_error(self, component, error_msg, severity="ERROR"):
        app_logger.error(
            f"System error | component={component} | severity={severity} | error={error_msg}"
        )
        
        if severity in ["CRITICAL"]:
            self._trigger_alert(
                alert_type=severity,
                title=f"System Error in {component}",
                details={
                    "component": component,
                    "error": error_msg,
                    "severity": severity,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
    
    def _trigger_alert(self, alert_type, title, details):
        alert_msg = f"[{alert_type}] {title} | {details}"
        
        alert_log_path = os.path.join(self.alert_log_dir, "alerts.log")
        with open(alert_log_path, "a") as f:
            f.write(f"{datetime.utcnow().isoformat()} | {alert_msg}\n")
        
        app_logger.critical(f"ALERT TRIGGERED: {alert_msg}")
        
        print(f"\n⚠️  SECURITY ALERT: {title}")
        print(f"   Severity: {alert_type}")
        print(f"   Details: {details}\n")
