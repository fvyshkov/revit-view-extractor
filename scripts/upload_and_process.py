#!/usr/bin/env python3
"""
RevitViewExtractor - Upload and Process Utility

Uploads a Revit file to Autodesk OSS and processes it in Design Automation.

Usage:
    python upload_and_process.py <path_to_revit_file> [options]

Options:
    --type TYPE       Filter by view type
    --exportable      Show only exportable views
    --json            Output in JSON format
"""

import os
import sys
import json
import argparse
import requests
from config import CLIENT_ID, CLIENT_SECRET, APS_BASE_URL

def get_access_token():
    """Get Autodesk access token"""
    url = "https://developer.api.autodesk.com/authentication/v2/token"
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials",
        "scope": "code:all data:write data:read bucket:create bucket:read"
    }
    response = requests.post(url, headers={"Content-Type": "application/x-www-form-urlencoded"}, data=data)
    return response.json()["access_token"] if response.status_code == 200 else None

def create_bucket(token):
    """Create a bucket for file uploads"""
    bucket_name = f"{CLIENT_ID.lower()}-revit-view-extractor"
    url = f"{APS_BASE_URL}/oss/v2/buckets"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {
        "bucketKey": bucket_name,
        "policyKey": "transient"  # Files will be automatically deleted after some time
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code in [200, 409]:  # 409 means bucket already exists
        return bucket_name
    
    print(f"Failed to create bucket: {response.text}")
    return None

def upload_file(token, bucket_name, file_path):
    """Upload file to OSS"""
    filename = os.path.basename(file_path)
    url = f"{APS_BASE_URL}/oss/v2/buckets/{bucket_name}/objects/{filename}"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/octet-stream"
    }
    
    with open(file_path, 'rb') as f:
        response = requests.put(url, headers=headers, data=f)
    
    if response.status_code == 200:
        return f"https://developer.api.autodesk.com/oss/v2/buckets/{bucket_name}/objects/{filename}"
    
    print(f"Failed to upload file: {response.text}")
    return None

def process_revit_file(file_url, view_type=None, exportable=None):
    """Process uploaded Revit file in Design Automation"""
    token = get_access_token()
    
    # Prepare workitem data
    workitem_data = {
        "activityId": f"{CLIENT_ID}.ExtractViewsActivityV3",
        "arguments": {
            "inputFile": {"url": file_url},
            "viewType": view_type,
            "exportableOnly": exportable,
            "result": {"url": "https://httpbin.org/put"}
        }
    }
    
    # Send workitem to process file
    url = "https://developer.api.autodesk.com/da/us-east/v3/workitems"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, headers=headers, json=workitem_data)
    
    if response.status_code != 200:
        print(f"Error processing file: {response.text}")
        return None
    
    workitem_id = response.json()["id"]
    
    # Monitor workitem
    status_url = f"https://developer.api.autodesk.com/da/us-east/v3/workitems/{workitem_id}"
    
    import time
    for _ in range(30):  # 5 minutes timeout
        status_response = requests.get(status_url, headers=headers)
        if status_response.status_code == 200:
            status_data = status_response.json()
            if status_data["status"] == "success":
                # Get report
                report_url = status_data.get("reportUrl")
                if report_url:
                    report_response = requests.get(report_url)
                    if report_response.status_code == 200:
                        return parse_view_report(report_response.text, view_type, exportable)
            elif status_data["status"] == "failed":
                print("Workitem processing failed")
                return None
        time.sleep(10)
    
    print("Timeout waiting for workitem")
    return None

def parse_view_report(report_text, view_type=None, exportable=None):
    """Parse view report and apply filters"""
    try:
        report_data = json.loads(report_text)
    except json.JSONDecodeError:
        # If not JSON, assume it's a text report
        report_data = {
            "view_list": [
                {
                    "name": line.split(" (")[0].strip("•"),
                    "type": line.split(" (")[1].split(")")[0],
                    "exportable": "✅" in line
                }
                for line in report_text.split("\n") 
                if line.startswith("•") and "(" in line
            ]
        }
    
    views = report_data.get("view_list", [])
    
    # Apply filters
    if view_type:
        views = [v for v in views if v["type"] == view_type]
    
    if exportable is not None:
        views = [v for v in views if v["exportable"] == exportable]
    
    return views

def main():
    parser = argparse.ArgumentParser(description="RevitViewExtractor - Upload and Process")
    parser.add_argument("file", help="Path to Revit file")
    parser.add_argument("--type", help="Filter by view type")
    parser.add_argument("--exportable", action="store_true", help="Show only exportable views")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    
    args = parser.parse_args()
    
    # Get token
    token = get_access_token()
    if not token:
        print("Failed to get access token")
        sys.exit(1)
    
    # Create bucket
    bucket_name = create_bucket(token)
    if not bucket_name:
        print("Failed to create bucket")
        sys.exit(1)
    
    # Upload file
    file_url = upload_file(token, bucket_name, args.file)
    if not file_url:
        print("Failed to upload file")
        sys.exit(1)
    
    # Process file
    views = process_revit_file(file_url, args.type, args.exportable)
    
    if views is None:
        print("Failed to extract views")
        sys.exit(1)
    
    # Output
    if args.json:
        print(json.dumps(views, indent=2))
    else:
        print(f"Found {len(views)} views:")
        for view in views:
            status = "✅ Exportable" if view["exportable"] else "❌ Non-Exportable"
            print(f"• {view['name']} ({view['type']}) - {status}")

if __name__ == "__main__":
    main()




