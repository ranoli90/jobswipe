"""
Security Headers Middleware

Adds essential security headers to all HTTP responses to protect against
common web vulnerabilities like XSS, clickjacking, MIME-sniffing, etc.
"""

class SecurityHeadersMiddleware:
    """
    Middleware to add security headers to all HTTP responses.
    
    Adds the following security headers:
    - Content-Security-Policy: Restricts resource loading to trusted sources
    - X-Frame-Options: Prevents clickjacking attacks
    - X-XSS-Protection: Enables browser XSS protection
    - X-Content-Type-Options: Prevents MIME-sniffing
    - Referrer-Policy: Controls referrer information in requests
    - Strict-Transport-Security: Enforces HTTPS
    - X-Permitted-Cross-Domain-Policies: Controls cross-domain policy files
    - Permissions-Policy: Controls access to browser features
    """
    
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Capture the original send to modify responses
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                # Add security headers
                message["headers"].append(
                    (b"content-security-policy", 
                     b"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self' data:; frame-ancestors 'none'")
                )
                message["headers"].append(
                    (b"x-frame-options", b"DENY")
                )
                message["headers"].append(
                    (b"x-xss-protection", b"1; mode=block")
                )
                message["headers"].append(
                    (b"x-content-type-options", b"nosniff")
                )
                message["headers"].append(
                    (b"referrer-policy", b"strict-origin-when-cross-origin")
                )
                message["headers"].append(
                    (b"strict-transport-security", b"max-age=31536000; includeSubDomains; preload")
                )
                message["headers"].append(
                    (b"x-permitted-cross-domain-policies", b"none")
                )
                message["headers"].append(
                    (b"permissions-policy", b"accelerometer=(), autoplay=(), camera=(), display-capture=(), encrypted-media=(), fullscreen=(), geolocation=(), gyroscope=(), magnetometer=(), microphone=(), midi=(), payment=(), picture-in-picture=(), sync-xhr=(), usb=()")
                )
            await send(message)

        await self.app(scope, receive, send_wrapper)
