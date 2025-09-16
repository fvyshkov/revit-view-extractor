#!/usr/bin/env python3
"""
RevitViewExtractor - Export View Utility

Allows exporting a specific view from a Revit file.

Usage:
    python export_view.py <path_to_revit_file> <view_name> [options]

Options:
    --type TYPE       Specify view type (optional, for disambiguation)
    --output PATH     Specify output path for exported view
    --format FORMAT   Export format (png, jpg, pdf) - default: png
"""

import sys
import os
import argparse
from config import CLIENT_ID, CLIENT_SECRET

def get_access_token():
    """Get Autodesk access token"""
    import requests
    url = "https://developer.api.autodesk.com/authentication/v2/token"
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials",
        "scope": "code:all"
    }
    response = requests.post(url, headers={"Content-Type": "application/x-www-form-urlencoded"}, data=data)
    return response.json()["access_token"] if response.status_code == 200 else None

def export_view(file_path, view_name, view_type=None, output_path=None, format='png'):
    """Export a specific view from Revit file"""
    token = get_access_token()
    
    # For now, use a working activity to test the system
    workitem_data = {
        "activityId": "Autodesk.Nop+Latest",
        "arguments": {}
    }
    
    # Send workitem to process file
    import requests
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
    print(f"✅ Workitem created: {workitem_id}")
    print(f"📝 Note: Mock export for view '{view_name}' as {format}")
    
    # Create a mock exported file
    if not output_path:
        output_path = os.path.join(
            os.path.dirname(file_path) if file_path != "100.rvt" else ".", 
            f"{view_name.replace(' ', '_')}.{format}"
        )
    
    # Create a simple mock file
    with open(output_path, 'w') as f:
        f.write(f"Mock export of view '{view_name}' in {format} format\n")
        f.write(f"Workitem ID: {workitem_id}\n")
        f.write("Real export functionality coming soon!\n")
    
    print(f"✅ Mock view exported to: {output_path}")
    return output_path

def main():
    parser = argparse.ArgumentParser(description="RevitViewExtractor - Export View")
    parser.add_argument("file", help="Path to Revit file")
    parser.add_argument("view_name", help="Name of the view to export")
    parser.add_argument("--type", help="View type (optional)")
    parser.add_argument("--output", help="Output file path")
    parser.add_argument("--format", choices=['png', 'jpg', 'pdf'], default='png', help="Export format")
    
    args = parser.parse_args()
    
    # Export view
    export_view(
        args.file, 
        args.view_name, 
        view_type=args.type, 
        output_path=args.output, 
        format=args.format
    )

if __name__ == "__main__":
    main()
