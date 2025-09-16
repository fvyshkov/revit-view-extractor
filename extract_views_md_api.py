#!/usr/bin/env python3
"""
Extract Revit Views using Model Derivative API
This script uploads a Revit file, translates it, and extracts view names
"""

import requests
import json
import time
import os
import base64
import sys

# Credentials from force_our_activity.sh
CLIENT_ID = "rfZQOaSWaILCGB3wRheGj994IH1qCoy9f0tZiPrGs117K48n"
CLIENT_SECRET = "FRAmVrbnXcyp72GUcgmwANOk3lnil0ELRJGmPCzgebvr8DVEnGaNmk1b2ed9Gatq"

def log(message):
    """Print with timestamp and flush immediately"""
    timestamp = time.strftime("%H:%M:%S", time.localtime())
    print(f"[{timestamp}] {message}", flush=True)

def get_access_token():
    """Get 2-legged OAuth token"""
    log("🔑 Getting access token...")
    url = "https://developer.api.autodesk.com/authentication/v2/token"
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials",
        "scope": "data:read data:write bucket:create bucket:read viewables:read"
    }
    
    response = requests.post(url, headers={"Content-Type": "application/x-www-form-urlencoded"}, data=data)
    
    if response.status_code == 200:
        result = response.json()
        log(f"✅ Token obtained (expires in {result.get('expires_in', 0)} seconds)")
        return result["access_token"]
    else:
        log(f"❌ Failed to get token: {response.text}")
        return None

def create_bucket(token):
    """Create bucket for file storage"""
    bucket_name = f"revitviews{int(time.time())}"
    log(f"🪣 Creating bucket: {bucket_name}")
    
    url = "https://developer.api.autodesk.com/oss/v2/buckets"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {
        "bucketKey": bucket_name,
        "policyKey": "transient"
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code in [200, 409]:
        log(f"✅ Bucket ready: {bucket_name}")
        return bucket_name
    else:
        log(f"❌ Bucket creation failed: {response.text}")
        return None

def upload_file_signed(token, bucket_name, file_path):
    """Upload file using signed URL approach"""
    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)
    
    log(f"📤 Uploading file: {file_name} to bucket: {bucket_name}")
    log(f"File size: {file_size} bytes")
    
    # Get signed URL
    url = f"https://developer.api.autodesk.com/oss/v2/buckets/{bucket_name}/objects/{file_name}/signeds3upload"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        upload_info = response.json()
        upload_url = upload_info["urls"][0]
        upload_key = upload_info.get("uploadKey")
        
        log(f"Got signed URL: {upload_url[:60]}...")
        
        # Upload file to S3
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        upload_response = requests.put(upload_url, data=file_data)
        
        if upload_response.status_code == 200:
            # Complete the upload
            complete_url = f"https://developer.api.autodesk.com/oss/v2/buckets/{bucket_name}/objects/{file_name}/signeds3upload"
            complete_data = {"uploadKey": upload_key}
            
            complete_response = requests.post(complete_url, headers=headers, json=complete_data)
            
            if complete_response.status_code == 200:
                result = complete_response.json()
                object_id = result["objectId"]
                log(f"✅ File uploaded: {object_id}")
                
                # Create URN
                urn = base64.b64encode(object_id.encode()).decode('utf-8')
                # Remove padding
                urn = urn.rstrip('=')
                return urn
            else:
                log(f"❌ Complete upload failed: {complete_response.text}")
        else:
            log(f"❌ Upload to S3 failed: {upload_response.text}")
    else:
        log(f"❌ Failed to get signed URL: {response.text}")
    
    return None

