#!/usr/bin/env python3
"""
JobSwipe Backup Manager
A Python backup manager with scheduling, monitoring, and verification capabilities.

Features:
- Scheduled backup execution (full, incremental, WAL archiving)
- Backup verification and integrity checks
- Email notifications for backup status
- Metrics collection for monitoring
- Configuration management
"""

import os
import sys
import time
import json
import logging
import argparse
import subprocess
import schedule
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configuration
DEFAULT_CONFIG = {
    "backup": {
        "base_dir": "/var/backups/postgres",
        "wal_dir": "/var/backups/postgres/wal",
        "log_dir": "/var/log/postgres-backup",
        "retention_days": 30,
        "incremental_retention_days": 7
    },
    "database": {
        "host": "localhost",
        "port": 5432,
        "user": "postgres",
        "database": "postgres"
    },
    "schedule": {
        "full_backup": "0 2 * * 0",  # Weekly on Sunday at 2 AM
        "incremental_backup": "0 2 * * 1-6",  # Daily at 2 AM (Mon-Sat)
        "wal_archive": "*/30 * * * *",  # Every 30 minutes
        "verify_backup": "0 4 * * *",  # Daily at 4 AM
        "cleanup": "0 5 * * *"  # Daily at 5 AM
    },
    "notifications": {
        "smtp_server": "localhost",
        "smtp_port": 25,
        "sender_email": "backup@jobswipe.com",
        "recipient_emails": ["devops@jobswipe.com"],
        "subject_prefix": "[JobSwipe Backup]"
    },
    "encryption": {
        "enabled": True,
        "key_file": "/etc/backup/encryption.key"
    },
    "cloud": {
        "s3_bucket": "",
        "s3_region": "us-east-1",
        "gcs_bucket": "",
        "azure_container": ""
    }
}

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(DEFAULT_CONFIG["backup"]["log_dir"], "backup_manager.log"))
    ]
)
logger = logging.getLogger(__name__)


def load_config(config_file: Optional[str] = None) -> Dict:
    """Load configuration from file or use defaults."""
    config = DEFAULT_CONFIG.copy()

    if config_file and os.path.exists(config_file):
        try:
            with open(config_file, "r") as f:
                user_config = json.load(f)
            config.update(user_config)
            logger.info(f"Configuration loaded from: {config_file}")
        except Exception as e:
            logger.error(f"Error loading config file: {e}")
            logger.info("Using default configuration")

    return config


def run_command(cmd: List[str], env: Optional[Dict] = None) -> Dict:
    """Run a shell command and return results."""
    try:
        logger.info(f"Running command: {' '.join(cmd)}")
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env or os.environ
        )
        stdout, stderr = process.communicate(timeout=3600)

        return {
            "success": process.returncode == 0,
            "returncode": process.returncode,
            "stdout": stdout.strip(),
            "stderr": stderr.strip()
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "returncode": -1,
            "stdout": "",
            "stderr": "Command timed out"
        }
    except Exception as e:
        return {
            "success": False,
            "returncode": -1,
            "stdout": "",
            "stderr": str(e)
        }


def send_email_notification(config: Dict, subject: str, body: str):
    """Send email notification."""
    try:
        smtp_config = config["notifications"]
        msg = MIMEMultipart()
        msg["From"] = smtp_config["sender_email"]
        msg["To"] = ", ".join(smtp_config["recipient_emails"])
        msg["Subject"] = f"{smtp_config['subject_prefix']} {subject}"

        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(smtp_config["smtp_server"], smtp_config["smtp_port"]) as server:
            server.send_message(msg)

        logger.info("Email notification sent successfully")
    except Exception as e:
        logger.error(f"Failed to send email notification: {e}")


def perform_full_backup(config: Dict) -> Dict:
    """Perform a full PostgreSQL backup using pg_basebackup."""
    logger.info("Starting full backup...")

    cmd = [
        "/bin/bash",
        "/home/brooketogo98/jobswipe/backup/incremental_backup.sh",
        "full"
    ]

    result = run_command(cmd)

    if result["success"]:
        logger.info("Full backup completed successfully")
        send_email_notification(config, "Full Backup Successful", "Backup completed at: " + datetime.now().isoformat())
    else:
        logger.error(f"Full backup failed: {result['stderr']}")
        send_email_notification(config, "Full Backup Failed", f"Error: {result['stderr']}")

    return result


def perform_incremental_backup(config: Dict) -> Dict:
    """Perform an incremental PostgreSQL backup using pg_basebackup."""
    logger.info("Starting incremental backup...")

    cmd = [
        "/bin/bash",
        "/home/brooketogo98/jobswipe/backup/incremental_backup.sh",
        "incremental"
    ]

    result = run_command(cmd)

    if result["success"]:
        logger.info("Incremental backup completed successfully")
        send_email_notification(config, "Incremental Backup Successful", "Backup completed at: " + datetime.now().isoformat())
    else:
        logger.error(f"Incremental backup failed: {result['stderr']}")
        send_email_notification(config, "Incremental Backup Failed", f"Error: {result['stderr']}")

    return result


