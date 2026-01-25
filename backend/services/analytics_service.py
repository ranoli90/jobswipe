"""
Advanced Analytics and Reporting Service

Provides analytics and reporting features for job matching and user behavior.
"""

import os
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json
import pandas as pd
import numpy as np

from backend.db.database import get_db
from backend.db.models import User, Job, UserJobInteraction, ApplicationTask
from backend.services.openai_service import OpenAIService
from backend.services.matching import calculate_job_score

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
            interactions = db.query(UserJobInteraction).filter(
                UserJobInteraction.created_at >= start_date,
                UserJobInteraction.created_at <= end_date
            ).all()
            
            # Calculate accuracy metrics
            total_interactions = len(interactions)
            if total_interactions == 0:
                return {
                    "time_range": time_range,
                    "total_interactions": 0,
                    "accuracy_score": 0.0,
                    "success_rate": 0.0,
                    "interactions_by_action": {},
                    "matches_by_score_range": {}
                }
                
            # Count interactions by action type
            interactions_by_action = {}
            for interaction in interactions:
                action = interaction.action
                interactions_by_action[action] = interactions_by_action.get(action, 0) + 1
                
            # Calculate matching accuracy scores
            accurate_matches = 0
            matches_by_score_range = {
                "low": 0,    # 0.0 - 0.4
                "medium": 0, # 0.4 - 0.7
                "high": 0,   # 0.7 - 1.0
                "very_high": 0 # > 0.9
            }
            
            for interaction in interactions:
                try:
                    user = db.query(User).filter(User.id == interaction.user_id).first()
                    job = db.query(Job).filter(Job.id == interaction.job_id).first()
                    
                    if user and job and user.profile:
                        score = await calculate_job_score(job, user.profile)
                except Exception as e:
                    logger.error(f"Error processing interaction: {e}")
                    import traceback
                    logger.error(f"Stack trace: {traceback.format_exc()}")
                    
                    # Classify scores
                    if score < 0.4:
                        matches_by_score_range["low"] += 1
                    elif score < 0.7:
                        matches_by_score_range["medium"] += 1
                    elif score < 0.9:
                        matches_by_score_range["high"] += 1
                    else:
                        matches_by_score_range["very_high"] += 1
                        
                    # Count accurate matches (score > 0.7 for 'like' or 'apply' actions)
                    if interaction.action in ["like", "apply"] and score > 0.7:
                        accurate_matches += 1
                        
            # Calculate success rate
            apply_interactions = [i for i in interactions if i.action == "apply"]
            if apply_interactions:
                success_count = 0
                for interaction in apply_interactions:
                    task = db.query(ApplicationTask).filter(
                        ApplicationTask.user_id == interaction.user_id,
                        ApplicationTask.job_id == interaction.job_id
                    ).first()
                    
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
                "matches_by_score_range": matches_by_score_range
            }
            
        except Exception as e:
            logger.error(f"Error generating matching accuracy report: {e}")
            return {
                "error": str(e)
            }
        finally:
            db.close()
            
    async def get_user_behavior_report(self, user_id: str) -> Dict:
        """
        Generate a user behavior report.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Dictionary containing user behavior metrics
        """
        db = next(get_db())
        
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"error": "User not found"}
                
            # Get all user interactions
            interactions = db.query(UserJobInteraction).filter(
                UserJobInteraction.user_id == user_id
            ).all()
            
            # Get user application tasks
            tasks = db.query(ApplicationTask).filter(
                ApplicationTask.user_id == user_id
            ).all()
            
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
                    "preferred_locations": []
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
            top_skills = sorted(skill_frequency.items(), key=lambda x: x[1], reverse=True)[:10]
            top_locations = sorted(location_frequency.items(), key=lambda x: x[1], reverse=True)[:5]
            
            return {
                "user_id": user_id,
                "total_interactions": total_interactions,
                "avg_match_score": avg_match_score,
                "actions_distribution": actions_distribution,
                "applications_status": applications_status,
                "top_interested_skills": [{"skill": s, "count": c} for s, c in top_skills],
                "preferred_locations": [{"location": l, "count": c} for l, c in top_locations]
            }
            
        except Exception as e:
            logger.error(f"Error generating user behavior report: {e}")
            return {
                "error": str(e)
            }
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
            jobs = db.query(Job).filter(
                Job.created_at >= last_week
            ).all()
            
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
                "growth_rate": 0.12  # Mock growth rate
            }
            
        except Exception as e:
            logger.error(f"Error generating job market analysis: {e}")
            return {
                "error": str(e)
            }
        finally:
            db.close()
            
    def _extract_skills_from_job(self, description: str) -> List[str]:
        """Extract skills from job description using keyword matching"""
        skills = []
        
        # Common technical skills (sorted by length descending to prioritize longer skills)
        technical_skills = sorted([
            "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "Go", "Rust",
            "React", "Angular", "Vue", "Node.js", "Express", "Django", "Flask",
            "SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis", "AWS", "Azure", "GCP"
        ], key=len, reverse=True)
        
        for skill in technical_skills:
            if skill.lower() in description.lower():
                skills.append(skill)
                # Remove any overlapping skills (e.g., if we found "JavaScript", don't add "Java")
                description = description.replace(skill, "")
                
        return list(set(skills))
        
    def _classify_job_type(self, title: str) -> str:
        """Classify job type based on title"""
        title_lower = title.lower()
        
        if any(keyword in title_lower for keyword in ["data", "scientist", "analyst", "machine learning"]):
            return "Data Science"
        elif any(keyword in title_lower for keyword in ["software", "developer", "engineer", "programmer"]):
            return "Software Development"
        elif "product manager" in title_lower:
            return "Product Management"
        elif any(keyword in title_lower for keyword in ["design", "ux", "ui"]):
            return "Design"
        elif any(keyword in title_lower for keyword in ["marketing", "growth"]):
            return "Marketing"
        elif any(keyword in title_lower for keyword in ["sales", "account executive", "account manager"]):
            return "Sales"
        elif "manager" in title_lower:
            return "Other"
        else:
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
                
            logger.info(f"Report exported successfully: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Error exporting report: {e}")
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
        
# Singleton instance
analytics_service = AnalyticsService()
