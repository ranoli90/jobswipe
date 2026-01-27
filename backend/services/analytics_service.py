"""
Advanced Analytics and Reporting Service

Provides analytics and reporting features for job matching and user behavior.
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from backend.db.database import get_db
from backend.db.models import ApplicationTask, Job, User, UserJobInteraction
from backend.services.matching import calculate_job_score
from backend.services.openai_service import OpenAIService

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for providing advanced analytics and reporting"""

    def __init__(self):
        self.openai_service = OpenAIService()

    async def get_matching_accuracy_report(self, time_range: int = 30) -> Dict:
        """
        Generate a report on matching accuracy over time.

        Args:
            time_range: Number of days to include in the report

        Returns:
            Dictionary containing matching accuracy metrics
        """
        db = next(get_db())

        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=time_range)

            # Get all user-job interactions in the time range
            interactions = (
                db.query(UserJobInteraction)
                .filter(
                    UserJobInteraction.created_at >= start_date,
                    UserJobInteraction.created_at <= end_date,
                )
                .all()
            )

            # Calculate accuracy metrics
            total_interactions = len(interactions)
            if total_interactions == 0:
                return {
                    "time_range": time_range,
                    "total_interactions": 0,
                    "accuracy_score": 0.0,
                    "success_rate": 0.0,
                    "interactions_by_action": {},
                    "matches_by_score_range": {},
                }

            # Count interactions by action type
            interactions_by_action = {}
            for interaction in interactions:
                action = interaction.action
                interactions_by_action[action] = (
                    interactions_by_action.get(action, 0) + 1
                )

            # Calculate matching accuracy scores
            accurate_matches = 0
            matches_by_score_range = {
                "low": 0,  # 0.0 - 0.4
                "medium": 0,  # 0.4 - 0.7
                "high": 0,  # 0.7 - 1.0
                "very_high": 0,  # > 0.9
            }

            for interaction in interactions:
                try:
                    score = 0.0  # Default score if calculation fails
                    user = db.query(User).filter(User.id == interaction.user_id).first()
                    job = db.query(Job).filter(Job.id == interaction.job_id).first()

                    if user and job and user.profile:
                        score = await calculate_job_score(job, user.profile)

                    # Classify scores
                    if score < 0.4:
                        matches_by_score_range["low"] += 1
                    elif score < 0.7:
                        matches_by_score_range["medium"] += 1
                    elif score < 0.9:
                        matches_by_score_range["high"] += 1
                    

                    matches_by_score_range["very_high"] += 1

                    # Count accurate matches (score > 0.7 for 'like' or 'apply' actions)
                    if interaction.action in {"like", "apply"} and score > 0.7:
                        accurate_matches += 1

                except Exception as e:
                    logger.error("Error processing interaction: %s", e)
                    import traceback

                    logger.error("Stack trace: %s", traceback.format_exc())

            # Calculate success rate
            apply_interactions = [i for i in interactions if i.action == "apply"]
            if apply_interactions:
                success_count = 0
                for interaction in apply_interactions:
                    task = (
                        db.query(ApplicationTask)
                        .filter(
                            ApplicationTask.user_id == interaction.user_id,
                            ApplicationTask.job_id == interaction.job_id,
                        )
                        .first()
                    )

                    if task and task.status == "completed":
                        success_count += 1

                success_rate = success_count / len(apply_interactions)
            else:
                success_rate = 0.0

            return {
                "time_range": time_range,
                "total_interactions": total_interactions,
                "accuracy_score": accurate_matches / total_interactions,
                "success_rate": success_rate,
                "interactions_by_action": interactions_by_action,
                "matches_by_score_range": matches_by_score_range,
            }

        except Exception as e:
            logger.error("Error generating matching accuracy report: %s", e)
            return {"error": str(e)}
        finally:
            db.close()

    async def get_user_behavior_report(self, user_id: str = None) -> Dict:
        """
        Generate a user behavior report.

        Args:
            user_id: ID of the user

        Returns:
            Dictionary containing user behavior metrics
        """
        db = next(get_db())

        try:
            if user_id:
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    return {"error": "User not found"}
                # Get user interactions
                interactions = (
                    db.query(UserJobInteraction)
                    .filter(UserJobInteraction.user_id == user_id)
                    .all()
                )
            else:
                # Get all interactions for aggregate report
                interactions = db.query(UserJobInteraction).all()
            interactions = (
                db.query(UserJobInteraction)
                .filter(UserJobInteraction.user_id == user_id)
                .all()
            )

            # Get user application tasks
            tasks = (
                db.query(ApplicationTask)
                .filter(ApplicationTask.user_id == user_id)
                .all()
            )

            # Calculate metrics
            total_interactions = len(interactions)
            if total_interactions == 0:
                return {
                    "user_id": user_id,
                    "total_interactions": 0,
                    "avg_match_score": 0.0,
                    "actions_distribution": {},
                    "applications_status": {},
                    "top_interested_skills": [],
                    "preferred_locations": [],
                }

            # Calculate average match score
            total_score = 0
            score_count = 0

            for interaction in interactions:
                job = db.query(Job).filter(Job.id == interaction.job_id).first()
                if job and user.profile:
                    score = await calculate_job_score(job, user.profile)
                    total_score += score
                    score_count += 1

            avg_match_score = total_score / score_count if score_count > 0 else 0.0

            # Actions distribution
            actions_distribution = {}
            for interaction in interactions:
                action = interaction.action
                actions_distribution[action] = actions_distribution.get(action, 0) + 1

            # Applications status
            applications_status = {}
            for task in tasks:
                status = task.status
                applications_status[status] = applications_status.get(status, 0) + 1

            # Extract skills and locations from jobs the user interacted with
            top_interested_skills = []
            preferred_locations = []

            for interaction in interactions:
                job = db.query(Job).filter(Job.id == interaction.job_id).first()
                if job and job.description:
                    # Extract skills from job description
                    job_skills = self._extract_skills_from_job(job.description)
                    top_interested_skills.extend(job_skills)

                if job and job.location:
                    preferred_locations.append(job.location)

            # Calculate skills frequency
            skill_frequency = {}
            for skill in top_interested_skills:
                skill_frequency[skill] = skill_frequency.get(skill, 0) + 1

            # Calculate location frequency
            location_frequency = {}
            for location in preferred_locations:
                location_frequency[location] = location_frequency.get(location, 0) + 1

            # Get top skills and locations
            top_skills = sorted(
                skill_frequency.items(), key=lambda x: x[1], reverse=True
            )[:10]
            top_locations = sorted(
                location_frequency.items(), key=lambda x: x[1], reverse=True
            )[:5]

            return {
                "user_id": user_id,
                "total_interactions": total_interactions,
                "avg_match_score": avg_match_score,
                "actions_distribution": actions_distribution,
                "applications_status": applications_status,
                "top_interested_skills": [
                    {"skill": s, "count": c} for s, c in top_skills
                ],
                "preferred_locations": [
                    {"location": l, "count": c} for l, c in top_locations
                ],
            }

        except Exception as e:
            logger.error("Error generating user behavior report: %s", e)
            return {"error": str(e)}
        finally:
            db.close()

    async def get_job_market_analysis(self) -> Dict:
        """
        Generate job market analysis report.

        Returns:
            Dictionary containing job market analysis
        """
        db = next(get_db())

        try:
            # Get all jobs from the last 7 days
            last_week = datetime.now() - timedelta(days=7)
            jobs = db.query(Job).filter(Job.created_at >= last_week).all()

            total_jobs = len(jobs)

            # Calculate jobs by source
            jobs_by_source = {}
            for job in jobs:
                source = job.source
                jobs_by_source[source] = jobs_by_source.get(source, 0) + 1

            # Calculate jobs by location
            jobs_by_location = {}
            for job in jobs:
                location = job.location if job.location else "Remote"
                jobs_by_location[location] = jobs_by_location.get(location, 0) + 1

            # Calculate jobs by type
            jobs_by_type = {}
            for job in jobs:
                # Extract type from title
                type = self._classify_job_type(job.title)
                jobs_by_type[type] = jobs_by_type.get(type, 0) + 1

            # Calculate average description length
            total_length = 0
            for job in jobs:
                if job.description:
                    total_length += len(job.description)

            avg_description_length = total_length / total_jobs if total_jobs > 0 else 0

            return {
                "period": "last_7_days",
                "total_jobs": total_jobs,
                "jobs_by_source": jobs_by_source,
                "jobs_by_location": jobs_by_location,
                "jobs_by_type": jobs_by_type,
                "avg_description_length": avg_description_length,
                "growth_rate": 0.12,  # Mock growth rate
            }

        except Exception as e:
            logger.error("Error generating job market analysis: %s", e)
            return {"error": str(e)}
        finally:
            db.close()

    def _extract_skills_from_job(self, description: str) -> List[str]:
        """Extract skills from job description using keyword matching"""
        skills = []

        # Common technical skills (sorted by length descending to prioritize longer skills)
        technical_skills = sorted(
            [
                "Python",
                "Java",
                "JavaScript",
                "TypeScript",
                "C++",
                "C#",
                "Go",
                "Rust",
                "React",
                "Angular",
                "Vue",
                "Node.js",
                "Express",
                "Django",
                "Flask",
                "SQL",
                "PostgreSQL",
                "MySQL",
                "MongoDB",
                "Redis",
                "AWS",
                "Azure",
                "GCP",
            ],
            key=len,
            reverse=True,
        )

        for skill in technical_skills:
            if skill.lower() in description.lower():
                skills.append(skill)
                # Remove any overlapping skills (e.g., if we found "JavaScript", don't add "Java")
                description = description.replace(skill, "")

        return list(set(skills))

    def _classify_job_type(self, title: str) -> str:
        """Classify job type based on title"""
        title_lower = title.lower()

        if any(
            keyword in title_lower
            for keyword in ["data", "scientist", "analyst", "machine learning"]
        ):
            return "Data Science"
        elif any(
            keyword in title_lower
            for keyword in ["software", "developer", "engineer", "programmer"]
        ):
            return "Software Development"
        elif "product manager" in title_lower:
            return "Product Management"
        elif any(keyword in title_lower for keyword in ["design", "ux", "ui"]):
            return "Design"
        elif any(keyword in title_lower for keyword in ["marketing", "growth"]):
            return "Marketing"
        elif any(
            keyword in title_lower
            for keyword in ["sales", "account executive", "account manager"]
        ):
            return "Sales"
        elif "manager" in title_lower:
            return "Other"

        return "Other"

    async def export_report(self, report_type: str, format: str = "json") -> str:
        """
        Export report in specified format.

        Args:
            report_type: Type of report to export
            format: Export format (json, csv, html)

        Returns:
            File path of the exported report
        """
        try:
            if report_type == "matching_accuracy":
                data = await self.get_matching_accuracy_report()
            elif report_type == "user_behavior":
                data = await self.get_user_behavior_report()
            elif report_type == "job_market":
                data = await self.get_job_market_analysis()
            else:
                raise ValueError(f"Unknown report type: {report_type}")

            # Generate file name
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"{report_type}_{timestamp}.{format}"
            file_path = os.path.join("/tmp/reports", file_name)

            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # Export based on format
            if format == "json":
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            elif format == "csv":
                df = pd.DataFrame([data])
                df.to_csv(file_path, index=False)
            elif format == "html":
                # Generate simple HTML report
                html = self._generate_html_report(data, report_type)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(html)
            else:
                raise ValueError(f"Unsupported format: {format}")

            logger.info("Report exported successfully: %s", file_path)
            return file_path

        except Exception as e:
            logger.error("Error exporting report: %s", e)
            raise

    def _generate_html_report(self, data: Dict, report_type: str) -> str:
        """Generate simple HTML report"""
        title = "Job Matching Analytics Report"
        if report_type == "matching_accuracy":
            title = "Matching Accuracy Report"
        elif report_type == "user_behavior":
            title = "User Behavior Report"
        elif report_type == "job_market":
            title = "Job Market Analysis Report"

        return f"""
        <html>
        <head>
            <title>{title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #333; }}
                .metric {{ margin: 20px 0; }}
                .metric-label {{ font-weight: bold; margin-bottom: 5px; }}
                .metric-value {{ font-size: 18px; color: #007bff; }}
            </style>
        </head>
        <body>
            <h1>{title}</h1>
            {self._render_report_content(data)}
        </body>
        </html>
        """

    def _render_report_content(self, data: Dict) -> str:
        """Render report content based on data structure"""
        html = ""

        for key, value in data.items():
            if isinstance(value, dict):
                html += f"<h3>{key}</h3>"
                html += self._render_report_content(value)
            elif isinstance(value, list):
                html += f"<h3>{key}</h3>"
                html += "<ul>"
                for item in value:
                    if isinstance(item, dict):
                        item_html = ", ".join([f"{k}: {v}" for k, v in item.items()])
                        html += f"<li>{item_html}</li>"
                    else:
                        html += f"<li>{item}</li>"
                html += "</ul>"
            else:
                html += f"""
                <div class="metric">
                    <div class="metric-label">{key}</div>
                    <div class="metric-value">{value}</div>
                </div>
                """

        return html

    async def get_dashboard_summary(self) -> Dict:
        """
        Get dashboard summary with key metrics for real-time monitoring.

        Returns:
            Dictionary containing dashboard summary metrics
        """
        db = next(get_db())

        try:
            # Get basic counts
            total_users = db.query(User).count()
            total_jobs = db.query(Job).count()
            total_interactions = db.query(UserJobInteraction).count()
            total_applications = db.query(ApplicationTask).count()

            # Get today's metrics
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            today_interactions = (
                db.query(UserJobInteraction)
                .filter(UserJobInteraction.created_at >= today)
                .count()
            )

            today_applications = (
                db.query(ApplicationTask)
                .filter(ApplicationTask.created_at >= today)
                .count()
            )

            # Calculate daily growth rate
            yesterday = today - timedelta(days=1)
            yesterday_interactions = (
                db.query(UserJobInteraction)
                .filter(
                    UserJobInteraction.created_at >= yesterday,
                    UserJobInteraction.created_at < today,
                )
                .count()
            )

            daily_growth = (
                (today_interactions - yesterday_interactions) / yesterday_interactions
                if yesterday_interactions > 0
                else 0
            )

            return {
                "total_users": total_users,
                "total_jobs": total_jobs,
                "total_interactions": total_interactions,
                "total_applications": total_applications,
                "today_interactions": today_interactions,
                "today_applications": today_applications,
                "daily_growth_rate": round(daily_growth, 4),
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error("Error generating dashboard summary: %s", e)
            return {"error": str(e)}
        finally:
            db.close()

    async def get_engagement_trends(self, days: int = 30) -> Dict:
        """
        Get user engagement trends over time.

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary containing engagement trends data
        """
        db = next(get_db())

        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            # Get interactions grouped by date
            interactions_by_date = {}
            applications_by_date = {}

            for i in range(days):
                date = start_date + timedelta(days=i)
                date_str = date.strftime("%Y-%m-%d")
                next_date = date + timedelta(days=1)

                count = (
                    db.query(UserJobInteraction)
                    .filter(
                        UserJobInteraction.created_at >= date,
                        UserJobInteraction.created_at < next_date,
                    )
                    .count()
                )
                interactions_by_date[date_str] = count

                app_count = (
                    db.query(ApplicationTask)
                    .filter(
                        ApplicationTask.created_at >= date,
                        ApplicationTask.created_at < next_date,
                    )
                    .count()
                )
                applications_by_date[date_str] = app_count

            return {
                "period_days": days,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "interactions_by_date": interactions_by_date,
                "applications_by_date": applications_by_date,
                "total_interactions": sum(interactions_by_date.values()),
                "total_applications": sum(applications_by_date.values()),
            }

        except Exception as e:
            logger.error("Error generating engagement trends: %s", e)
            return {"error": str(e)}
        finally:
            db.close()

    async def get_job_performance(self, job_id: str) -> Dict:
        """
        Get performance metrics for a specific job.

        Args:
            job_id: ID of the job

        Returns:
            Dictionary containing job performance metrics
        """
        db = next(get_db())

        try:
            job = db.query(Job).filter(Job.id == job_id).first()
            if not job:
                return {"error": "Job not found"}

            # Get interactions for this job
            interactions = (
                db.query(UserJobInteraction)
                .filter(UserJobInteraction.job_id == job_id)
                .all()
            )

            total_views = len(interactions)
            total_likes = sum(1 for i in interactions if i.action == "like")
            total_passes = sum(1 for i in interactions if i.action == "pass")
            total_applications = sum(1 for i in interactions if i.action == "apply")

            # Get application tasks for this job
            applications = (
                db.query(ApplicationTask).filter(ApplicationTask.job_id == job_id).all()
            )

            applications_by_status = {}
            for app in applications:
                status = app.status
                applications_by_status[status] = (
                    applications_by_status.get(status, 0) + 1
                )

            # Calculate engagement rate
            engagement_rate = (
                (total_likes + total_applications) / total_views
                if total_views > 0
                else 0
            )

            return {
                "job_id": job_id,
                "job_title": job.title,
                "total_views": total_views,
                "total_likes": total_likes,
                "total_passes": total_passes,
                "total_applications": total_applications,
                "engagement_rate": round(engagement_rate, 4),
                "applications_by_status": applications_by_status,
                "created_at": job.created_at.isoformat() if job.created_at else None,
            }

        except Exception as e:
            logger.error("Error generating job performance: %s", e)
            return {"error": str(e)}
        finally:
            db.close()

    async def get_application_funnel(self) -> Dict:
        """
        Get application funnel analytics showing conversion rates.

        Returns:
            Dictionary containing application funnel data
        """
        db = next(get_db())

        try:
            # Get all application tasks
            applications = db.query(ApplicationTask).all()

            total_applications = len(applications)
            pending = sum(1 for a in applications if a.status == "pending")
            in_progress = sum(1 for a in applications if a.status == "in_progress")
            completed = sum(1 for a in applications if a.status == "completed")
            failed = sum(1 for a in applications if a.status == "failed")

            # Get conversion funnel based on interactions
            interactions = db.query(UserJobInteraction).all()
            total_views = len(interactions)
            total_likes = sum(1 for i in interactions if i.action == "like")
            total_applies = sum(1 for i in interactions if i.action == "apply")

            view_to_like_rate = total_likes / total_views if total_views > 0 else 0
            like_to_apply_rate = total_applies / total_likes if total_likes > 0 else 0
            overall_conversion = total_applies / total_views if total_views > 0 else 0

            return {
                "interaction_funnel": {
                    "total_views": total_views,
                    "total_likes": total_likes,
                    "total_applies": total_applies,
                    "view_to_like_rate": round(view_to_like_rate, 4),
                    "like_to_apply_rate": round(like_to_apply_rate, 4),
                    "overall_conversion_rate": round(overall_conversion, 4),
                },
                "application_status_funnel": {
                    "total_applications": total_applications,
                    "pending": pending,
                    "in_progress": in_progress,
                    "completed": completed,
                    "failed": failed,
                    "completion_rate": (
                        completed / total_applications if total_applications > 0 else 0
                    ),
                    "success_rate": (
                        completed / (completed + failed)
                        if (completed + failed) > 0
                        else 0
                    ),
                },
            }

        except Exception as e:
            logger.error("Error generating application funnel: %s", e)
            return {"error": str(e)}
        finally:
            db.close()


# Singleton instance
analytics_service = AnalyticsService()