def verify_backup(config: Dict) -> Dict:
    """Verify backup integrity."""
    logger.info("Starting backup verification...")

    cmd = [
        "/bin/bash",
        "/home/brooketogo98/jobswipe/backup/incremental_backup.sh",
        "verify"
    ]

    result = run_command(cmd)

    if result["success"]:
        logger.info("Backup verification completed successfully")
    else:
        logger.error(f"Backup verification failed: {result['stderr']}")
        send_email_notification(config, "Backup Verification Failed", f"Error: {result['stderr']}")

    return result


def cleanup_old_backups(config: Dict) -> Dict:
    """Cleanup old backups according to retention policy."""
    logger.info("Starting backup cleanup...")

    cmd = [
        "/bin/bash",
        "/home/brooketogo98/jobswipe/backup/incremental_backup.sh",
        "cleanup"
    ]

    result = run_command(cmd)

    if result["success"]:
        logger.info("Backup cleanup completed successfully")
    else:
        logger.error(f"Backup cleanup failed: {result['stderr']}")

    return result


def setup_scheduler(config: Dict):
    """Set up the backup scheduler."""
    logger.info("Setting up backup scheduler...")

    # Full backup schedule
    full_schedule = config["schedule"]["full_backup"]
    schedule.every().sunday.at(full_schedule.split()[1]).do(perform_full_backup, config)
    logger.info(f"Full backup scheduled: {full_schedule}")

    # Incremental backup schedule
    incremental_schedule = config["schedule"]["incremental_backup"]
    for day in [1, 2, 3, 4, 5, 6]:  # Monday-Saturday
        schedule.every().day.at(incremental_schedule.split()[1]).do(perform_incremental_backup, config).tag(f"incremental_{day}")
    logger.info(f"Incremental backup scheduled: {incremental_schedule}")

    # Backup verification schedule
    verify_schedule = config["schedule"]["verify_backup"]
    schedule.every().day.at(verify_schedule.split()[1]).do(verify_backup, config)
    logger.info(f"Backup verification scheduled: {verify_schedule}")

    # Backup cleanup schedule
    cleanup_schedule = config["schedule"]["cleanup"]
    schedule.every().day.at(cleanup_schedule.split()[1]).do(cleanup_old_backups, config)
    logger.info(f"Backup cleanup scheduled: {cleanup_schedule}")

    logger.info("Scheduler setup completed")


def run_once(config: Dict):
    """Run all backup tasks once."""
    logger.info("Running all backup tasks once...")

    perform_full_backup(config)
    perform_incremental_backup(config)
    verify_backup(config)
    cleanup_old_backups(config)

    logger.info("All backup tasks completed")


def start_scheduler(config: Dict):
    """Start the backup scheduler."""
    logger.info("Starting backup manager scheduler...")

    setup_scheduler(config)

    # Run initial backup
    logger.info("Running initial backup...")
    run_once(config)

    # Start scheduler loop
    logger.info("Backup scheduler running. Press Ctrl+C to stop.")
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
            sys.exit(0)
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
            time.sleep(60)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="JobSwipe Backup Manager - A Python backup manager with scheduling"
    )
    parser.add_argument(
        "-c", "--config",
        help="Path to configuration file (default: None)",
        default=None
    )
    parser.add_argument(
        "-o", "--once",
        help="Run all backup tasks once and exit",
        action="store_true"
    )
    parser.add_argument(
        "-s", "--schedule",
        help="Start the backup scheduler (default)",
        action="store_true"
    )
    parser.add_argument(
        "-f", "--full",
        help="Perform a single full backup",
        action="store_true"
    )
    parser.add_argument(
        "-i", "--incremental",
        help="Perform a single incremental backup",
        action="store_true"
    )
    parser.add_argument(
        "-v", "--verify",
        help="Verify backup integrity",
        action="store_true"
    )
    parser.add_argument(
        "-C", "--cleanup",
        help="Cleanup old backups",
        action="store_true"
    )

    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)

    # Ensure log directory exists
    os.makedirs(config["backup"]["log_dir"], exist_ok=True)

    # Handle command-line arguments
    if args.once:
        run_once(config)
    elif args.full:
        perform_full_backup(config)
    elif args.incremental:
        perform_incremental_backup(config)
    elif args.verify:
        verify_backup(config)
    elif args.cleanup:
        cleanup_old_backups(config)
    else:
        start_scheduler(config)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"Backup manager failed: {e}")
        sys.exit(1)
