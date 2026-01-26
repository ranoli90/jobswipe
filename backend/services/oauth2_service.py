"""
OAuth2 service for social login (Google, LinkedIn)
"""

import os
from typing import Optional, Dict, Any
from authlib.integrations.httpx_client import AsyncOAuth2Client
from backend.vault_secrets import get_secret


class OAuth2Service:
    """Handles OAuth2 authentication with social providers"""

    def __init__(self):
        self.google_client_id = get_secret("jobswipe/oauth2/google", "client_id")
        self.google_client_secret = get_secret("jobswipe/oauth2/google", "client_secret")
        self.linkedin_client_id = get_secret("jobswipe/oauth2/linkedin", "client_id")
        self.linkedin_client_secret = get_secret("jobswipe/oauth2/linkedin", "client_secret")

        # OAuth2 configuration
        self.providers = {
            "google": {
                "client_id": self.google_client_id,
                "client_secret": self.google_client_secret,
                "authorize_url": "https://accounts.google.com/o/oauth2/auth",
                "access_token_url": "https://oauth2.googleapis.com/token",
                "userinfo_url": "https://www.googleapis.com/oauth2/v2/userinfo",
                "scope": "openid email profile",
                "redirect_uri": os.getenv("OAUTH2_REDIRECT_URI", "http://localhost:8000/auth/callback/google")
            },
            "linkedin": {
                "client_id": self.linkedin_client_id,
                "client_secret": self.linkedin_client_secret,
                "authorize_url": "https://www.linkedin.com/oauth/v2/authorization",
                "access_token_url": "https://www.linkedin.com/oauth/v2/accessToken",
                "userinfo_url": "https://api.linkedin.com/v2/people/~:(id,firstName,lastName,emailAddress)",
                "scope": "r_liteprofile r_emailaddress",
                "redirect_uri": os.getenv("OAUTH2_REDIRECT_URI", "http://localhost:8000/auth/callback/linkedin")
            }
        }

    def get_authorization_url(self, provider: str, state: str) -> Optional[str]:
        """
        Get authorization URL for OAuth2 provider

        Args:
            provider: OAuth2 provider (google, linkedin)
            state: State parameter for CSRF protection

        Returns:
            Authorization URL or None if provider not configured
        """
        if provider not in self.providers:
            return None

        config = self.providers[provider]
        if not config["client_id"] or not config["client_secret"]:
            return None

        client = AsyncOAuth2Client(
            client_id=config["client_id"],
            client_secret=config["client_secret"],
            redirect_uri=config["redirect_uri"]
        )

        authorization_url, _ = client.create_authorization_url(
            config["authorize_url"],
            state=state,
            scope=config["scope"]
        )

        return authorization_url

    async def get_user_info(self, provider: str, code: str) -> Optional[Dict[str, Any]]:
        """
        Exchange authorization code for access token and get user info

        Args:
            provider: OAuth2 provider (google, linkedin)
            code: Authorization code from callback

        Returns:
            User info dictionary or None if failed
        """
        if provider not in self.providers:
            return None

        config = self.providers[provider]
        if not config["client_id"] or not config["client_secret"]:
            return None

        try:
            client = AsyncOAuth2Client(
                client_id=config["client_id"],
                client_secret=config["client_secret"],
                redirect_uri=config["redirect_uri"]
            )

            # Exchange code for token
            token = await client.fetch_token(
                config["access_token_url"],
                code=code
            )

            # Get user info
            user_info = await client.get(config["userinfo_url"])
            user_info.raise_for_status()

            return self._normalize_user_info(provider, user_info.json())

        except Exception as e:
            print(f"OAuth2 error for {provider}: {e}")
            return None

    def _normalize_user_info(self, provider: str, user_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize user info from different providers to common format

        Args:
            provider: OAuth2 provider
            user_info: Raw user info from provider

        Returns:
            Normalized user info
        """
        if provider == "google":
            return {
                "provider": "google",
                "provider_id": user_info.get("id"),
                "email": user_info.get("email"),
                "email_verified": user_info.get("verified_email", False),
                "full_name": user_info.get("name"),
                "first_name": user_info.get("given_name"),
                "last_name": user_info.get("family_name"),
                "picture": user_info.get("picture")
            }
        elif provider == "linkedin":
            return {
                "provider": "linkedin",
                "provider_id": user_info.get("id"),
                "email": user_info.get("emailAddress"),
                "email_verified": True,  # LinkedIn emails are verified
                "full_name": f"{user_info.get('firstName', {}).get('localized', {}).get('en_US', '')} {user_info.get('lastName', {}).get('localized', {}).get('en_US', '')}".strip(),
                "first_name": user_info.get("firstName", {}).get("localized", {}).get("en_US"),
                "last_name": user_info.get("lastName", {}).get("localized", {}).get("en_US"),
                "picture": None
            }

        return user_info


# Global OAuth2 service instance
oauth2_service = OAuth2Service()