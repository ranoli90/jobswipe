"""
Job Ingestion Service with Real-time Processing

Provides job ingestion capabilities using Kafka for real-time job distribution.
Uses free, open-source job sources including RSS feeds and company career pages.
"""

import asyncio
import json
import logging
import os
import re
import time
from datetime import datetime
from typing import Dict, List

import aiohttp
import feedparser
from bs4 import BeautifulSoup

from backend.db.database import get_db
from backend.db.models import Job
from backend.services.matching import calculate_job_score
from backend.services.openai_service import OpenAIService

logger = logging.getLogger(__name__)

# Configuration
KAFKA_BROKER_URL = os.getenv("KAFKA_BROKER_URL", "localhost:9092")
KAFKA_JOB_TOPIC = os.getenv("KAFKA_JOB_TOPIC", "job_ingestion")
KAFKA_CONSUMER_GROUP = os.getenv("KAFKA_CONSUMER_GROUP", "job_processor_group")

# Free, open-source job sources configuration
JOB_SOURCES = {
    "rss_indeed": {
        "type": "rss",
        "url": "https://rss.indeed.com/rss?q=software+engineer&l=remote&sort=date",
        "category": "software",
    },
    "rss_linkedin": {
        "type": "rss",
        "url": "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=Software%20Engineer&location=Remote&geoId=92000000&trk=public_jobs_rss&start=0",
        "category": "software",
    },
    "rss_github": {
        "type": "rss",
        "url": "https://github.com/jobs/feed?l=Remote&q=software+engineer",
        "category": "software",
    },
    "rss_stackoverflow": {
        "type": "rss",
        "url": "https://stackoverflow.com/jobs/feed?r=Remote&q=software-engineer",
        "category": "software",
    },
    "rss_weworkremotely": {
        "type": "rss",
        "url": "https://weworkremotely.com/categories/remote-programming-jobs.rss",
        "category": "software",
    },
    "rss_remoteok": {
        "type": "rss",
        "url": "https://remoteok.com/remote-jobs.rss",
        "category": "all",
    },
    "company_careers": {
        "type": "scrape",
        "companies": [
            {
                "name": "airbnb",
                "url": "https://careers.airbnb.com/positions/",
                "job_selector": "a[href*='/positions/']",
            },
            {
                "name": "uber",
                "url": "https://www.uber.com/us/en/careers/list/",
                "job_selector": "a[href*='/careers/']",
            },
            {
                "name": "stripe",
                "url": "https://stripe.com/jobs",
                "job_selector": "a[href*='/jobs/']",
            },
            {
                "name": "spotify",
                "url": "https://www.lifeatspotify.com/jobs",
                "job_selector": "a[href*='/jobs/']",
            },
            {
                "name": "github",
                "url": "https://github.com/about/careers",
                "job_selector": "a[href*='/careers/']",
            },
            {
                "name": "slack",
                "url": "https://slack.com/careers",
                "job_selector": "a[href*='/careers/']",
            },
            {
                "name": "dropbox",
                "url": "https://www.dropbox.com/jobs",
                "job_selector": "a[href*='/jobs/']",
            },
        ],
    },
}

# Job types to include
JOB_TYPES = ["Software Engineer", "Data Scientist", "Product Manager", "Designer"]
MAX_JOB_POSTINGS_PER_SOURCE = 100


