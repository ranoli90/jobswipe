"""
App Store Service
Handles Apple App Store metadata lookup and validation.
"""

import httpx
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any

APP_ID = "6504584959"
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
OUTPUT_FILE = os.path.join(DATA_DIR, "appstore_lookup.json")
PREVIOUS_FILE = os.path.join(DATA_DIR, "appstore_lookup_prev.json")

def ensure_data_dir_exists():
    """Ensure data directory exists"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)

def fetch_appstore_metadata() -> Optional[Dict[str, Any]]:
    """
    Fetch App Store metadata using Apple Lookup API.
    
    Returns:
        Parsed JSON response or None if failed
    """
    ensure_data_dir_exists()
    
    url = f"https://itunes.apple.com/lookup?id={APP_ID}"
    
    try:
        with httpx.Client(timeout=30) as client:
            response = client.get(url)
            response.raise_for_status()
            data = response.json()
            
            # Save to file
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            
            return data
            
    except Exception as e:
        import logging
        logging.error(f"Failed to fetch App Store metadata: {str(e)}")
        return None

def get_appstore_metadata() -> Optional[Dict[str, Any]]:
    """
    Get saved App Store metadata.
    
    Returns:
        Parsed JSON response or None if file doesn't exist
    """
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            import logging
            logging.error(f"Failed to read App Store metadata file: {str(e)}")
    
    return None

def get_prev_appstore_metadata() -> Optional[Dict[str, Any]]:
    """
    Get previous App Store metadata.
    
    Returns:
        Parsed JSON response or None if file doesn't exist
    """
    if os.path.exists(PREVIOUS_FILE):
        try:
            with open(PREVIOUS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            import logging
            logging.error(f"Failed to read previous App Store metadata file: {str(e)}")
    
    return None

def has_metadata_changed() -> bool:
    """
    Check if metadata has changed from previous version.
    
    Returns:
        True if metadata has changed, False otherwise
    """
    current = get_appstore_metadata()
    previous = get_prev_appstore_metadata()
    
    if not previous or not current:
        return True
        
    return json.dumps(current) != json.dumps(previous)

def update_prev_metadata():
    """Update previous metadata file with current version"""
    ensure_data_dir_exists()
    
    if os.path.exists(OUTPUT_FILE):
        try:
            import shutil
            shutil.copy(OUTPUT_FILE, PREVIOUS_FILE)
        except Exception as e:
            import logging
            logging.error(f"Failed to update previous metadata file: {str(e)}")

def get_app_info() -> Optional[Dict[str, Any]]:
    """
    Get parsed app information from metadata.
    
    Returns:
        Dictionary with key app information or None if failed
    """
    metadata = get_appstore_metadata()
    
    if metadata and "results" in metadata and len(metadata["results"]) > 0:
        result = metadata["results"][0]
        
        return {
            "version": result.get("version"),
            "minimumOsVersion": result.get("minimumOsVersion"),
            "sellerName": result.get("sellerName"),
            "releaseNotes": result.get("releaseNotes"),
            "screenshotUrls": result.get("screenshotUrls", [])[:3],
            "averageUserRating": result.get("averageUserRating"),
            "userRatingCount": result.get("userRatingCount"),
            "bundleId": result.get("bundleId"),
            "trackId": result.get("trackId")
        }
    
    return None

def validate_appstore_data() -> bool:
    """
    Validate App Store metadata.
    
    Returns:
        True if metadata is valid, False otherwise
    """
    metadata = get_appstore_metadata()
    
    if not metadata:
        return False
        
    if "results" not in metadata or len(metadata["results"]) == 0:
        return False
        
    result = metadata["results"][0]
    
    required_fields = [
        "version", 
        "minimumOsVersion", 
        "sellerName",
        "bundleId",
        "trackId"
    ]
    
    for field in required_fields:
        if field not in result:
            return False
            
    return True

def run_audit() -> Dict[str, Any]:
    """
    Run full App Store metadata audit.
    
    Returns:
        Audit result dictionary
    """
    audit_result = {
        "timestamp": datetime.now().isoformat(),
        "success": False,
        "appInfo": None,
        "changed": False,
        "error": None
    }
    
    try:
        # Fetch latest metadata
        metadata = fetch_appstore_metadata()
        
        if metadata:
            audit_result["appInfo"] = get_app_info()
            audit_result["changed"] = has_metadata_changed()
            
            if audit_result["changed"]:
                update_prev_metadata()
            
            audit_result["success"] = True
            
    except Exception as e:
        audit_result["error"] = str(e)
        
    return audit_result

if __name__ == "__main__":
    # Run audit and print results
    result = run_audit()
    print("App Store Metadata Audit")
    print("=" * 30)
    print(f"Timestamp: {result['timestamp']}")
    print(f"Success: {result['success']}")
    if result["error"]:
        print(f"Error: {result['error']}")
    else:
        print(f"Changed: {result['changed']}")
        app_info = result["appInfo"]
        print(f"Version: {app_info['version']}")
        print(f"Minimum OS: {app_info['minimumOsVersion']}")
        print(f"Seller: {app_info['sellerName']}")
        print(f"Bundle ID: {app_info['bundleId']}")
