"""
Application Automation Service

Handles automated job applications and resume submissions.
"""

import asyncio
import logging
import os
import random
import string
from datetime import datetime
from typing import Dict, List, Optional

from playwright.async_api import async_playwright

from backend.db.database import get_db
from backend.db.models import ApplicationTask, CandidateProfile, Job, User
from backend.services.captcha_detector import (CaptchaDetector,
                                               HumanInTheLoopSystem)
from backend.services.domain_service import domain_service
from backend.services.resume_parser_enhanced import parse_resume_enhanced

logger = logging.getLogger(__name__)


class ApplicationAutomationService:
    """Service for automated job applications"""

    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.captcha_detector = CaptchaDetector()
        self.hitl_system = HumanInTheLoopSystem()

    async def initialize_browser(self):
        """Initialize Playwright browser instance"""
        try:
            logger.info("Initializing Playwright browser")

            if not self.browser:
                self.playwright = await async_playwright().start()
                self.browser = await self.playwright.chromium.launch(
                    headless=os.getenv("HEADLESS", "true").lower() == "true",
                    args=["--no-sandbox", "--disable-setuid-sandbox"],
                )

            if not self.context:
                self.context = await self.browser.new_context()

            if not self.page:
                self.page = await self.context.new_page()

            logger.info("Playwright browser initialized successfully")

        except Exception as e:
            logger.error("Failed to initialize browser: %s", e)
            raise

    async def close_browser(self):
        """Close browser and Playwright instance"""
        try:
            if self.page:
                await self.page.close()
                self.page = None

            if self.context:
                await self.context.close()
                self.context = None

            if self.browser:
                await self.browser.close()
                self.browser = None

            if self.playwright:
                await self.playwright.stop()
                self.playwright = None

            logger.info("Playwright browser closed")

        except Exception as e:
            logger.error("Failed to close browser: %s", e)

    async def fill_form_field(self, selector: str, value: str):
        """Fill form field with value"""
        try:
            await self.page.wait_for_selector(selector, timeout=10000)
            await self.page.fill(selector, value)
            await self.page.wait_for_timeout(500)  # Add human-like delay
            logger.debug("Filled field %s with value: %s", selector, value)

        except Exception as e:
            logger.warning("Failed to fill field %s: %s", selector, e)

    async def click_element(self, selector: str):
        """Click on an element"""
        try:
            await self.page.wait_for_selector(selector, timeout=10000)
            await self.page.click(selector)
            await self.page.wait_for_timeout(500)
            logger.debug("Clicked element: %s", selector)

        except Exception as e:
            logger.warning("Failed to click element %s: %s", selector, e)

    async def check_for_captcha(self) -> Optional[Dict]:
        """Check if page contains CAPTCHA

        Returns:
            Dict with CAPTCHA details if detected, None otherwise
        """
        try:
            # Take screenshot for CAPTCHA detection
            screenshot = await self.page.screenshot()

            # Use CAPTCHA detector to analyze
            captcha_details = self.captcha_detector.detect_captcha(screenshot)

            if captcha_details:
                logger.warning("CAPTCHA detected: %s", captcha_details)

                # Queue for human resolution if automated solving fails
                captcha_details["screenshot"] = screenshot

                # If human resolution is enabled
                if self.captcha_detector.enable_human_resolution:
                    captcha_details["human_task_id"] = self.hitl_system.queue_task(
                        "captcha_solving",
                        {
                            "screenshot": (
                                screenshot.decode("utf-8")
                                if isinstance(screenshot, bytes)
                                else screenshot
                            ),
                            "url": self.page.url,
                            "timestamp": datetime.now().isoformat(),
                        },
                    )

                return captcha_details

            return None

        except Exception as e:
            logger.error("Error checking for CAPTCHA: %s", e)
            return None

    async def solve_captcha(self, captcha_details: Dict) -> Optional[Dict]:
        """Attempt to solve detected CAPTCHA

        Args:
            captcha_details: Details from CAPTCHA detection

        Returns:
            Dict with solution if successful, None otherwise
        """
        try:
            # First, try automated solving
            solution = self.captcha_detector.solve_captcha(
                captcha_details["screenshot"], self.page.url
            )

            if solution and solution.get("status") == "solved":
                logger.info("CAPTCHA solved successfully")
                return solution

            # If automated solving fails and human resolution is enabled
            if "human_task_id" in captcha_details:
                logger.info("Waiting for human CAPTCHA resolution")
                return {
                    "status": "waiting_human",
                    "task_id": captcha_details["human_task_id"],
                }

            return None

        except Exception as e:
            logger.error("Error solving CAPTCHA: %s", e)
            return None

    async def select_dropdown(self, selector: str, value: str):
        """Select dropdown option"""
        try:
            await self.page.wait_for_selector(selector, timeout=10000)
            await self.page.select_option(selector, value)
            await self.page.wait_for_timeout(500)
            logger.debug("Selected %s from %s", value, selector)

        except Exception as e:
            logger.warning("Failed to select dropdown %s: %s", selector, e)

    async def fill_checkboxes(self, selectors: List[str]):
        """Fill multiple checkboxes"""
        for selector in selectors:
            try:
                await self.page.wait_for_selector(selector, timeout=5000)
                is_checked = await self.page.is_checked(selector)
                if not is_checked:
                    await self.page.check(selector)
                logger.debug("Handled checkbox: %s", selector)

            except Exception as e:
                logger.warning("Failed to handle checkbox %s: %s", selector, e)

    async def upload_file(self, selector: str, file_path: str):
        """Upload file using file input"""
        try:
            await self.page.wait_for_selector(selector, timeout=10000)
            await self.page.set_input_files(selector, file_path)
            await self.page.wait_for_timeout(1000)
            logger.debug("Uploaded file: %s", file_path)

        except Exception as e:
            logger.warning("Failed to upload file %s: %s", file_path, e)

    async def submit_form(self, selector: str = "button[type='submit']"):
        """Submit form by clicking submit button"""
        try:
            await self.page.wait_for_selector(selector, timeout=10000)
            await self.page.click(selector)
            logger.debug("Form submitted")

        except Exception as e:
            logger.warning("Failed to submit form: %s", e)

    async def handle_common_elements(self):
        """Handle common form elements"""
        try:
            # Handle cookie consent
            cookie_selectors = [
                "button[id*='cookie']",
                "button[class*='cookie']",
                "button[text*='Accept']",
                "button[text*='Consent']",
            ]

            for selector in cookie_selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=3000)
                    await self.page.click(selector)
                    logger.debug("Cookie consent accepted")
                except Exception:
                    continue

            # Handle popup modals
            modal_selectors = [
                "button[class*='close']",
                "button[class*='modal']",
                "button[text*='Close']",
            ]

            for selector in modal_selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=2000)
                    await self.page.click(selector)
                    logger.debug("Popup modal closed")
                except Exception:
                    continue

        except Exception as e:
            logger.warning("Failed to handle common elements: %s", e)

    async def navigate_to_application_page(self, apply_url: str):
        """Navigate to job application page"""
        try:
            logger.info("Navigating to application page: %s", apply_url)
            await self.page.goto(apply_url, timeout=60000)
            await self.page.wait_for_load_state("networkidle")
            await self.page.wait_for_timeout(2000)
            logger.debug("Page loaded successfully")

        except Exception as e:
            logger.error("Failed to navigate to %s: %s", apply_url, e)
            raise

    async def extract_form_fields(self) -> Dict[str, List[str]]:
        """Extract all form fields from page"""
        try:
            fields = {
                "input": await self.page.evaluate("""
                    Array.from(document.querySelectorAll('input')).map(input => ({
                        selector: 'input[name="' + input.name + '"]',
                        type: input.type,
                        value: input.value
                    }))
                """),
                "select": await self.page.evaluate("""
                    Array.from(document.querySelectorAll('select')).map(select => ({
                        selector: 'select[name="' + select.name + '"]',
                        options: Array.from(select.options).map(option => option.value)
                    }))
                """),
                "textarea": await self.page.evaluate("""
                    Array.from(document.querySelectorAll('textarea')).map(textarea => ({
                        selector: 'textarea[name="' + textarea.name + '"]',
                        value: textarea.value
                    }))
                """),
            }

            logger.debug("Extracted fields: %s", fields)
            return fields

        except Exception as e:
            logger.warning("Failed to extract form fields: %s", e)
            return {}

    async def fill_application_form(self, profile: Dict):
        """Fill job application form with candidate profile"""
        try:
            logger.info("Filling application form with candidate profile")

            # Fill common fields using various selectors
            # Name fields
            await self.fill_form_field(
                "input[name*='first']", profile.get("first_name", "")
            )
            await self.fill_form_field(
                "input[name*='last']", profile.get("last_name", "")
            )
            await self.fill_form_field(
                "input[name*='name']", profile.get("full_name", "")
            )

            # Email fields
            await self.fill_form_field("input[type='email']", profile.get("email", ""))

            # Phone fields
            await self.fill_form_field("input[type='tel']", profile.get("phone", ""))
            await self.fill_form_field("input[name*='phone']", profile.get("phone", ""))

            # Location fields
            await self.fill_form_field(
                "input[name*='location']", profile.get("location", "")
            )
            await self.fill_form_field("input[name*='city']", profile.get("city", ""))

            # Experience fields
            await self.fill_form_field(
                "input[name*='experience']", str(profile.get("years_experience", ""))
            )
            await self.fill_form_field(
                "input[name*='years']", str(profile.get("years_experience", ""))
            )

            # Education fields
            await self.fill_form_field(
                "input[name*='degree']", profile.get("highest_degree", "")
            )

            # Skills field (textarea)
            skills_text = ", ".join(profile.get("skills", []))
            await self.fill_form_field("textarea[name*='skills']", skills_text)

            # LinkedIn field
            if profile.get("linkedin_url"):
                await self.fill_form_field(
                    "input[name*='linkedin']", profile.get("linkedin_url")
                )

            # GitHub field
            if profile.get("github_url"):
                await self.fill_form_field(
                    "input[name*='github']", profile.get("github_url")
                )

            logger.info("Form fields filled successfully")

        except Exception as e:
            logger.error("Failed to fill application form: %s", e)

    async def validate_form_submission(self):
        """Validate form submission success"""
        try:
            # Look for success indicators
            success_indicators = [
                "text='Application submitted'",
                "text='Thank you'",
                "text='Your application has been received'",
                "text='Success'",
                ".application-success",
            ]

            for selector in success_indicators:
                try:
                    await self.page.wait_for_selector(selector, timeout=30000)
                    logger.info("Application submitted successfully")
                    return True
                except Exception:
                    continue

            # Check for error indicators
            error_indicators = [
                ".error-message",
                "text='Error'",
                "text='Please correct'",
                "text='Required field'",
            ]

            for selector in error_indicators:
                try:
                    await self.page.wait_for_selector(selector, timeout=5000)
                    logger.warning("Application has errors")
                    return False
                except Exception:
                    continue

            logger.warning("Application status unclear, assuming success")
            return True

        except Exception as e:
            logger.error("Failed to validate form submission: %s", e)
            return False

    async def auto_apply_to_job(self, task: ApplicationTask) -> Dict:
        """
        Automatically apply to a job.

        Args:
            task: Application task with job and profile information

        Returns:
            Dictionary with application results
        """
        result = {
            "success": False,
            "status": "failed",
            "message": "",
            "submitted": False,
            "screenshot": None,
            "timestamp": datetime.now().isoformat(),
        }

        try:
            logger.info("Starting auto-apply for job: %s", task.job_id)

            # Initialize browser
            await self.initialize_browser()

            # Get job and profile
            db = next(get_db())
            job = db.query(Job).filter(Job.id == task.job_id).first()
            user = db.query(User).filter(User.id == task.user_id).first()
            profile = (
                db.query(CandidateProfile)
                .filter(CandidateProfile.user_id == task.user_id)
                .first()
            )

            if not job or not user or not profile:
                result["message"] = "Job or candidate profile not found"
                return result

            # Parse candidate profile to dictionary
            candidate_profile = self._parse_profile_to_dict(profile, user)

            # Check rate limits and circuit breaker before proceeding
            rate_allowed, rate_retry_after = domain_service.check_rate_limit(
                job.apply_url
            )
            if not rate_allowed:
                result["status"] = "rate_limited"
                result["message"] = (
                    f"Rate limit exceeded. Retry after {rate_retry_after:.1f} seconds"
                )
                logger.warning("Rate limit exceeded for %s", job.apply_url)

                # Send notification to user
                await self._send_user_notification(
                    task.user_id,
                    str(task.id),
                    "rate_limited",
                    f"Application rate limited. Will retry in {rate_retry_after:.0f} seconds.",
                    {"job_id": str(task.job_id), "retry_after": rate_retry_after},
                )

                return result

            cb_allowed, cb_retry_after = domain_service.check_circuit_breaker(
                job.apply_url
            )
            if not cb_allowed:
                result["status"] = "circuit_open"
                result["message"] = (
                    f"Circuit breaker open. Retry after {cb_retry_after:.1f} seconds"
                )
                logger.warning("Circuit breaker open for %s", job.apply_url)

                # Send notification to user
                await self._send_user_notification(
                    task.user_id,
                    str(task.id),
                    "circuit_open",
                    f"Application temporarily blocked. Will retry in {cb_retry_after:.0f} seconds.",
                    {"job_id": str(task.job_id), "retry_after": cb_retry_after},
                )

                return result

            # Navigate to application page
            await self.navigate_to_application_page(job.apply_url)

            # Check for CAPTCHA after navigation
            captcha_details = await self.check_for_captcha()
            if captcha_details:
                logger.warning("CAPTCHA detected for job %s", task.job_id)
                result["status"] = "waiting_human"
                result["message"] = "CAPTCHA detected, waiting for human resolution"
                result["captcha_details"] = captcha_details

                # Queue for human resolution
                if "human_task_id" in captcha_details:
                    logger.info("CAPTCHA queued for human resolution (Task ID: %s)", captcha_details["human_task_id"])

                # Send notification to user
                await self._send_user_notification(
                    task.user_id,
                    str(task.id),
                    "captcha_detected",
                    "CAPTCHA detected during application. Please complete the verification manually.",
                    {"job_id": str(task.job_id), "apply_url": job.apply_url},
                )

                return result

            # Handle common elements
            await self.handle_common_elements()

            # Fill application form
            await self.fill_application_form(candidate_profile)

            # Upload resume
            if profile.resume_file_url:
                await self.upload_file("input[type='file']", profile.resume_file_url)

            # Submit application
            await self.submit_form()

            # Wait for page navigation or processing
            await self.page.wait_for_load_state("networkidle")
            await self.page.wait_for_timeout(3000)

            # Validate submission
            result["submitted"] = await self.validate_form_submission()

            if result["submitted"]:
                result["success"] = True
                result["status"] = "success"
                result["message"] = "Application submitted successfully"
                logger.info("Application completed successfully")
                # Record successful request
                domain_service.record_request(job.apply_url, success=True)
            else:
                result["status"] = "failed"
                result["message"] = "Form validation failed"
                logger.warning("Application failed validation")
                # Record failed request
                domain_service.record_request(job.apply_url, success=False)

            # Take screenshot for debugging
            result["screenshot"] = await self.page.screenshot()

        except Exception as e:
            logger.error("Auto-apply failed: %s", e)
            import traceback

            logger.error("Traceback: %s", traceback.format_exc())
            result["message"] = str(e)

            try:
                result["screenshot"] = await self.page.screenshot()
            except Exception:
                pass

        finally:
            await self.close_browser()

        return result

    async def _send_user_notification(
        self,
        user_id: str,
        task_id: str,
        notification_type: str,
        message: str,
        metadata: Dict = None,
    ):
        """
        Send a notification to the user.

        Args:
            user_id: User ID
            task_id: Application task ID
            notification_type: Type of notification
            message: Notification message
            metadata: Additional metadata
        """
        try:
            # Import here to avoid circular imports
            from backend.services.notification_service import \
                notification_service

            await notification_service.send_notification(
                user_id=user_id,
                task_id=task_id,
                notification_type=notification_type,
                message=message,
                metadata=metadata or {},
            )

        except ImportError:
            # If notification service doesn't exist yet, just log
            logger.info("Notification: User %s, Task %s, Type %s, Message: %s" % (user_id, task_id, notification_type, message)
            )
        except Exception as e:
            logger.error("Failed to send notification: %s", e)

    def _parse_profile_to_dict(self, profile: CandidateProfile, user: User) -> Dict:
        """Convert CandidateProfile to dictionary"""
        full_name = profile.full_name or "John Doe"
        name_parts = full_name.split()

        return {
            "full_name": full_name,
            "first_name": name_parts[0] if len(name_parts) > 0 else "",
            "last_name": " ".join(name_parts[1:]) if len(name_parts) > 1 else "",
            "email": user.email,
            "phone": profile.phone or "",
            "location": profile.location or "",
            "city": profile.location.split(",")[0] if profile.location else "",
            "years_experience": (
                len(profile.work_experience) if profile.work_experience else 0
            ),
            "highest_degree": (
                profile.education[0].get("degree") if profile.education else ""
            ),
            "skills": profile.skills or [],
            "linkedin_url": "",
            "github_url": "",
        }

    async def run_application_task(self, task: ApplicationTask) -> Dict:
        """
        Run application task and update status.

        Args:
            task: Application task to run

        Returns:
            Dictionary with execution results
        """
        logger.info("Processing application task: %s", task.id)

        # Update task status
        task.status = "in_progress"
        task.attempt_count += 1
        task.updated_at = datetime.now()

        db = next(get_db())
        db.add(task)
        db.commit()

        try:
            # Run auto-apply
            result = await self.auto_apply_to_job(task)

            # Update task with results
            task.status = result["status"]
            task.attempt_count += 1
            task.updated_at = datetime.now()

            if not result["success"]:
                task.last_error = result["message"]

            db.add(task)
            db.commit()

            logger.info("Task completed: %s - Status: %s", task.id, task.status)

            return result

        except Exception as e:
            logger.error("Task failed: %s - Error: %s", task.id, e)

            task.status = "failed"
            task.attempt_count += 1
            task.last_error = str(e)
            task.updated_at = datetime.now()

            db.add(task)
            db.commit()

            return {
                "success": False,
                "status": "failed",
                "message": str(e),
                "submitted": False,
                "timestamp": datetime.now().isoformat(),
            }
        finally:
            db.close()


# Singleton instance
application_automation_service = ApplicationAutomationService()
