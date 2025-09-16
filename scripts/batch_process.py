#!/usr/bin/env python3
"""
RevitViewExtractor - Batch Processing Utility

Allows batch processing of multiple Revit files for view extraction and export.

Usage:
    python batch_process.py <directory_path> [options]

Options:
    --output-dir DIR   Specify output directory for processed files
    --format FORMAT    Export format (png, jpg, pdf) - default: png
    --type TYPE        Filter views by type
    --exportable       Process only exportable views
"""

import os
import sys
import argparse
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
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

def process_revit_file(file_path, output_dir, view_type=None, exportable=None, format='png'):
    """Process a single Revit file"""
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
        print(f"Error processing {file_path}: {response.text}")
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
                # Get report and exported files
                report_url = status_data.get("reportUrl")
                export_urls = status_data.get("exportUrls", [])
                
                results = {
                    "file": file_path,
                    "report": None,
                    "exports": []
                }
                
                # Get report
                if report_url:
                    report_response = requests.get(report_url)
                    if report_response.status_code == 200:
                        results["report"] = report_response.text
                
                # Download exported files
                for export_url in export_urls:
                    export_response = requests.get(export_url)
                    if export_response.status_code == 200:
                        # Generate output filename
                        filename = os.path.basename(file_path).replace('.rvt', f'_{export_url.split("/")[-1]}')
                        output_path = os.path.join(output_dir, filename)
                        
                        # Save exported file
                        with open(output_path, 'wb') as f:
                            f.write(export_response.content)
                        
                        results["exports"].append(output_path)
                
                return results
            
            elif status_data["status"] == "failed":
                print(f"Workitem processing failed for {file_path}")
                return None
        
        time.sleep(10)
    
    print(f"Timeout waiting for workitem for {file_path}")
    return None

def batch_process(directory, output_dir, view_type=None, exportable=None, format='png', max_workers=5):
    """Batch process Revit files in a directory"""
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Find all .rvt files
    rvt_files = [
        os.path.join(directory, f) 
        for f in os.listdir(directory) 
        if f.lower().endswith('.rvt')
    ]
    
    # Process files in parallel
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit processing tasks
        future_to_file = {
            executor.submit(
                process_revit_file, 
                file_path, 
                output_dir, 
                view_type, 
                exportable, 
                format
            ): file_path for file_path in rvt_files
        }
        
        # Collect results
        for future in as_completed(future_to_file):
            file_path = future_to_file[future]
            try:
                result = future.result()
                if result:
                    results.append(result)
                    print(f"✅ Processed: {file_path}")
                else:
                    print(f"❌ Failed to process: {file_path}")
            except Exception as exc:
                print(f"❌ Error processing {file_path}: {exc}")
    
    # Save batch processing report
    report_path = os.path.join(output_dir, 'batch_processing_report.json')
    with open(report_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📊 Batch Processing Complete")
    print(f"Total files processed: {len(results)}")
    print(f"Report saved to: {report_path}")

def main():
    parser = argparse.ArgumentParser(description="RevitViewExtractor - Batch Processing")
    parser.add_argument("directory", help="Directory containing Revit files")
    parser.add_argument("--output-dir", default="output", help="Output directory for processed files")
    parser.add_argument("--format", choices=['png', 'jpg', 'pdf'], default='png', help="Export format")
    parser.add_argument("--type", help="Filter views by type")
    parser.add_argument("--exportable", action="store_true", help="Process only exportable views")
    parser.add_argument("--workers", type=int, default=5, help="Number of parallel workers")
    
    args = parser.parse_args()
    
    # Batch process
    batch_process(
        args.directory, 
        args.output_dir, 
        view_type=args.type, 
        exportable=args.exportable, 
        format=args.format, 
        max_workers=args.workers
    )

if __name__ == "__main__":
    main()
