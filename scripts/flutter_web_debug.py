#!/usr/bin/env python3
"""
Comprehensive Playwright Debugging Script for Flutter Web Application

This script helps diagnose blank screen issues in Flutter web apps by:
- Launching Chrome in headful mode for visual inspection
- Capturing screenshots at various stages of page load
- Recording console logs with types (error, warning, info)
- Capturing all network requests and responses
- Examining API endpoint responses
- Checking for JavaScript errors
- Inspecting DOM structure to identify rendering issues
- Saving detailed debugging output to a report file

Usage:
    python scripts/flutter_web_debug.py [--url URL] [--output OUTPUT_DIR] [--timeout TIMEOUT]
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from playwright.async_api import (
    async_playwright,
    Browser,
    BrowserContext,
    ConsoleMessage,
    Page,
    Request,
    Response,
)


class FlutterWebDebugger:
    """Comprehensive debugger for Flutter web applications."""
    
    def __init__(
        self,
        app_url: str = "https://jobswipe-9obhra.fly.dev",
        output_dir: str = "./debug_output",
        timeout: int = 60000,
        headless: bool = False,
    ):
        self.app_url = app_url
        self.output_dir = Path(output_dir)
        self.timeout = timeout
        self.headless = headless
        
        # Debug data collection
        self.console_logs: List[Dict[str, Any]] = []
        self.network_requests: List[Dict[str, Any]] = []
        self.network_responses: List[Dict[str, Any]] = []
        self.js_errors: List[Dict[str, Any]] = []
        self.screenshots: List[Dict[str, str]] = []
        self.dom_snapshot: Optional[Dict[str, Any]] = None
        self.timeline_events: List[Dict[str, Any]] = []
        
        # API endpoints to monitor
        self.api_base_url = "https://jobswipe-9obhra.fly.dev"
        self.health_endpoint = "/health"
        
    async def setup_browser(self, playwright: Any) -> tuple[Browser, BrowserContext, Page]:
        """Launch Chrome browser with debugging options."""
        self._log_timeline("browser_launch_started")
        
        browser = await playwright.chromium.launch(
            headless=self.headless,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,SitePerProcess",
                "--allow-running-insecure-content",
                "--disable-extensions",
                "--disable-popup-blocking",
                "--disable-notifications",
                "--disable-background-networking",
                "--disable-sync",
                "--disable-translate",
                "--metrics-recording-only",
                "--mute-audio",
                "--no-first-run",
                "--safebrowsing-disable-auto-update",
                "--hide-scrollbars",
                "--window-size=1920,1080",
            ],
        )
        
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
            locale="en-US",
            timezone_id="UTC",
            accept_downloads=False,
            ignore_https_errors=True,
        )
        
        page = await context.new_page()
        
        # Set up console logging
        page.on("console", self._handle_console)
        
        # Set up request/response logging
        page.on("request", self._handle_request)
        page.on("response", self._handle_response)
        
        # Set up page error handling
        page.on("pageerror", self._handle_page_error)
        
        # Set up frame navigation events
        page.on("framenavigated", self._handle_frame_navigated)
        
        self._log_timeline("browser_launch_completed")
        
        return browser, context, page
    
    def _log_timeline(self, event: str, details: Optional[Dict] = None):
        """Log a timeline event."""
        timestamp = datetime.utcnow().isoformat()
        event_data = {
            "timestamp": timestamp,
            "event": event,
            "details": details or {},
        }
        self.timeline_events.append(event_data)
        print(f"[TIMELINE] {timestamp} - {event}")
        
    def _handle_console(self, msg: ConsoleMessage):
        """Handle console messages from the page."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": msg.type,
            "text": msg.text,
            "location": msg.location,
        }
        self.console_logs.append(log_entry)
        
        # Separate errors and warnings
        if msg.type == "error":
            print(f"[CONSOLE ERROR] {msg.text}")
        elif msg.type == "warning":
            print(f"[CONSOLE WARNING] {msg.text}")
        else:
            print(f"[CONSOLE {msg.type.upper()}] {msg.text}")
    
    def _handle_request(self, request: Request):
        """Handle network requests."""
        request_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "url": request.url,
            "method": request.method,
            "headers": dict(request.headers),
            "resource_type": request.resource_type,
            "post_data": request.post_data,
        }
        self.network_requests.append(request_data)
        
        # Check if it's an API request
        if "/api/" in request.url or request.url.endswith("/health"):
            print(f"[NETWORK REQUEST] {request.method} {request.url}")
    
    def _handle_response(self, response: Response):
        """Handle network responses."""
        response_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "url": response.url,
            "status": response.status,
            "status_text": response.status_text,
            "headers": dict(response.headers),
            "content_length": response.headers.get("content-length"),
        }
        self.network_responses.append(response_data)
        
        # Log failed responses
        if response.status >= 400:
            print(f"[NETWORK ERROR] {response.status} {response.url}")
        else:
            print(f"[NETWORK RESPONSE] {response.status} {response.url}")
    
    def _handle_page_error(self, error: Exception):
        """Handle JavaScript page errors."""
        error_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "stack_trace": getattr(error, "stack", None),
        }
        self.js_errors.append(error_data)
        print(f"[JS ERROR] {type(error).__name__}: {error}")
    
    def _handle_frame_navigated(self, frame):
        """Handle frame navigation events."""
        if frame:
            self._log_timeline("frame_navigated", {"url": frame.url})
    
    async def _take_screenshot(self, page: Page, name: str):
        """Take a screenshot and save it."""
        screenshot_path = self.output_dir / "screenshots" / f"{name}.png"
        screenshot_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            await page.screenshot(path=str(screenshot_path), full_page=True)
            screenshot_data = {
                "name": name,
                "path": str(screenshot_path),
                "timestamp": datetime.utcnow().isoformat(),
            }
            self.screenshots.append(screenshot_data)
            print(f"[SCREENSHOT] Saved: {screenshot_path}")
            return True
        except Exception as e:
            print(f"[SCREENSHOT ERROR] Failed to capture {name}: {e}")
            return False
    
    async def _capture_dom_snapshot(self, page: Page):
        """Capture detailed DOM structure."""
        try:
            # Get basic DOM info
            dom_info = await page.evaluate("""() => {
                return {
                    title: document.title,
                    url: document.URL,
                    readyState: document.readyState,
                    bodyHTML: document.body ? document.body.innerHTML.substring(0, 5000) : 'No body',
                    bodyText: document.body ? document.body.innerText.substring(0, 2000) : 'No body text',
                    children: document.body ? document.body.children.length : 0,
                    scripts: Array.from(document.scripts).map(s => s.src),
                    stylesheets: Array.from(document.styleSheets).map(s => s.href),
                    images: document.images.length,
                    links: document.links.length,
                    forms: document.forms.length,
                    // Check for common Flutter elements
                    hasFlutterEngine: !!document.querySelector('flt-glass-pane, flutter-view, flt-scene'),
                    hasLoadingIndicator: !!document.querySelector('.loading, #loading, [class*="loading"]'),
                    hasError: !!document.querySelector('.error, #error, [class*="error"]'),
                    // Get all script errors
                    consoleErrors: window._consoleErrors || [],
                };
            }""")
            
            self.dom_snapshot = {
                "timestamp": datetime.utcnow().isoformat(),
                **dom_info,
            }
            
            print(f"[DOM SNAPSHOT] Captured - URL: {dom_info['url']}, State: {dom_info['readyState']}")
            return self.dom_snapshot
            
        except Exception as e:
            print(f"[DOM SNAPSHOT ERROR] {e}")
            return None
    
    async def _check_flutter_specific_errors(self, page: Page) -> Dict[str, Any]:
        """Check for Flutter-specific rendering issues."""
        try:
            flutter_status = await page.evaluate("""() => {
                const result = {
                    flutterLoaded: false,
                    engineVersion: null,
                    errorMessage: null,
                    renderElement: null,
                    serviceWorkerReady: false,
                    widgetsCount: 0,
                };
                
                // Check if Flutter is loaded
                if (window.flutter && window.flutter.engine) {
                    result.flutterLoaded = true;
                    result.engineVersion = window.flutter.engineVersion || 'unknown';
                }
                
                // Check for Flutter render element
                const fltGlass = document.querySelector('flt-glass-pane');
                const fltScene = document.querySelector('flt-scene');
                const flutterView = document.querySelector('flutter-view');
                
                if (fltGlass) {
                    result.renderElement = 'flt-glass-pane';
                } else if (fltScene) {
                    result.renderElement = 'flt-scene';
                } else if (flutterView) {
                    result.renderElement = 'flutter-view';
                }
                
                // Check for service worker
                if ('serviceWorker' in navigator) {
                    navigator.serviceWorker.ready.then(reg => {
                        result.serviceWorkerReady = true;
                    }).catch(() => {});
                }
                
                // Try to get widget count (approximate)
                try {
                    const rootElement = document.body.querySelector('[class*="flutter"], [class*="material"], [class*="cupertino"]');
                    if (rootElement) {
                        result.widgetsCount = rootElement.querySelectorAll('*').length;
                    }
                } catch (e) {}
                
                // Check for loading errors
                const loadingEl = document.querySelector('.loading, #loading, [class*="loading"]');
                if (loadingEl) {
                    result.loadingElementFound = true;
                    result.loadingText = loadingEl.innerText || loadingEl.textContent || 'Loading...';
                }
                
                return result;
            }""")
            
            print(f"[FLUTTER STATUS] {flutter_status}")
            return flutter_status
            
        except Exception as e:
            print(f"[FLUTTER CHECK ERROR] {e}")
            return {"error": str(e)}
    
    async def _wait_for_network_idle(self, page: Page, timeout: int = 30000):
        """Wait for network to be idle."""
        try:
            await page.wait_for_load_state("networkidle", timeout=timeout)
            print("[NETWORK] Network idle reached")
        except Exception as e:
            print(f"[NETWORK] Network idle timeout: {e}")
    
    async def _wait_for_dom_ready(self, page: Page, timeout: int = 30000):
        """Wait for DOM to be ready."""
        try:
            await page.wait_for_load_state("domcontentloaded", timeout=timeout)
            print("[DOM] DOM content loaded")
        except Exception as e:
            print(f"[DOM] DOM ready timeout: {e}")
    
    async def debug_session(self):
        """Run the complete debugging session."""
        print(f"\n{'='*60}")
        print(f"FLUTTER WEB DEBUGGER - SESSION STARTED")
        print(f"{'='*60}")
        print(f"App URL: {self.app_url}")
        print(f"Output Directory: {self.output_dir}")
        print(f"Headless Mode: {self.headless}")
        print(f"{'='*60}\n")
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "screenshots").mkdir(exist_ok=True)
        
        async with async_playwright() as p:
            browser, context, page = await self.setup_browser(p)
            
            try:
                # Stage 1: Navigate to the page
                self._log_timeline("navigation_started", {"url": self.app_url})
                print(f"\n[NAVIGATION] Navigating to: {self.app_url}")
                
                response = await page.goto(
                    self.app_url,
                    wait_until="domcontentloaded",
                    timeout=self.timeout,
                )
                
                print(f"[NAVIGATION] Response status: {response.status if response else 'No response'}")
                self._log_timeline("navigation_completed")
                
                # Stage 2: Take initial screenshot
                await self._take_screenshot(page, "01_initial_load")
                
                # Stage 3: Wait for DOM ready
                await self._wait_for_dom_ready(page)
                await self._take_screenshot(page, "02_dom_ready")
                
                # Stage 4: Wait for network idle
                await self._wait_for_network_idle(page)
                await self._take_screenshot(page, "03_network_idle")
                
                # Stage 5: Capture DOM snapshot
                await self._capture_dom_snapshot(page)
                
                # Stage 6: Check Flutter-specific status
                flutter_status = await self._check_flutter_specific_errors(page)
                
                # Stage 7: Additional wait for Flutter to render
                print("\n[FLUTTER] Waiting for Flutter engine to initialize...")
                await asyncio.sleep(5)  # Give Flutter time to render
                await self._take_screenshot(page, "04_flutter_rendered")
                
                # Stage 8: Check again for Flutter status after rendering
                flutter_status_after = await self._check_flutter_specific_errors(page)
                
                # Stage 9: Wait a bit more and take final screenshot
                await asyncio.sleep(5)
                await self._take_screenshot(page, "05_final_state")
                
                # Stage 10: Capture final DOM state
                final_dom = await self._capture_dom_snapshot(page)
                
                # Stage 11: Check for API health
                await self._check_api_health(page)
                
            except Exception as e:
                print(f"\n[ERROR] Debug session error: {e}")
                self.js_errors.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "error_type": "SessionError",
                    "error_message": str(e),
                })
                # Try to capture error screenshot
                try:
                    await self._take_screenshot(page, "99_error_state")
                except:
                    pass
            
            finally:
                await browser.close()
                self._log_timeline("browser_closed")
        
        # Generate debug report
        await self._generate_debug_report(flutter_status, flutter_status_after)
        
        print(f"\n{'='*60}")
        print(f"DEBUG SESSION COMPLETED")
        print(f"{'='*60}")
        print(f"Output saved to: {self.output_dir}")
        print(f"Total screenshots: {len(self.screenshots)}")
        print(f"Console logs: {len(self.console_logs)}")
        print(f"JS errors: {len(self.js_errors)}")
        print(f"Network requests: {len(self.network_requests)}")
        print(f"{'='*60}\n")
        
        return self._create_summary()
    
    async def _check_api_health(self, page: Page):
        """Check backend API health endpoint."""
        try:
            health_url = f"{self.api_base_url}{self.health_endpoint}"
            response = await page.request.get(health_url)
            
            # Get response content
            content_type = response.headers.get("content-type", "")
            
            if "application/json" in content_type:
                response_body = await response.json()
            else:
                response_body = await response.text()
            
            health_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "url": health_url,
                "status": response.status,
                "response": response_body,
            }
            
            print(f"[API HEALTH] {health_url} - Status: {response.status}")
            return health_data
            
        except Exception as e:
            print(f"[API HEALTH ERROR] {e}")
            return {"error": str(e)}
    
    async def _generate_debug_report(
        self,
        flutter_initial: Dict[str, Any],
        flutter_final: Dict[str, Any],
    ):
        """Generate a comprehensive debug report."""
        report = {
            "session_info": {
                "start_time": self.timeline_events[0]["timestamp"] if self.timeline_events else None,
                "end_time": datetime.utcnow().isoformat(),
                "app_url": self.app_url,
                "output_dir": str(self.output_dir),
            },
            "timeline": self.timeline_events,
            "screenshots": self.screenshots,
            "console_logs": {
                "total": len(self.console_logs),
                "errors": [log for log in self.console_logs if log["type"] == "error"],
                "warnings": [log for log in self.console_logs if log["type"] == "warning"],
                "all": self.console_logs,
            },
            "javascript_errors": self.js_errors,
            "network_requests": self.network_requests,
            "network_responses": self.network_responses,
            "dom_snapshot": self.dom_snapshot,
            "flutter_status": {
                "initial": flutter_initial,
                "final": flutter_final,
            },
            "analysis": self._analyze_issues(),
        }
        
        # Save report as JSON
        report_path = self.output_dir / "debug_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"[REPORT] Debug report saved to: {report_path}")
        
        # Save HTML report
        await self._generate_html_report(report, report_path)
        
        return report
    
    def _analyze_issues(self) -> Dict[str, List[str]]:
        """Analyze collected data to identify potential issues."""
        issues = {
            "critical": [],
            "warnings": [],
            "info": [],
        }
        
        # Check for JS errors
        if self.js_errors:
            issues["critical"].append(f"Found {len(self.js_errors)} JavaScript errors")
        
        # Check for console errors
        console_errors = [log for log in self.console_logs if log["type"] == "error"]
        if console_errors:
            issues["critical"].append(f"Found {len(console_errors)} console errors")
        
        # Check for failed network requests
        failed_requests = [
            req for req in self.network_requests
            if any(resp["url"] == req["url"] and resp["status"] >= 400
                   for resp in self.network_responses)
        ]
        if failed_requests:
            issues["warnings"].append(f"Found {len(failed_requests)} failed network requests")
        
        # Check for missing Flutter elements
        if self.dom_snapshot:
            if not self.dom_snapshot.get("hasFlutterEngine"):
                issues["critical"].append("Flutter engine element not found in DOM")
            
            if self.dom_snapshot.get("hasError"):
                issues["critical"].append("Error element detected in DOM")
        
        # Check if page has content
        if self.dom_snapshot:
            body_text = self.dom_snapshot.get("bodyText", "").strip()
            if len(body_text) < 50:
                issues["critical"].append("Page appears to have minimal or no content (possible blank screen)")
            else:
                issues["info"].append(f"Page has {len(body_text)} characters of text content")
        
        return issues
    
    async def _generate_html_report(self, report: Dict, json_path: Path):
        """Generate an HTML version of the debug report."""
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Flutter Web Debug Report - {report["session_info"]["app_url"]}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        .section {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .critical {{ color: #dc3545; }}
        .warning {{ color: #ffc107; }}
        .info {{ color: #17a2b8; }}
        .screenshot {{
            margin: 10px 0;
            border: 2px solid #ddd;
            border-radius: 4px;
        }}
        .screenshot img {{
            max-width: 100%;
            height: auto;
        }}
        .log-entry {{
            padding: 8px;
            margin: 4px 0;
            border-radius: 4px;
            font-family: monospace;
            font-size: 12px;
        }}
        .log-error {{ background: #f8d7da; }}
        .log-warning {{ background: #fff3cd; }}
        .log-info {{ background: #d1ecf1; }}
        .timeline {{
            display: flex;
            flex-direction: column;
            gap: 8px;
        }}
        .timeline-item {{
            padding: 10px;
            background: #e9ecef;
            border-radius: 4px;
            border-left: 4px solid #667eea;
        }}
        .issues-list {{
            list-style: none;
            padding: 0;
        }}
        .issues-list li {{
            padding: 10px;
            margin: 5px 0;
            border-radius: 4px;
        }}
        .issues-critical {{
            background: #f8d7da;
            border-left: 4px solid #dc3545;
        }}
        .issues-warning {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
        }}
        .issues-info {{
            background: #d1ecf1;
            border-left: 4px solid #17a2b8;
        }}
        .summary-stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .stat-number {{
            font-size: 36px;
            font-weight: bold;
        }}
        .stat-label {{
            font-size: 14px;
            opacity: 0.9;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔍 Flutter Web Debug Report</h1>
        <p>App: {report["session_info"]["app_url"]}</p>
        <p>Generated: {report["session_info"]["end_time"]}</p>
    </div>
    
    <div class="section">
        <h2>📊 Summary Statistics</h2>
        <div class="summary-stats">
            <div class="stat-card">
                <div class="stat-number">{len(report["screenshots"])}</div>
                <div class="stat-label">Screenshots</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{len(report["console_logs"]["errors"])}</div>
                <div class="stat-label">Console Errors</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{len(report["javascript_errors"])}</div>
                <div class="stat-label">JS Errors</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{len(report["network_requests"])}</div>
                <div class="stat-label">Network Requests</div>
            </div>
        </div>
    </div>
    
    <div class="section">
        <h2>⚠️ Issues Analysis</h2>
        <h3>Critical Issues</h3>
        <ul class="issues-list">
            {"".join(f'<li class="issues-critical">{issue}</li>' for issue in report["analysis"]["critical"]) or '<li>No critical issues found</li>'}
        </ul>
        <h3>Warnings</h3>
        <ul class="issues-list">
            {"".join(f'<li class="issues-warning">{issue}</li>' for issue in report["analysis"]["warnings"]) or '<li>No warnings found</li>'}
        </ul>
        <h3>Info</h3>
        <ul class="issues-list">
            {"".join(f'<li class="issues-info">{issue}</li>' for issue in report["analysis"]["info"]) or '<li>No additional info</li>'}
        </ul>
    </div>
    
    <div class="section">
        <h2>📸 Screenshots</h2>
        {"".join(f'''
        <div class="screenshot">
            <h4>{s["name"]}</h4>
            <p>Captured: {s["timestamp"]}</p>
            <img src="screenshots/{s["name"]}.png" alt="{s["name"]}">
        </div>
        ''' for s in report["screenshots"]) or '<p>No screenshots captured</p>'}
    </div>
    
    <div class="section">
        <h2>📜 Timeline</h2>
        <div class="timeline">
            {"".join(f'''
            <div class="timeline-item">
                <strong>{e["event"]}</strong>
                <p>{e["timestamp"]}</p>
                {"".join(f'<p>{k}: {v}</p>' for k, v in e["details"].items())}
            </div>
            ''' for e in report["timeline"])}
        </div>
    </div>
    
    <div class="section">
        <h2>🐛 JavaScript Errors</h2>
        {report["javascript_errors"] and "".join(f'''
        <div class="log-entry log-error">
            <strong>{err["error_type"]}</strong>
            <p>{err["error_message"]}</p>
            <p>{err["timestamp"]}</p>
        </div>
        ''' for err in report["javascript_errors"]) or '<p>No JavaScript errors detected</p>'}
    </div>
    
    <div class="section">
        <h2>🖥️ Console Errors</h2>
        {report["console_logs"]["errors"] and "".join(f'''
        <div class="log-entry log-error">
            <p>{log["text"]}</p>
            <small>{log["timestamp"]}</small>
        </div>
        ''' for log in report["console_logs"]["errors"]) or '<p>No console errors detected</p>'}
    </div>
    
    <div class="section">
        <h2>🌐 DOM Snapshot</h2>
        {report["dom_snapshot"] and f'''
        <h3>Page Info</h3>
        <ul>
            <li>URL: {report["dom_snapshot"]["url"]}</li>
            <li>Title: {report["dom_snapshot"]["title"]}</li>
            <li>Ready State: {report["dom_snapshot"]["readyState"]}</li>
            <li>Body Children: {report["dom_snapshot"]["children"]}</li>
            <li>Scripts: {len(report["dom_snapshot"]["scripts"])}</li>
            <li>Images: {report["dom_snapshot"]["images"]}</li>
            <li>Flutter Engine: {report["dom_snapshot"]["hasFlutterEngine"]}</li>
        </ul>
        ''' or '<p>No DOM snapshot available</p>'}
    </div>
    
    <div class="section">
        <h2>🔧 Flutter Status</h2>
        <h3>Initial Check</h3>
        <pre>{json.dumps(report["flutter_status"]["initial"], indent=2)}</pre>
        <h3>Final Check</h3>
        <pre>{json.dumps(report["flutter_status"]["final"], indent=2)}</pre>
    </div>
    
    <div class="section">
        <h2>📡 Network Summary</h2>
        <p>Total Requests: {len(report["network_requests"])}</p>
        <p>Failed Requests: {len([r for r in report["network_requests"] if any(resp["url"] == r["url"] and resp["status"] >= 400 for resp in report["network_responses"])])}</p>
    </div>
    
    <div class="section">
        <h2>📁 Raw Data</h2>
        <p>Full debug report: <a href="debug_report.json">debug_report.json</a></p>
    </div>
</body>
</html>"""
        
        html_path = self.output_dir / "debug_report.html"
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        print(f"[REPORT] HTML report saved to: {html_path}")
    
    def _create_summary(self) -> Dict[str, Any]:
        """Create a summary of the debugging session."""
        return {
            "status": "completed",
            "timestamp": datetime.utcnow().isoformat(),
            "screenshots_captured": len(self.screenshots),
            "console_errors": len([log for log in self.console_logs if log["type"] == "error"]),
            "javascript_errors": len(self.js_errors),
            "network_requests": len(self.network_requests),
            "critical_issues": len(self._analyze_issues()["critical"]),
            "output_directory": str(self.output_dir),
        }


async def main():
    """Main entry point for the Flutter web debugger."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Flutter Web Debugger")
    parser.add_argument(
        "--url",
        default="https://jobswipe-9obhra.fly.dev",
        help="URL of the Flutter web app to debug",
    )
    parser.add_argument(
        "--output",
        default="./debug_output",
        help="Output directory for debug artifacts",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60000,
        help="Timeout in milliseconds",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run in headless mode (default: False for visual inspection)",
    )
    
    args = parser.parse_args()
    
    # Create debugger instance
    debugger = FlutterWebDebugger(
        app_url=args.url,
        output_dir=args.output,
        timeout=args.timeout,
        headless=args.headless,
    )
    
    # Run debugging session
    summary = await debugger.debug_session()
    
    # Print summary
    print("\n" + "="*60)
    print("DEBUGGING SESSION SUMMARY")
    print("="*60)
    print(f"Status: {summary['status']}")
    print(f"Screenshots: {summary['screenshots_captured']}")
    print(f"Console Errors: {summary['console_errors']}")
    print(f"JavaScript Errors: {summary['javascript_errors']}")
    print(f"Network Requests: {summary['network_requests']}")
    print(f"Critical Issues: {summary['critical_issues']}")
    print(f"Output Directory: {summary['output_directory']}")
    print("="*60)
    
    return summary


if __name__ == "__main__":
    asyncio.run(main())
