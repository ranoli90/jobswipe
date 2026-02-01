"""
Security Headers Middleware

Adds essential security headers to all HTTP responses to protect against
common web vulnerabilities like XSS, clickjacking, MIME-sniffing, etc.

Following OWASP recommendations:
- https://owasp.org/www-project-secure-headers/
- https://cheatsheetseries.owasp.org/cheatsheets/HTTP_Headers_Cheat_Sheet.html
"""

import os
import logging

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware:
    """
    Middleware to add security headers to all HTTP responses.
    
    Adds the following security headers:
    - Content-Security-Policy: Restricts resource loading to trusted sources
    - Content-Security-Policy-Report-Only: CSP in report-only mode (staging)
    - X-Frame-Options: Prevents clickjacking attacks
    - X-XSS-Protection: Enables browser XSS protection
    - X-Content-Type-Options: Prevents MIME-sniffing
    - Referrer-Policy: Controls referrer information in requests
    - Strict-Transport-Security: Enforces HTTPS (with preload)
    - X-Permitted-Cross-Domain-Policies: Controls cross-domain policy files
    - Permissions-Policy: Controls access to browser features
    - Cross-Origin-Embedder-Policy: Controls cross-origin embedding
    - Cross-Origin-Opener-Policy: Controls cross-origin window interactions
    - Cross-Origin-Resource-Policy: Controls cross-origin resource sharing
    - Report-To: Configures reporting endpoints for violations
    """
    
    def __init__(self, app):
        self.app = app
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.csp_report_uri = os.getenv("CSP_REPORT_URI", "/csp-report")
        self.csp_report_only = os.getenv("CSP_REPORT_ONLY", "false").lower() == "true"
        
        # Build CSP directive with report-uri if configured
        self.csp_directive = self._build_csp_directive()
        
        logger.info(f"SecurityHeadersMiddleware initialized for environment: {self.environment}")
        if self.csp_report_only:
            logger.info("CSP is in report-only mode")

    def _build_csp_directive(self):
        """Build the Content Security Policy directive."""
        base_csp = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self'; "
            "media-src 'self'; "
            "object-src 'none'; "
            "frame-src 'none'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
        
        # Add report-uri if configured
        if self.csp_report_uri:
            base_csp += f"; report-uri {self.csp_report_uri}"
            base_csp += f"; report-to csp-endpoint"
        
        return base_csp

    def _get_report_to_header(self):
        """Build the Report-To header for CSP violation reporting."""
        if not self.csp_report_uri:
            return None
        
        # Report-To header format (JSON)
        report_to = {
            "group": "csp-endpoint",
            "max_age": 10886400,
            "endpoints": [
                {"url": self.csp_report_uri}
            ]
        }
        import json
        return json.dumps(report_to)

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Capture the original send to modify responses
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                # Determine if we should use report-only mode
                # Enable report-only for staging environments to test CSP without blocking
                is_report_only = self.csp_report_only or self.environment == "staging"
                
                # Add Content-Security-Policy header
                if is_report_only:
                    message["headers"].append(
                        (b"content-security-policy-report-only", 
                         self.csp_directive.encode())
                    )
                else:
                    message["headers"].append(
                        (b"content-security-policy", 
                         self.csp_directive.encode())
                    )
                
                # Add Report-To header for CSP violation reporting
                report_to = self._get_report_to_header()
                if report_to:
                    message["headers"].append(
                        (b"report-to", report_to.encode())
                    )
                
                # X-Frame-Options: Prevents clickjacking
                message["headers"].append(
                    (b"x-frame-options", b"DENY")
                )
                
                # X-XSS-Protection: Enables browser XSS filter
                message["headers"].append(
                    (b"x-xss-protection", b"1; mode=block")
                )
                
                # X-Content-Type-Options: Prevents MIME-sniffing
                message["headers"].append(
                    (b"x-content-type-options", b"nosniff")
                )
                
                # Referrer-Policy: Controls referrer information
                message["headers"].append(
                    (b"referrer-policy", b"strict-origin-when-cross-origin")
                )
                
                # Strict-Transport-Security: Enforces HTTPS with preload
                # max-age=31536000 (1 year), includeSubDomains, preload
                message["headers"].append(
                    (b"strict-transport-security", b"max-age=31536000; includeSubDomains; preload")
                )
                
                # X-Permitted-Cross-Domain-Policies: Controls Flash cross-domain policies
                message["headers"].append(
                    (b"x-permitted-cross-domain-policies", b"none")
                )
                
                # Permissions-Policy: Controls browser features
                # Disables unnecessary features to reduce attack surface
                message["headers"].append(
                    (b"permissions-policy", 
                     b"accelerometer=(), autoplay=(), camera=(), display-capture=(), "
                     b"encrypted-media=(), fullscreen=(), geolocation=(), gyroscope=(), "
                     b"magnetometer=(), microphone=(), midi=(), payment=(), "
                     b"picture-in-picture=(), sync-xhr=(), usb=(), web-share=(), "
                     b"xr-spatial-tracking=()")
                )
                
                # Cross-Origin-Embedder-Policy: Controls cross-origin embedding
                message["headers"].append(
                    (b"cross-origin-embedder-policy", b"require-corp")
                )
                
                # Cross-Origin-Opener-Policy: Controls cross-origin window interactions
                message["headers"].append(
                    (b"cross-origin-opener-policy", b"same-origin")
                )
                
                # Cross-Origin-Resource-Policy: Controls cross-origin resource sharing
                message["headers"].append(
                    (b"cross-origin-resource-policy", b"same-origin")
                )
                
            await send(message)

        await self.app(scope, receive, send_wrapper)
