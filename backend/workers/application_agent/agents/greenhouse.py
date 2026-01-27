"""
Greenhouse ATS Application Agent

Handles automated job applications to Greenhouse ATS.
"""

import logging
import os

from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)


class GreenhouseAgent:
    """Agent for applying to jobs on Greenhouse ATS"""

    @staticmethod
    async def apply(apply_url: str, profile: dict, resume_path: str, logger):
        """
        Automate job application to Greenhouse ATS.

        Args:
            apply_url: Job application URL
            profile: Candidate profile data
            resume_path: Path to resume file
            logger: Logger for audit trail

        Returns:
            Success status and any errors
        """
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(locale="en-US")
                page = await context.new_page()

                try:
                    # Navigate to application page
                    await page.goto(apply_url, wait_until="domcontentloaded")
                    logger.step("navigate", {"url": apply_url})

                    # Check for CAPTCHA
                    captcha_detected = await GreenhouseAgent._check_captcha(
                        page, logger
                    )
                    if captcha_detected:
                        logger.step("captcha_detected", {"url": apply_url})
                        return False, "CAPTCHA detected - requires human intervention"

                    # Fill out personal information
                    await page.fill(
                        'input[name="first_name"]',
                        (
                            profile.get("full_name", "").split()[0]
                            if profile.get("full_name")
                            else ""
                        ),
                    )
                    await page.fill(
                        'input[name="last_name"]',
                        (
                            " ".join(profile.get("full_name", "").split()[1:])
                            if profile.get("full_name")
                            and len(profile.get("full_name").split()) > 1
                            else ""
                        ),
                    )
                    await page.fill('input[type="email"]', profile.get("email", ""))
                    await page.fill('input[name="phone"]', profile.get("phone", ""))
                    logger.step(
                        "fill_personal_info",
                        {
                            "data": {
                                "email": profile.get("email"),
                                "phone": profile.get("phone"),
                            }
                        },
                    )

                    # Upload resume
                    await page.set_input_files('input[type="file"]', resume_path)
                    logger.step("upload_resume", {"resume_path": resume_path})

                    # Fill out location
                    location = profile.get("location", "")
                    if location:
                        await page.fill('input[name="location"]', location)

                    # Answer standard questions (example)
                    # This would need to be customized based on specific job application forms
                    await page.select_option(
                        'select[name="job_title"]', label="Software Engineer"
                    )

                    # Submit application
                    await page.click('button[type="submit"]')
                    await page.wait_for_selector("text=Thank you", timeout=60000)
                    logger.step("submit", {"result": "success"})

                    return True, None

                except Exception as e:
                    logger.step("error", {"message": str(e)})
                    await page.screenshot(path="greenhouse_error.png")
                    return False, str(e)
                finally:
                    await context.close()
                    await browser.close()

        except Exception as e:
            logger.step("error", {"message": str(e)})
            return False, str(e)

    @staticmethod
    async def _check_captcha(page, logger):
        """Check if page contains CAPTCHA"""
        try:
            # Check for common CAPTCHA patterns
            captcha_indicators = [
                "captcha",
                "g-recaptcha",
                "reCAPTCHA",
                "security-check",
                "verify-you-are-human",
                "prove-you-are-not-a-robot",
            ]

            # Check for CAPTCHA elements in the DOM
            page_content = await page.content()
            for indicator in captcha_indicators:
                if indicator in page_content.lower():
                    logger.step("captcha_detected", {"indicator": indicator})
                    await page.screenshot(path="greenhouse_captcha.png")
                    return True

            return False

        except Exception as e:
            logger.step("captcha_detection_error", {"message": str(e)})
            return False


class LeverAgent:
    """Agent for applying to jobs on Lever ATS"""

    @staticmethod
    async def apply(apply_url: str, profile: dict, resume_path: str, logger):
        """
        Automate job application to Lever ATS.

        Args:
            apply_url: Job application URL
            profile: Candidate profile data
            resume_path: Path to resume file
            logger: Logger for audit trail

        Returns:
            Success status and any errors
        """
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(locale="en-US")
                page = await context.new_page()

                try:
                    # Navigate to application page
                    await page.goto(apply_url, wait_until="domcontentloaded")
                    logger.step("navigate", {"url": apply_url})

                    # Check for CAPTCHA
                    captcha_detected = await LeverAgent._check_captcha(page, logger)
                    if captcha_detected:
                        logger.step("captcha_detected", {"url": apply_url})
                        return False, "CAPTCHA detected - requires human intervention"

                    # Fill out personal information
                    await page.fill('input[name="name"]', profile.get("full_name", ""))
                    await page.fill('input[type="email"]', profile.get("email", ""))
                    await page.fill('input[name="phone"]', profile.get("phone", ""))
                    logger.step(
                        "fill_personal_info",
                        {
                            "data": {
                                "email": profile.get("email"),
                                "phone": profile.get("phone"),
                            }
                        },
                    )

                    # Upload resume
                    await page.set_input_files('input[type="file"]', resume_path)
                    logger.step("upload_resume", {"resume_path": resume_path})

                    # Answer standard questions
                    await page.select_option(
                        'select[name="experience"]', label="3-5 years"
                    )

                    # Submit application
                    await page.click('button[type="submit"]')
                    await page.wait_for_selector(
                        "text=Application submitted", timeout=60000
                    )
                    logger.step("submit", {"result": "success"})

                    return True, None

                except Exception as e:
                    logger.step("error", {"message": str(e)})
                    await page.screenshot(path="lever_error.png")
                    return False, str(e)
                finally:
                    await context.close()
                    await browser.close()

        except Exception as e:
            logger.step("error", {"message": str(e)})
            return False, str(e)

    @staticmethod
    async def _check_captcha(page, logger):
        """Check if page contains CAPTCHA"""
        try:
            # Check for common CAPTCHA patterns
            captcha_indicators = [
                "captcha",
                "g-recaptcha",
                "reCAPTCHA",
                "security-check",
                "verify-you-are-human",
                "prove-you-are-not-a-robot",
            ]

            # Check for CAPTCHA elements in the DOM
            page_content = await page.content()
            for indicator in captcha_indicators:
                if indicator in page_content.lower():
                    logger.step("captcha_detected", {"indicator": indicator})
                    await page.screenshot(path="lever_captcha.png")
                    return True

            return False

        except Exception as e:
            logger.step("captcha_detection_error", {"message": str(e)})
            return False


class ApplicationLogger:
    """Logger for application task audit trail"""

    def __init__(self, task_id: str):
        """
        Initialize logger.

        Args:
            task_id: Application task ID
        """
        self.task_id = task_id
        self.logs = []

    def step(self, step: str, payload: dict):
        """
        Log step.

        Args:
            step: Step name
            payload: Step data
        """
        log_entry = {
            "step": step,
            "payload": payload,
            "timestamp": "2026-01-25T00:00:00Z",
        }
        self.logs.append(log_entry)
        logger.info("Task %s - %s: %s", ('self.task_id', 'step', 'payload'))

    def get_logs(self):
        """Get all log entries"""
        return self.logs
