#!/usr/bin/env python3
"""
Security Audit Script for JobSwipe API

This script performs comprehensive security checks on the JobSwipe API
configuration, environment variables, and security headers.

Usage:
    python backend/scripts/security_audit.py [--output <file>]

Exit codes:
    0 - No critical security issues found
    1 - Critical security issues detected
"""

import argparse
import json
import os
import re
import ssl
import subprocess
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


class SecurityAudit:
    """Security audit checker for JobSwipe API."""
    
    # Patterns that indicate exposed secrets
    SECRET_PATTERNS = {
        "api_key": re.compile(r"[a-zA-Z0-9_-]*api[_-]?key[a-zA-Z0-9_-]*", re.IGNORECASE),
        "secret": re.compile(r"[a-zA-Z0-9_-]*secret[a-zA-Z0-9_-]*", re.IGNORECASE),
        "password": re.compile(r"[a-zA-Z0-9_-]*password[a-zA-Z0-9_-]*", re.IGNORECASE),
        "token": re.compile(r"[a-zA-Z0-9_-]*token[a-zA-Z0-9_-]*", re.IGNORECASE),
        "private_key": re.compile(r"[a-zA-Z0-9_-]*private[_-]?key[a-zA-Z0-9_-]*", re.IGNORECASE),
        "credential": re.compile(r"[a-zA-Z0-9_-]*credential[a-zA-Z0-9_-]*", re.IGNORECASE),
    }
    
    # Sensitive file patterns
    SENSITIVE_FILES = [
        ".env",
        ".env.local",
        ".env.production",
        ".env.staging",
        "*.pem",
        "*.key",
        "*.p12",
        "*.pfx",
        "id_rsa",
        "id_dsa",
        "id_ecdsa",
        "id_ed25519",
        ".htpasswd",
        ".netrc",
        "credentials.json",
        "service-account.json",
    ]
    
    # Required security headers
    REQUIRED_HEADERS = {
        "Content-Security-Policy": {
            "required": True,
            "description": "Prevents XSS and data injection attacks",
        },
        "X-Frame-Options": {
            "required": True,
            "description": "Prevents clickjacking attacks",
        },
        "X-Content-Type-Options": {
            "required": True,
            "description": "Prevents MIME-sniffing",
        },
        "Referrer-Policy": {
            "required": True,
            "description": "Controls referrer information",
        },
        "Strict-Transport-Security": {
            "required": True,
            "description": "Enforces HTTPS connections",
        },
        "Permissions-Policy": {
            "required": False,
            "description": "Controls browser permissions",
        },
        "Cross-Origin-Embedder-Policy": {
            "required": False,
            "description": "Controls cross-origin embedding",
        },
        "Cross-Origin-Opener-Policy": {
            "required": False,
            "description": "Controls cross-origin window interactions",
        },
        "Cross-Origin-Resource-Policy": {
            "required": False,
            "description": "Controls cross-origin resource sharing",
        },
    }
    
    def __init__(self):
        self.findings: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []
        self.info: List[Dict[str, Any]] = []
        self.environment = os.getenv("ENVIRONMENT", "development")
        
    def add_finding(self, category: str, severity: str, message: str, details: Optional[Dict] = None):
        """Add a security finding."""
        finding = {
            "timestamp": datetime.utcnow().isoformat(),
            "category": category,
            "severity": severity,
            "message": message,
            "details": details or {},
        }
        if severity == "CRITICAL":
            self.findings.append(finding)
        elif severity == "WARNING":
            self.warnings.append(finding)
        else:
            self.info.append(finding)
            
    def check_cors_configuration(self) -> None:
        """Check CORS configuration for security issues."""
        print("Checking CORS configuration...")
        
        cors_origins = os.getenv("CORS_ALLOW_ORIGINS", "")
        
        if not cors_origins:
            self.add_finding(
                "CORS",
                "WARNING",
                "CORS_ALLOW_ORIGINS not set - using default configuration",
                {"environment": self.environment}
            )
            return
        
        # Parse origins
        origins = [o.strip() for o in cors_origins.split(",")]
        
        # Check for wildcard in production
        if self.environment == "production":
            if "*" in origins:
                self.add_finding(
                    "CORS",
                    "CRITICAL",
                    "Wildcard CORS origin '*' is not allowed in production",
                    {"origins": origins}
                )
            
            # Check for localhost in production
            localhost_patterns = ["localhost", "127.0.0.1", "::1", "0.0.0.0"]
            for origin in origins:
                origin_lower = origin.lower()
                for pattern in localhost_patterns:
                    if pattern in origin_lower:
                        self.add_finding(
                            "CORS",
                            "CRITICAL",
                            f"Localhost origin '{origin}' should not be allowed in production",
                            {"origin": origin, "pattern": pattern}
                        )
                        break
        
        # Check for http in production
        if self.environment == "production":
            for origin in origins:
                if origin.startswith("http://"):
                    self.add_finding(
                        "CORS",
                        "WARNING",
                        f"Non-HTTPS origin '{origin}' detected in production",
                        {"origin": origin}
                    )
        
        self.add_finding(
            "CORS",
            "INFO",
            f"CORS configuration checked - {len(origins)} origin(s) configured",
            {"origins": origins, "environment": self.environment}
        )
    
    def check_environment_variables(self) -> None:
        """Check environment variables for exposed secrets."""
        print("Checking environment variables for exposed secrets...")
        
        # Required secrets that should be set
        required_secrets = [
            "SECRET_KEY",
            "ENCRYPTION_PASSWORD",
            "ENCRYPTION_SALT",
            "OAUTH_STATE_SECRET",
        ]
        
        # API keys that should be set
        api_keys = [
            "ANALYTICS_API_KEY",
            "INGESTION_API_KEY",
            "DEDUPLICATION_API_KEY",
            "CATEGORIZATION_API_KEY",
            "AUTOMATION_API_KEY",
        ]
        
        # Check required secrets
        for secret in required_secrets:
            value = os.getenv(secret)
            if not value:
                self.add_finding(
                    "SECRETS",
                    "CRITICAL" if self.environment == "production" else "WARNING",
                    f"Required secret '{secret}' is not set",
                    {"variable": secret}
                )
            elif self._is_weak_secret(value):
                self.add_finding(
                    "SECRETS",
                    "WARNING",
                    f"Secret '{secret}' appears to be weak or default",
                    {"variable": secret, "hint": "Value length or pattern suggests weak secret"}
                )
        
        # Check API keys
        for key in api_keys:
            value = os.getenv(key)
            if not value:
                self.add_finding(
                    "SECRETS",
                    "WARNING",
                    f"API key '{key}' is not set",
                    {"variable": key}
                )
            elif value.startswith("dev-") and self.environment == "production":
                self.add_finding(
                    "SECRETS",
                    "CRITICAL",
                    f"Development API key '{key}' used in production",
                    {"variable": key}
                )
        
        # Check for secrets in environment that might be logged
        env_vars = dict(os.environ)
        for var_name, value in env_vars.items():
            # Skip checking the variable name itself for patterns
            if any(pattern.search(var_name) for pattern in self.SECRET_PATTERNS.values()):
                # This is a secret variable, check if value looks exposed
                if len(value) < 16:
                    self.add_finding(
                        "SECRETS",
                        "WARNING",
                        f"Secret variable '{var_name}' has a short value (possible weak secret)",
                        {"variable": var_name, "length": len(value)}
                    )
    
    def _is_weak_secret(self, value: str) -> bool:
        """Check if a secret value appears weak."""
        weak_patterns = [
            "password",
            "secret",
            "123",
            "admin",
            "test",
            "dev-",
            "CHANGE_",
            "your-",
            "example",
        ]
        
        value_lower = value.lower()
        
        # Check length
        if len(value) < 16:
            return True
        
        # Check for weak patterns
        for pattern in weak_patterns:
            if pattern in value_lower:
                return True
        
        return False
    
    def check_security_headers(self) -> None:
        """Check if security headers middleware is configured."""
        print("Checking security headers configuration...")
        
        # Check if middleware file exists and is importable
        middleware_path = os.path.join(
            os.path.dirname(__file__), "..", "api", "middleware", "security_headers.py"
        )
        
        if not os.path.exists(middleware_path):
            self.add_finding(
                "HEADERS",
                "CRITICAL",
                "Security headers middleware file not found",
                {"path": middleware_path}
            )
            return
        
        # Try to import and check configuration
        try:
            import sys
            backend_path = os.path.join(os.path.dirname(__file__), "..")
            if backend_path not in sys.path:
                sys.path.insert(0, backend_path)
            
            from api.middleware.security_headers import SecurityHeadersMiddleware
            
            self.add_finding(
                "HEADERS",
                "INFO",
                "Security headers middleware is available",
                {}
            )
            
        except ImportError as e:
            self.add_finding(
                "HEADERS",
                "WARNING",
                f"Could not import security headers middleware: {e}",
                {}
            )
    
    def check_tls_configuration(self) -> None:
        """Check TLS/SSL configuration."""
        print("Checking TLS/SSL configuration...")
        
        # Check if running in production without HTTPS enforcement
        if self.environment == "production":
            # Check for TLS-related environment variables
            tls_cert = os.getenv("TLS_CERT_PATH")
            tls_key = os.getenv("TLS_KEY_PATH")
            
            if not tls_cert and not tls_key:
                # In containerized environments, TLS is often handled by load balancer
                self.add_finding(
                    "TLS",
                    "INFO",
                    "TLS certificates not configured in environment - ensure TLS is handled by load balancer/reverse proxy",
                    {"environment": self.environment}
                )
        
        # Check Python SSL version
        ssl_version = ssl.OPENSSL_VERSION
        self.add_finding(
            "TLS",
            "INFO",
            f"OpenSSL version: {ssl_version}",
            {}
        )
        
        # Check for SSL verification disabling
        if os.getenv("PYTHONHTTPSVERIFY") == "0":
            self.add_finding(
                "TLS",
                "CRITICAL",
                "Python SSL verification is disabled (PYTHONHTTPSVERIFY=0)",
                {}
            )
        
        if os.getenv("CURL_CA_BUNDLE") == "":
            self.add_finding(
                "TLS",
                "WARNING",
                "cURL CA bundle verification is disabled",
                {}
            )
    
    def check_sensitive_files(self) -> None:
        """Check for sensitive files that shouldn't be in repository."""
        print("Checking for sensitive files...")
        
        backend_dir = os.path.join(os.path.dirname(__file__), "..")
        
        for pattern in self.SENSITIVE_FILES:
            # Use glob to find files
            import glob
            search_path = os.path.join(backend_dir, "**", pattern)
            matches = glob.glob(search_path, recursive=True)
            
            for match in matches:
                # Skip files in .git directory
                if ".git" in match:
                    continue
                
                # Check if file is in .gitignore
                if not self._is_in_gitignore(match):
                    self.add_finding(
                        "FILES",
                        "WARNING",
                        f"Sensitive file found and not in .gitignore: {match}",
                        {"file": match, "pattern": pattern}
                    )
    
    def _is_in_gitignore(self, filepath: str) -> bool:
        """Check if a file is covered by .gitignore."""
        gitignore_path = os.path.join(os.path.dirname(__file__), "..", "..", ".gitignore")
        
        if not os.path.exists(gitignore_path):
            return False
        
        try:
            result = subprocess.run(
                ["git", "check-ignore", "-q", filepath],
                capture_output=True,
                cwd=os.path.dirname(__file__)
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def check_database_security(self) -> None:
        """Check database connection security."""
        print("Checking database security...")
        
        database_url = os.getenv("DATABASE_URL", "")
        
        if not database_url:
            self.add_finding(
                "DATABASE",
                "WARNING",
                "DATABASE_URL not set",
                {}
            )
            return
        
        # Check for SSL in database URL
        if "postgresql" in database_url.lower():
            if "sslmode" not in database_url.lower() and self.environment == "production":
                self.add_finding(
                    "DATABASE",
                    "WARNING",
                    "PostgreSQL connection does not specify SSL mode in production",
                    {"hint": "Add ?sslmode=require or ?sslmode=verify-full to DATABASE_URL"}
                )
        
        # Check for credentials in URL (basic check)
        if "@" in database_url:
            # URL contains credentials
            self.add_finding(
                "DATABASE",
                "INFO",
                "Database URL contains credentials - ensure this is from a secure vault/secrets manager",
                {}
            )
    
    def check_debug_mode(self) -> None:
        """Check if debug mode is enabled in production."""
        print("Checking debug mode...")
        
        debug = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes", "on")
        
        if debug and self.environment == "production":
            self.add_finding(
                "DEBUG",
                "CRITICAL",
                "DEBUG mode is enabled in production environment",
                {"DEBUG": os.getenv("DEBUG")}
            )
        elif debug:
            self.add_finding(
                "DEBUG",
                "INFO",
                "DEBUG mode is enabled (acceptable for non-production)",
                {"environment": self.environment}
            )
    
    def run_all_checks(self) -> None:
        """Run all security checks."""
        print("=" * 80)
        print(f"JobSwipe Security Audit - {datetime.utcnow().isoformat()}")
        print(f"Environment: {self.environment}")
        print("=" * 80)
        print()
        
        self.check_cors_configuration()
        self.check_environment_variables()
        self.check_security_headers()
        self.check_tls_configuration()
        self.check_sensitive_files()
        self.check_database_security()
        self.check_debug_mode()
        
        print()
        print("=" * 80)
    
    def generate_report(self, output_file: Optional[str] = None) -> Dict[str, Any]:
        """Generate a comprehensive security audit report."""
        report = {
            "metadata": {
                "timestamp": datetime.utcnow().isoformat(),
                "environment": self.environment,
                "version": "1.0.0",
            },
            "summary": {
                "total_findings": len(self.findings),
                "total_warnings": len(self.warnings),
                "total_info": len(self.info),
                "critical_issues": len([f for f in self.findings if f["severity"] == "CRITICAL"]),
            },
            "findings": {
                "critical": [f for f in self.findings if f["severity"] == "CRITICAL"],
                "warnings": self.warnings,
                "info": self.info,
            },
            "recommendations": self._generate_recommendations(),
        }
        
        if output_file:
            with open(output_file, "w") as f:
                json.dump(report, f, indent=2)
            print(f"\nReport saved to: {output_file}")
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate security recommendations based on findings."""
        recommendations = []
        
        # Check for critical issues
        critical_count = len([f for f in self.findings if f["severity"] == "CRITICAL"])
        if critical_count > 0:
            recommendations.append(
                f"URGENT: Address {critical_count} critical security issue(s) immediately"
            )
        
        # CORS recommendations
        cors_issues = [f for f in self.findings if f["category"] == "CORS"]
        if cors_issues:
            recommendations.append(
                "Review CORS configuration - ensure only trusted origins are allowed in production"
            )
        
        # Secret recommendations
        secret_issues = [f for f in self.findings if f["category"] == "SECRETS"]
        if secret_issues:
            recommendations.append(
                "Review secret management - use a secure vault or secrets manager in production"
            )
        
        # TLS recommendations
        tls_issues = [f for f in self.findings if f["category"] == "TLS"]
        if tls_issues:
            recommendations.append(
                "Ensure TLS 1.2+ is enforced for all connections in production"
            )
        
        # General recommendations
        if self.environment == "production":
            recommendations.append(
                "Enable security monitoring and alerting for production environment"
            )
            recommendations.append(
                "Implement regular security audits and penetration testing"
            )
        
        return recommendations
    
    def print_summary(self) -> None:
        """Print a summary of findings to console."""
        print("\n" + "=" * 80)
        print("SECURITY AUDIT SUMMARY")
        print("=" * 80)
        
        critical_count = len([f for f in self.findings if f["severity"] == "CRITICAL"])
        warning_count = len(self.warnings)
        info_count = len(self.info)
        
        print(f"\nCritical Issues: {critical_count}")
        print(f"Warnings: {warning_count}")
        print(f"Info: {info_count}")
        
        if self.findings:
            print("\n--- CRITICAL FINDINGS ---")
            for finding in self.findings:
                print(f"[{finding['category']}] {finding['message']}")
        
        if self.warnings:
            print("\n--- WARNINGS ---")
            for warning in self.warnings:
                print(f"[{warning['category']}] {warning['message']}")
        
        print("\n--- RECOMMENDATIONS ---")
        for rec in self._generate_recommendations():
            print(f"• {rec}")
        
        print("\n" + "=" * 80)
        
        if critical_count > 0:
            print("\n❌ AUDIT FAILED: Critical security issues found!")
        elif warning_count > 0:
            print("\n⚠️  AUDIT PASSED WITH WARNINGS: Review warnings above")
        else:
            print("\n✅ AUDIT PASSED: No critical issues found")
        
        print("=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="Security Audit Script for JobSwipe API"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file for JSON report (default: print to stdout)"
    )
    parser.add_argument(
        "--format", "-f",
        choices=["json", "console"],
        default="console",
        help="Output format (default: console)"
    )
    
    args = parser.parse_args()
    
    # Run audit
    audit = SecurityAudit()
    audit.run_all_checks()
    
    # Generate report
    if args.format == "json" or args.output:
        report = audit.generate_report(args.output)
        if not args.output:
            print(json.dumps(report, indent=2))
    
    # Print summary
    if args.format == "console":
        audit.print_summary()
    
    # Exit with appropriate code
    critical_count = len([f for f in audit.findings if f["severity"] == "CRITICAL"])
    sys.exit(1 if critical_count > 0 else 0)


if __name__ == "__main__":
    main()
