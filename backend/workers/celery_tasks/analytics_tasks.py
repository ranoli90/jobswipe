"""
Analytics Background Tasks

Celery tasks for analytics data collection and reporting.
"""

import json
import logging
from datetime import datetime, timedelta

from backend.db.database import get_db
from backend.db.models import ApplicationTask, Job, User, UserJobInteraction
from backend.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task
def generate_hourly_snapshot():
    """
    Generate hourly analytics snapshot for monitoring.

    Returns:
        Snapshot data
    """
    db = next(get_db())

    try:
        now = datetime.utcnow()
        hour_ago = now - timedelta(hours=1)

        # Count interactions in the last hour
        interactions = (
            db.query(UserJobInteraction)
            .filter(UserJobInteraction.created_at >= hour_ago)
            .count()
        )

        applications = (
            db.query(ApplicationTask)
            .filter(ApplicationTask.created_at >= hour_ago)
            .count()
        )

        # Count active users in the last hour
        active_users = (
            db.query(UserJobInteraction)
            .filter(UserJobInteraction.created_at >= hour_ago)
            .distinct(UserJobInteraction.user_id)
            .count()
        )

        snapshot = {
            "timestamp": now.isoformat(),
            "period": "hourly",
            "interactions": interactions,
            "applications": applications,
            "active_users": active_users,
            "jobs_available": db.query(Job).filter(Job.is_active == True).count(),
        }

        # Store in Redis for quick access
        import redis

        r = redis.Redis(host="redis", port=6379, decode_responses=True)
        r.setex("analytics:hourly_snapshot", 3600, json.dumps(snapshot))

        logger.info(
            f"Generated hourly snapshot: {interactions} interactions, {applications} applications"
        )
        return snapshot

    except Exception as e:
        logger.error(f"Error generating hourly snapshot: {e}")
        return {"error": str(e)}
    finally:
        db.close()


@celery_app.task
def calculate_daily_metrics():
    """
    Calculate and store daily metrics for historical analysis.

    Returns:
        Daily metrics summary
    """
    db = next(get_db())

    try:
        today = datetime.utcnow().date()
        start_of_day = datetime.combine(today, datetime.min.time())
        end_of_day = start_of_day + timedelta(days=1)

        # Get daily metrics
        new_users = (
            db.query(User)
            .filter(User.created_at >= start_of_day, User.created_at < end_of_day)
            .count()
        )

        new_jobs = (
            db.query(Job)
            .filter(Job.created_at >= start_of_day, Job.created_at < end_of_day)
            .count()
        )

        total_interactions = (
            db.query(UserJobInteraction)
            .filter(
                UserJobInteraction.created_at >= start_of_day,
                UserJobInteraction.created_at < end_of_day,
            )
            .count()
        )

        total_applications = (
            db.query(ApplicationTask)
            .filter(
                ApplicationTask.created_at >= start_of_day,
                ApplicationTask.created_at < end_of_day,
            )
            .count()
        )

        completed_applications = (
            db.query(ApplicationTask)
            .filter(
                ApplicationTask.created_at >= start_of_day,
                ApplicationTask.created_at < end_of_day,
                ApplicationTask.status == "completed",
            )
            .count()
        )

        metrics = {
            "date": today.isoformat(),
            "new_users": new_users,
            "new_jobs": new_jobs,
            "total_interactions": total_interactions,
            "total_applications": total_applications,
            "completed_applications": completed_applications,
            "completion_rate": (
                completed_applications / total_applications
                if total_applications > 0
                else 0
            ),
        }

        # Store in Redis with 30-day retention
        import redis

        r = redis.Redis(host="redis", port=6379, decode_responses=True)
        r.setex(f"analytics:daily:{today}", 30 * 24 * 3600, json.dumps(metrics))

        logger.info(f"Calculated daily metrics for {today}")
        return metrics

    except Exception as e:
        logger.error(f"Error calculating daily metrics: {e}")
        return {"error": str(e)}
    finally:
        db.close()