class JobIngestionService:
    """Service for job ingestion and real-time processing"""

    # Job sources configuration - free, open-source alternatives
    JOB_SOURCES = {
        "rss_indeed": {
            "type": "rss",
            "url": "https://rss.indeed.com/rss?q=software+engineer&l=remote&sort=date",
            "category": "software",
        },
        "rss_linkedin": {
            "type": "rss",
            "url": "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=Software%20Engineer&location=Remote&geoId=92000000&trk=public_jobs_rss&start=0",
            "category": "software",
        },
        "rss_github": {
            "type": "rss",
            "url": "https://github.com/jobs/feed?l=Remote&q=software+engineer",
            "category": "software",
        },
        "rss_stackoverflow": {
            "type": "rss",
            "url": "https://stackoverflow.com/jobs/feed?r=Remote&q=software-engineer",
            "category": "software",
        },
        "rss_weworkremotely": {
            "type": "rss",
            "url": "https://weworkremotely.com/categories/remote-programming-jobs.rss",
            "category": "software",
        },
        "rss_remoteok": {
            "type": "rss",
            "url": "https://remoteok.com/remote-jobs.rss",
            "category": "all",
        },
        "company_careers": {
            "type": "scrape",
            "companies": [
                {
                    "name": "airbnb",
                    "url": "https://careers.airbnb.com/positions/",
                    "job_selector": "a[href*='/positions/']",
                },
                {
                    "name": "uber",
                    "url": "https://www.uber.com/us/en/careers/list/",
                    "job_selector": "a[href*='/careers/']",
                },
                {
                    "name": "stripe",
                    "url": "https://stripe.com/jobs",
                    "job_selector": "a[href*='/jobs/']",
                },
                {
                    "name": "spotify",
                    "url": "https://www.lifeatspotify.com/jobs",
                    "job_selector": "a[href*='/jobs/']",
                },
                {
                    "name": "github",
                    "url": "https://github.com/about/careers",
                    "job_selector": "a[href*='/careers/']",
                },
                {
                    "name": "slack",
                    "url": "https://slack.com/careers",
                    "job_selector": "a[href*='/careers/']",
                },
                {
                    "name": "dropbox",
                    "url": "https://www.dropbox.com/jobs",
                    "job_selector": "a[href*='/jobs/']",
                },
            ],
        },
    }

    def __init__(self, openai_service=None):
        if openai_service is None:
            self.openai_service = OpenAIService()
        else:
            self.openai_service = openai_service
        self.kafka_producer = None
        self.kafka_consumer = None

    def init_kafka(self):
        """Initialize Kafka producer and consumer"""
        try:
            from kafka import KafkaConsumer, KafkaProducer

            # Producer
            self.kafka_producer = KafkaProducer(
                bootstrap_servers=KAFKA_BROKER_URL,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            )

            # Consumer
            self.kafka_consumer = KafkaConsumer(
                KAFKA_JOB_TOPIC,
                bootstrap_servers=KAFKA_BROKER_URL,
                group_id=KAFKA_CONSUMER_GROUP,
                value_deserializer=lambda x: json.loads(x.decode("utf-8")),
                auto_offset_reset="earliest",
            )

            logger.info("Kafka connection initialized successfully")

        except Exception as e:
            logger.warning(f"Failed to initialize Kafka connection: {e}")
            logger.warning("Falling back to direct database ingestion")

    async def ingest_jobs_from_sources(self) -> List[Dict]:
        """Ingest jobs from all configured sources"""
        all_jobs = []

        for source, config in self.JOB_SOURCES.items():
            logger.info(f"Ingesting jobs from {source}")

            try:
                if config["type"] == "rss":
                    jobs = await self.ingest_rss_feed(config)
                elif config["type"] == "scrape":
                    jobs = await self.ingest_scraped_jobs(config)
                else:
                    logger.warning(f"Unknown job source type: {config['type']}")
                    continue

                all_jobs.extend(jobs)
                logger.info(f"Ingested {len(jobs)} jobs from {source}")

            except Exception as e:
                logger.error(f"Error ingesting jobs from {source}: {e}")

        return all_jobs

    async def ingest_rss_feed(self, config: Dict) -> List[Dict]:
        """Ingest jobs from RSS feed"""
        jobs = []

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    config["url"], timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    response.raise_for_status()
                    content = await response.text()

                    # Parse RSS feed
                    feed = feedparser.parse(content)

                    for entry in feed.entries:
                        try:
                            # Check if job title contains any of the desired job types
                            if any(
                                job_type.lower() in entry.title.lower()
                                for job_type in JOB_TYPES
                            ):
                                # Extract job details
                                job = {
                                    "id": (
                                        entry.id
                                        if hasattr(entry, "id")
                                        else hash(entry.link)
                                    ),
                                    "title": entry.title,
                                    "company": self.extract_company_from_rss(entry),
                                    "location": self.extract_location_from_rss(entry),
                                    "description": self.extract_description_from_rss(
                                        entry
                                    ),
                                    "url": entry.link,
                                    "source": config.get("category", "rss"),
                                    "salary_range": self.extract_salary_from_rss(entry),
                                    "type": config.get("category", "software"),
                                    "created_at": (
                                        entry.published
                                        if hasattr(entry, "published")
                                        else datetime.now().isoformat()
                                    ),
                                }

                                jobs.append(job)

                        except Exception as e:
                            logger.error(f"Error parsing RSS entry: {e}")

        except Exception as e:
            logger.error(f"Error ingesting RSS feed {config['url']}: {e}")

        return jobs[:MAX_JOB_POSTINGS_PER_SOURCE]

    async def ingest_scraped_jobs(self, config: Dict) -> List[Dict]:
        """Ingest jobs from company career pages using scraping"""
        jobs = []

        for company_config in config["companies"]:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        company_config["url"], timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        response.raise_for_status()
                        content = await response.text()

                        # Parse HTML content
                        soup = BeautifulSoup(content, "html.parser")

                        # Find job links
                        job_links = soup.select(company_config["job_selector"])

                        for link in job_links:
                            try:
                                job_url = link.get("href")
                                # Make relative URLs absolute
                                if not job_url.startswith("http"):
                                    job_url = (
                                        f"{company_config['url'].rstrip('/')}{job_url}"
                                    )

                                # Extract job title from link text or attribute
                                job_title = link.get_text(strip=True)

                                # Check if job title contains any of the desired job types
                                if any(
                                    job_type.lower() in job_title.lower()
                                    for job_type in JOB_TYPES
                                ):
                                    job = {
                                        "id": hash(job_url),
                                        "title": job_title,
                                        "company": company_config["name"],
                                        "location": "Remote",  # Default to remote for tech companies
                                        "description": "",  # Will be fetched from job detail page
                                        "url": job_url,
                                        "source": "scraped",
                                        "salary_range": "",
                                        "type": "software",
                                        "created_at": datetime.now().isoformat(),
                                    }

                                    jobs.append(job)

                            except Exception as e:
                                logger.error(f"Error parsing job link: {e}")

            except Exception as e:
                logger.error(f"Error scraping {company_config['name']} jobs: {e}")

        return jobs[:MAX_JOB_POSTINGS_PER_SOURCE]

    def extract_company_from_rss(self, entry):
        """Extract company name from RSS entry"""
        # Try to extract company from various RSS feed formats
        if hasattr(entry, "source") and hasattr(entry.source, "title"):
            return entry.source.title

        # Extract from title or link
        if hasattr(entry, "link"):
            # Try to extract from domain
            try:
                from urllib.parse import urlparse

                domain = urlparse(entry.link).netloc
                return domain.split(".")[-2]  # Get second-level domain
            except Exception:
                pass

        return "Unknown"

    def extract_location_from_rss(self, entry):
        """Extract location from RSS entry"""
        # Try to extract location from summary or title
        if hasattr(entry, "summary"):
            # Common location patterns
            location_patterns = [
                r"Location[:\s]*([\w\s,]+)",
                r"Remote",
                r"New York",
                r"San Francisco",
                r"London",
            ]

            for pattern in location_patterns:
                match = re.search(pattern, entry.summary, re.IGNORECASE)
                if match:
                    return match.group(1) if len(match.groups()) > 0 else pattern

        return "Remote"

    def extract_description_from_rss(self, entry):
        """Extract job description from RSS entry"""
        if hasattr(entry, "summary"):
            return entry.summary

        return "No description available"

    def extract_salary_from_rss(self, entry):
        """Extract salary range from RSS entry"""
        if hasattr(entry, "summary"):
            # Common salary patterns
            salary_patterns = [
                r"\$(\d{4,5})-?\$?(\d{4,5})",
                r"(\d{4,5})-(\d{4,5})",
                r"\$(\d{4,5})\+",
            ]

            for pattern in salary_patterns:
                match = re.search(pattern, entry.summary)
                if match:
                    if match.group(2):
                        return f"${match.group(1)} - ${match.group(2)}"
                    return f"${match.group(1)}+"

        return ""

    async def process_job(self, job_data: Dict):
        """Process and store job data in database"""
        db = next(get_db())

        try:
            # Check if job already exists
            existing_job = (
                db.query(Job)
                .filter(
                    Job.external_id == job_data["id"], Job.source == job_data["source"]
                )
                .first()
            )

            if existing_job:
                # Update existing job
                existing_job.title = job_data["title"]
                existing_job.company = job_data["company"]
                existing_job.location = job_data["location"]
                existing_job.description = job_data["description"]
                existing_job.apply_url = job_data["url"]
                existing_job.salary_range = job_data.get("salary_range", "")
                existing_job.type = job_data.get("type", "")
                existing_job.updated_at = datetime.now()
                db.commit()
                logger.info(f"Updated job: {job_data['title']}")

            else:
                # Create new job
                new_job = Job(
                    external_id=job_data["id"],
                    title=job_data["title"],
                    company=job_data["company"],
                    location=job_data["location"],
                    description=job_data["description"],
                    apply_url=job_data["url"],
                    source=job_data["source"],
                    salary_range=job_data.get("salary_range", ""),
                    type=job_data.get("type", ""),
                    created_at=datetime.now(),
                )

                db.add(new_job)
                db.commit()
                logger.info(f"Created new job: {job_data['title']}")

            return True

        except Exception as e:
            logger.error(f"Error processing job: {e}")
            db.rollback()
            return False

        finally:
            db.close()

    async def process_jobs_batch(self, jobs: List[Dict]):
        """Process a batch of jobs"""
        success_count = 0
        failed_count = 0

        for job in jobs:
            try:
                # Check if job meets quality standards
                if len(job.get("description", "")) < 500:
                    logger.warning(f"Job description too short: {job['title']}")
                    continue

                if self.kafka_producer:
                    # Send to Kafka for real-time processing
                    self.kafka_producer.send(KAFKA_JOB_TOPIC, job)
                    logger.debug(f"Sent job to Kafka: {job['title']}")
                else:
                    # Process directly if Kafka not available
                    await self.process_job(job)

                success_count += 1

            except Exception as e:
                logger.error(
                    f"Failed to process job {job.get('title', 'Unknown')}: {e}"
                )
                failed_count += 1

        logger.info(
            f"Batch processed: {success_count} succeeded, {failed_count} failed"
        )
        return success_count, failed_count

    async def kafka_consumer_loop(self):
        """Consumer loop to process jobs from Kafka"""
        if not self.kafka_consumer:
            logger.warning("Kafka consumer not available, skipping consumer loop")
            return

        logger.info("Started Kafka consumer loop")

        try:
            for msg in self.kafka_consumer:
                try:
                    job_data = msg.value
                    logger.info(f"Processing job from Kafka: {job_data['title']}")

                    await self.process_job(job_data)

                except Exception as e:
                    logger.error(f"Error processing Kafka message: {e}")

        except Exception as e:
            logger.error(f"Kafka consumer error: {e}")

        finally:
            self.kafka_consumer.close()

    async def run_periodic_ingestion(self, interval_seconds: int = 3600):
        """Run periodic job ingestion at specified interval"""
        self.init_kafka()

        logger.info(
            f"Starting periodic job ingestion with interval: {interval_seconds} seconds"
        )

        while True:
            try:
                # Ingest jobs from all sources
                jobs = await self.ingest_jobs_from_sources()

                if jobs:
                    logger.info(f"Ingested {len(jobs)} jobs for processing")
                    await self.process_jobs_batch(jobs)
                else:
                    logger.info("No new jobs to ingest")

                logger.info(f"Next ingestion in {interval_seconds} seconds")
                await asyncio.sleep(interval_seconds)

            except Exception as e:
                logger.error(f"Periodic ingestion error: {e}")
                await asyncio.sleep(60)  # Wait before retrying

    async def run_once(self):
        """Run ingestion once"""
        self.init_kafka()

        logger.info("Running job ingestion once")

        try:
            jobs = await self.ingest_jobs_from_sources()

            if jobs:
                logger.info(f"Ingested {len(jobs)} jobs")
                success, failed = await self.process_jobs_batch(jobs)
                logger.info(
                    f"Processing complete: {success} succeeded, {failed} failed"
                )
            else:
                logger.info("No new jobs to ingest")

            return jobs

        except Exception as e:
            logger.error(f"Single ingestion run error: {e}")
            return []


# Singleton instance
job_ingestion_service = JobIngestionService()


# Helper functions
async def ingest_jobs_once() -> List[Dict]:
    """Convenience function to run ingestion once"""
    return await job_ingestion_service.run_once()


async def start_periodic_ingestion(interval_seconds: int = 3600):
    """Convenience function to start periodic ingestion"""
    await job_ingestion_service.run_periodic_ingestion(interval_seconds)