def start_translation(token, urn):
    """Start Model Derivative translation to extract metadata"""
    log(f"🔄 Starting translation for URN: {urn}")
    
    url = "https://developer.api.autodesk.com/modelderivative/v2/designdata/job"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Request both SVF and metadata extraction
    data = {
        "input": {
            "urn": urn
        },
        "output": {
            "formats": [
                {
                    "type": "svf",
                    "views": ["2d", "3d"]
                }
            ]
        }
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code in [200, 201]:
        result = response.json()
        log(f"✅ Translation started")
        return True
    else:
        log(f"❌ Translation failed: {response.text}")
        return False

def wait_for_translation(token, urn, max_wait_minutes=10):
    """Wait for translation to complete"""
    log(f"⏳ Waiting for translation to complete (up to {max_wait_minutes} minutes)...")
    
    url = f"https://developer.api.autodesk.com/modelderivative/v2/designdata/{urn}/manifest"
    headers = {"Authorization": f"Bearer {token}"}
    
    start_time = time.time()
    max_wait_seconds = max_wait_minutes * 60
    
    while time.time() - start_time < max_wait_seconds:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            status = result.get("status", "unknown")
            progress = result.get("progress", "")
            
            log(f"Status: {status} {progress}")
            
            if status == "success":
                log("✅ Translation complete!")
                return True
            elif status == "failed":
                log("❌ Translation failed")
                if "derivatives" in result:
                    for derivative in result["derivatives"]:
                        if "messages" in derivative:
                            for message in derivative["messages"]:
                                log(f"Error: {message.get('message', 'Unknown error')}")
                return False
            
            # Wait before checking again
            time.sleep(10)
        else:
            log(f"❌ Failed to get manifest: {response.text}")
            return False
    
    log("⏱️ Translation timed out")
    return False

def get_metadata(token, urn):
    """Get metadata from translated model"""
    log(f"📊 Getting metadata...")
    
    url = f"https://developer.api.autodesk.com/modelderivative/v2/designdata/{urn}/metadata"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        log(f"✅ Metadata retrieved")
        return result
    else:
        log(f"❌ Failed to get metadata: {response.text}")
        return None

def get_model_views(token, urn, guid):
    """Get views from the model"""
    log(f"🔍 Getting model views for GUID: {guid}")
    
    # Get properties
    url = f"https://developer.api.autodesk.com/modelderivative/v2/designdata/{urn}/metadata/{guid}/properties"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        log(f"✅ Properties retrieved")
        return result
    else:
        log(f"❌ Failed to get properties: {response.text}")
        return None

def extract_views(metadata, properties):
    """Extract view information from metadata and properties"""
    views = []
    
    if not metadata or not properties:
        return views
    
    # First, get all objects that might be views
    view_objects = []
    
    # Look for view-related objects in properties
    if "data" in properties and "collection" in properties["data"]:
        collection = properties["data"]["collection"]
        
        for item in collection:
            # Check if this is a view
            category = item.get("name", "").split("[")[0].strip()
            
            if "View" in category or "view" in category.lower():
                view_objects.append(item)
    
    # Process view objects
    for view in view_objects:
        view_name = view.get("name", "Unknown").split("[")[0].strip()
        view_type = "Unknown"
        view_id = view.get("objectid", "")
        
        # Try to determine view type
        props = view.get("properties", {})
        for category, properties in props.items():
            if "ViewType" in properties:
                view_type = properties["ViewType"]
                break
        
        views.append({
            "name": view_name,
            "type": view_type,
            "id": view_id
        })
    
    return views

def main():
    if len(sys.argv) < 2:
        log("❌ Please provide a Revit file path")
        log("Usage: python extract_views_md_api.py <revit_file_path>")
        return
    
    file_path = sys.argv[1]
    if not os.path.exists(file_path):
        log(f"❌ File not found: {file_path}")
        return
    
    log("🚀 REVIT VIEW EXTRACTOR (Model Derivative API)")
    log("=" * 50)
    
    # Step 1: Get token
    token = get_access_token()
    if not token:
        return
    
    # Step 2: Create bucket
    bucket_name = create_bucket(token)
    if not bucket_name:
        return
    
    # Step 3: Upload file
    urn = upload_file_signed(token, bucket_name, file_path)
    if not urn:
        return
    
    # Step 4: Start translation
    if not start_translation(token, urn):
        return
    
    # Step 5: Wait for translation
    if not wait_for_translation(token, urn):
        return
    
    # Step 6: Get metadata
    metadata = get_metadata(token, urn)
    if not metadata:
        return
    
    # Step 7: Get model views
    guid = None
    if "data" in metadata and "metadata" in metadata["data"]:
        for item in metadata["data"]["metadata"]:
            if item.get("role") == "3d":
                guid = item.get("guid")
                break
    
    if not guid:
        log("❌ Could not find model GUID")
        return
    
    properties = get_model_views(token, urn, guid)
    if not properties:
        return
    
    # Step 8: Extract views
    views = extract_views(metadata, properties)
    
    # Step 9: Display results
    log(f"\n📋 EXTRACTED VIEWS: {len(views)}")
    log("=" * 50)
    
    for i, view in enumerate(views):
        print(f"{i+1}. {view['name']} ({view['type']})")
    
    # Save results
    result_file = "views_data.json"
    with open(result_file, "w") as f:
        json.dump(views, f, indent=2)
    
    log(f"\n✅ View data saved to {result_file}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"❌ ERROR: {str(e)}")
        import traceback
        log(traceback.format_exc())
