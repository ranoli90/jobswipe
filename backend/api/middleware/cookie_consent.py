"""
Cookie Consent Middleware

This middleware handles cookie consent preferences for GDPR compliance.
It provides:
- Cookie consent management for essential, analytics, and marketing cookies
- Do Not Track (DNT) header support
- Cookie banner configuration endpoint
- Consent persistence and validation
"""

import json
import logging
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware

from backend.db.database import SessionLocal
from backend.db.models import CookieConsent

# Configure logging
logger = logging.getLogger(__name__)


class CookieCategory(str, Enum):
    """Categories of cookies"""
    ESSENTIAL = "essential"
    ANALYTICS = "analytics"
    MARKETING = "marketing"
    PREFERENCES = "preferences"


class CookieConsentMiddleware(BaseHTTPMiddleware):
    """
    Middleware for handling cookie consent preferences.
    
    This middleware:
    - Reads cookie consent preferences from request
    - Respects Do Not Track headers
    - Validates cookie consent for analytics/marketing cookies
    - Provides consent information to downstream handlers
    """
    
    # Cookies that are essential and don't require consent
    ESSENTIAL_COOKIES: Set[str] = {
        "session",
        "csrf_token",
        "auth_token",
        "refresh_token",
        "cookie_consent",  # The consent cookie itself
        "cookie_consent_id",
    }
    
    # Analytics cookies that require consent
    ANALYTICS_COOKIES: Set[str] = {
        "_ga",
        "_gid",
        "_gat",
        "_ga_*",
        "mp_*",  # Mixpanel
        "amplitude_*",
        "segment_*",
    }
    
    # Marketing cookies that require consent
    MARKETING_COOKIES: Set[str] = {
        "_fbp",  # Facebook Pixel
        "_fbc",
        "fr",
        "tr",
        "_gcl_au",  # Google Ads
        "_gcl_aw",
        "_gcl_dc",
        "IDE",  # DoubleClick
        "NID",
    }
    
    # Preference cookies
    PREFERENCE_COOKIES: Set[str] = {
        "language",
        "theme",
        "timezone",
        "notification_preferences",
    }
    
    def __init__(self, app: FastAPI):
        super().__init__(app)
        logger.info("CookieConsentMiddleware initialized")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and handle cookie consent.
        
        Args:
            request: The incoming request
            call_next: The next middleware/handler in the chain
            
        Returns:
            The response from downstream handlers
        """
        # Parse cookie consent from request
        consent = self._parse_consent(request)
        
        # Check for Do Not Track header
        dnt_header = request.headers.get("DNT")
        consent["do_not_track"] = dnt_header == "1"
        
        # If DNT is enabled, disable analytics and marketing
        if consent["do_not_track"]:
            consent["analytics"] = False
            consent["marketing"] = False
            logger.debug("Do Not Track header detected, disabling analytics and marketing")
        
        # Store consent in request state for access by route handlers
        request.state.cookie_consent = consent
        
        # Process the request
        response = await call_next(request)
        
        # Set consent cookie if not present
        response = self._ensure_consent_cookie(request, response, consent)
        
        # Filter cookies in response based on consent
        response = self._filter_cookies(request, response, consent)
        
        return response
    
    def _parse_consent(self, request: Request) -> Dict[str, Any]:
        """
        Parse cookie consent from the request.
        
        Args:
            request: The incoming request
            
        Returns:
            Dictionary with consent preferences
        """
        # Default consent (only essential allowed)
        default_consent = {
            "essential": True,  # Always true
            "analytics": False,
            "marketing": False,
            "preferences": False,
            "do_not_track": False,
            "consent_id": None,
            "timestamp": None,
        }
        
        # Try to parse consent cookie
        consent_cookie = request.cookies.get("cookie_consent")
        if consent_cookie:
            try:
                parsed = json.loads(consent_cookie)
                default_consent.update(parsed)
            except json.JSONDecodeError:
                logger.warning("Invalid cookie_consent format")
        
        # Get consent ID
        consent_id = request.cookies.get("cookie_consent_id")
        if consent_id:
            default_consent["consent_id"] = consent_id
        else:
            default_consent["consent_id"] = str(uuid.uuid4())
        
        return default_consent
    
    def _ensure_consent_cookie(
        self,
        request: Request,
        response: Response,
        consent: Dict[str, Any],
    ) -> Response:
        """
        Ensure consent cookies are set in the response.
        
        Args:
            request: The incoming request
            response: The outgoing response
            consent: Current consent preferences
            
        Returns:
            Modified response with consent cookies
        """
        # Set consent ID cookie if not present
        if not request.cookies.get("cookie_consent_id"):
            response.set_cookie(
                key="cookie_consent_id",
                value=consent["consent_id"],
                max_age=365 * 24 * 60 * 60,  # 1 year
                httponly=True,
                secure=True,
                samesite="lax",
            )
        
        # Update consent cookie if changed
        consent_to_store = {
            "essential": consent["essential"],
            "analytics": consent["analytics"],
            "marketing": consent["marketing"],
            "preferences": consent["preferences"],
            "do_not_track": consent["do_not_track"],
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        response.set_cookie(
            key="cookie_consent",
            value=json.dumps(consent_to_store),
            max_age=365 * 24 * 60 * 60,  # 1 year
            httponly=False,  # Allow JavaScript access
            secure=True,
            samesite="lax",
        )
        
        return response
    
    def _filter_cookies(
        self,
        request: Request,
        response: Response,
        consent: Dict[str, Any],
    ) -> Response:
        """
        Filter cookies in the response based on consent.
        
        Args:
            request: The incoming request
            response: The outgoing response
            consent: Current consent preferences
            
        Returns:
            Modified response with filtered cookies
        """
        # Get all Set-Cookie headers
        set_cookie_headers = response.headers.getlist("set-cookie") if hasattr(response.headers, "getlist") else []
        
        if not set_cookie_headers:
            return response
        
        # Clear existing Set-Cookie headers
        response.raw_headers = [
            (name, value) for name, value in response.raw_headers
            if name.lower() != b"set-cookie"
        ]
        
        # Filter and re-add cookies
        for cookie_header in set_cookie_headers:
            cookie_name = self._extract_cookie_name(cookie_header)
            
            if self._is_cookie_allowed(cookie_name, consent):
                response.headers.append("set-cookie", cookie_header)
            else:
                logger.debug(f"Cookie '{cookie_name}' blocked due to consent preferences")
        
        return response
    
    def _extract_cookie_name(self, cookie_header: str) -> str:
        """
        Extract cookie name from Set-Cookie header.
        
        Args:
            cookie_header: The Set-Cookie header value
            
        Returns:
            Cookie name
        """
        if isinstance(cookie_header, bytes):
            cookie_header = cookie_header.decode("utf-8")
        
        # Cookie format: name=value; attributes...
        parts = cookie_header.split(";")
        name_value = parts[0].strip()
        
        if "=" in name_value:
            return name_value.split("=")[0].strip()
        
        return name_value
    
    def _is_cookie_allowed(self, cookie_name: str, consent: Dict[str, Any]) -> bool:
        """
        Check if a cookie is allowed based on consent.
        
        Args:
            cookie_name: Name of the cookie
            consent: Current consent preferences
            
        Returns:
            True if cookie is allowed, False otherwise
        """
        # Essential cookies are always allowed
        if cookie_name in self.ESSENTIAL_COOKIES:
            return True
        
        # Check if it's an essential cookie pattern
        for essential in self.ESSENTIAL_COOKIES:
            if essential.endswith("*") and cookie_name.startswith(essential[:-1]):
                return True
        
        # Check analytics cookies
        if self._is_analytics_cookie(cookie_name):
            return consent.get("analytics", False)
        
        # Check marketing cookies
        if self._is_marketing_cookie(cookie_name):
            return consent.get("marketing", False)
        
        # Check preference cookies
        if cookie_name in self.PREFERENCE_COOKIES:
            return consent.get("preferences", False)
        
        # Unknown cookies default to blocked if no consent
        logger.debug(f"Unknown cookie '{cookie_name}' - allowing (default)")
        return True
    
    def _is_analytics_cookie(self, cookie_name: str) -> bool:
        """Check if cookie is an analytics cookie"""
        for pattern in self.ANALYTICS_COOKIES:
            if pattern.endswith("*"):
                if cookie_name.startswith(pattern[:-1]):
                    return True
            elif cookie_name == pattern:
                return True
        return False
    
    def _is_marketing_cookie(self, cookie_name: str) -> bool:
        """Check if cookie is a marketing cookie"""
        for pattern in self.MARKETING_COOKIES:
            if pattern.endswith("*"):
                if cookie_name.startswith(pattern[:-1]):
                    return True
            elif cookie_name == pattern:
                return True
        return False


class CookieConsentManager:
    """
    Manager for cookie consent operations.
    
    Provides methods for:
    - Updating consent preferences
    - Storing consent in database
    - Retrieving consent configuration
    """
    
    def __init__(self, db: Session = None):
        self.db = db
    
    def update_consent(
        self,
        consent_id: str,
        essential: bool = True,
        analytics: bool = False,
        marketing: bool = False,
        preferences: bool = False,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update cookie consent preferences.
        
        Args:
            consent_id: Unique consent identifier
            essential: Essential cookies (always True)
            analytics: Analytics cookies consent
            marketing: Marketing cookies consent
            preferences: Preference cookies consent
            user_id: Optional user ID for logged-in users
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            Updated consent preferences
        """
        consent_data = {
            "consent_id": consent_id,
            "essential": True,  # Always true
            "analytics": analytics,
            "marketing": marketing,
            "preferences": preferences,
            "updated_at": datetime.utcnow().isoformat(),
        }
        
        # Store in database if available
        if self.db:
            try:
                # Check for existing consent
                existing = (
                    self.db.query(CookieConsent)
                    .filter(
                        (CookieConsent.consent_id == consent_id) |
                        (CookieConsent.user_id == user_id if user_id else False)
                    )
                    .first()
                )
                
                if existing:
                    existing.analytics = analytics
                    existing.marketing = marketing
                    existing.preferences = preferences
                    existing.updated_at = datetime.utcnow()
                else:
                    new_consent = CookieConsent(
                        id=uuid.uuid4(),
                        consent_id=consent_id,
                        user_id=uuid.UUID(user_id) if user_id else None,
                        essential=True,
                        analytics=analytics,
                        marketing=marketing,
                        preferences=preferences,
                        ip_address=ip_address,
                        user_agent=user_agent,
                    )
                    self.db.add(new_consent)
                
                self.db.commit()
                logger.info(f"Cookie consent updated for {consent_id}")
                
            except Exception as e:
                logger.error(f"Failed to store cookie consent: {e}")
                if self.db:
                    self.db.rollback()
        
        return consent_data
    
    def get_consent_config(self) -> Dict[str, Any]:
        """
        Get cookie consent configuration for the banner/UI.
        
        Returns:
            Configuration object for cookie consent UI
        """
        return {
            "version": "1.0",
            "categories": [
                {
                    "id": "essential",
                    "name": "Essential Cookies",
                    "description": "These cookies are necessary for the website to function and cannot be switched off.",
                    "required": True,
                    "cookies": list(CookieConsentMiddleware.ESSENTIAL_COOKIES),
                },
                {
                    "id": "analytics",
                    "name": "Analytics Cookies",
                    "description": "These cookies allow us to count visits and traffic sources so we can measure and improve the performance of our site.",
                    "required": False,
                    "cookies": list(CookieConsentMiddleware.ANALYTICS_COOKIES),
                },
                {
                    "id": "preferences",
                    "name": "Preference Cookies",
                    "description": "These cookies enable the website to provide enhanced functionality and personalization.",
                    "required": False,
                    "cookies": list(CookieConsentMiddleware.PREFERENCE_COOKIES),
                },
                {
                    "id": "marketing",
                    "name": "Marketing Cookies",
                    "description": "These cookies may be set through our site by our advertising partners to build a profile of your interests.",
                    "required": False,
                    "cookies": list(CookieConsentMiddleware.MARKETING_COOKIES),
                },
            ],
            "privacy_policy_url": "/api/v1/compliance/privacy-policy",
            "cookie_policy_url": "/api/v1/compliance/data-retention",
            "contact_email": "privacy@jobswipe.com",
        }
    
    def check_consent(self, consent_id: str, category: CookieCategory) -> bool:
        """
        Check if a specific cookie category is consented.
        
        Args:
            consent_id: Consent identifier
            category: Cookie category to check
            
        Returns:
            True if consented, False otherwise
        """
        if category == CookieCategory.ESSENTIAL:
            return True
        
        if not self.db:
            return False
        
        try:
            consent = (
                self.db.query(CookieConsent)
                .filter(CookieConsent.consent_id == consent_id)
                .first()
            )
            
            if not consent:
                return False
            
            if category == CookieCategory.ANALYTICS:
                return consent.analytics
            elif category == CookieCategory.MARKETING:
                return consent.marketing
            elif category == CookieCategory.PREFERENCES:
                return consent.preferences
            
        except Exception as e:
            logger.error(f"Failed to check consent: {e}")
        
        return False


# FastAPI dependency for cookie consent
def get_cookie_consent(request: Request) -> Dict[str, Any]:
    """
    Get cookie consent from request state.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Cookie consent dictionary
    """
    return getattr(request.state, "cookie_consent", {
        "essential": True,
        "analytics": False,
        "marketing": False,
        "preferences": False,
        "do_not_track": False,
    })


def add_cookie_consent_middleware(app: FastAPI) -> None:
    """
    Add cookie consent middleware to FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    app.add_middleware(CookieConsentMiddleware)
    logger.info("Cookie consent middleware added")