@celery_app.task
def aggregate_engagement_metrics(days: int = 7):
    """
    Aggregate engagement metrics over the past N days.

    Args:
        days: Number of days to aggregate

    Returns:
        Aggregated metrics
    """
    db = next(get_db())

    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # Get all interactions in the period
        interactions = (
            db.query(UserJobInteraction)
            .filter(
                UserJobInteraction.created_at >= start_date,
                UserJobInteraction.created_at < end_date,
            )
            .all()
        )

        # Calculate metrics
        action_counts = {}
        for interaction in interactions:
            action = interaction.action
            action_counts[action] = action_counts.get(action, 0) + 1

        # Get unique users
        unique_users = set(i.user_id for i in interactions)

        # Get daily breakdown
        daily_breakdown = {}
        for interaction in interactions:
            date_key = interaction.created_at.date().isoformat()
            if date_key not in daily_breakdown:
                daily_breakdown[date_key] = {"interactions": 0, "users": set()}
            daily_breakdown[date_key]["interactions"] += 1
            daily_breakdown[date_key]["users"].add(interaction.user_id)

        # Convert sets to counts
        for date_key in daily_breakdown:
            daily_breakdown[date_key]["users"] = len(daily_breakdown[date_key]["users"])

        metrics = {
            "period_days": days,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_interactions": len(interactions),
            "unique_users": len(unique_users),
            "action_breakdown": action_counts,
            "daily_breakdown": daily_breakdown,
            "avg_interactions_per_user": (
                len(interactions) / len(unique_users) if unique_users else 0
            ),
        }

        logger.info(f"Aggregated engagement metrics for {days} days")
        return metrics

    except Exception as e:
        logger.error(f"Error aggregating engagement metrics: {e}")
        return {"error": str(e)}
    finally:
        db.close()


@celery_app.task
def export_analytics_report(report_type: str = "daily", format: str = "json"):
    """
    Export analytics report to file.

    Args:
        report_type: Type of report (daily, weekly, monthly)
        format: Output format (json, csv)

    Returns:
        File path of exported report
    """
    import os

    try:
        if report_type == "daily":
            metrics = calculate_daily_metrics()
        elif report_type == "weekly":
            metrics = aggregate_engagement_metrics(days=7)
        elif report_type == "monthly":
            metrics = aggregate_engagement_metrics(days=30)
        else:
            raise ValueError(f"Unknown report type: {report_type}")

        # Generate file
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{report_type}_report_{timestamp}.{format}"
        file_path = f"/tmp/reports/{filename}"

        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        if format == "json":
            with open(file_path, "w") as f:
                json.dump(metrics, f, indent=2, default=str)
        elif format == "csv":
            import pandas as pd

            df = pd.DataFrame([metrics])
            df.to_csv(file_path, index=False)

        logger.info(f"Exported {report_type} report to {file_path}")
        return file_path

    except Exception as e:
        logger.error(f"Error exporting analytics report: {e}")
        return {"error": str(e)}


@celery_app.task
def calculate_user_engagement_scores():
    """
    Calculate engagement scores for all users.

    Returns:
        Number of users processed
    """
    db = next(get_db())
    processed = 0

    try:
        users = db.query(User).all()

        for user in users:
            # Calculate engagement score based on recent activity
            from datetime import timedelta

            week_ago = datetime.utcnow() - timedelta(days=7)

            interactions = (
                db.query(UserJobInteraction)
                .filter(
                    UserJobInteraction.user_id == user.id,
                    UserJobInteraction.created_at >= week_ago,
                )
                .count()
            )

            applications = (
                db.query(ApplicationTask)
                .filter(
                    ApplicationTask.user_id == user.id,
                    ApplicationTask.created_at >= week_ago,
                )
                .count()
            )

            # Simple engagement score calculation
            engagement_score = (interactions * 1 + applications * 5) / 10

            # Store score in user metadata (in a real app, this would be a separate field)
            if user.metadata:
                user.metadata["engagement_score"] = engagement_score
            else:
                user.metadata = {"engagement_score": engagement_score}

            processed += 1

        db.commit()
        logger.info(f"Calculated engagement scores for {processed} users")
        return processed

    except Exception as e:
        logger.error(f"Error calculating engagement scores: {e}")
        db.rollback()
        return 0
    finally:
        db.close()
