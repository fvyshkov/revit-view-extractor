#!/usr/bin/env python3
"""
Debug version with more logging
"""

import requests
import json
import time
import sys

# Using credentials from force_our_activity.sh
CLIENT_ID = "rfZQOaSWaILCGB3wRheGj994IH1qCoy9f0tZiPrGs117K48n"
CLIENT_SECRET = "FRAmVrbnXcyp72GUcgmwANOk3lnil0ELRJGmPCzgebvr8DVEnGaNmk1b2ed9Gatq"

def log(message):
    """Print with timestamp and flush immediately"""
    timestamp = time.strftime("%H:%M:%S", time.localtime())
    print(f"[{timestamp}] {message}", flush=True)

def get_access_token():
    """Get 2-legged OAuth token"""
    log("🔑 Requesting access token...")
    url = "https://developer.api.autodesk.com/authentication/v2/token"
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials",
        "scope": "data:read data:write bucket:create bucket:read viewables:read"
    }
    
    try:
        response = requests.post(url, headers={"Content-Type": "application/x-www-form-urlencoded"}, data=data)
        log(f"Token response: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            log(f"✅ Token obtained (expires in {result.get('expires_in', 0)} seconds)")
            return result["access_token"]
        else:
            log(f"❌ Failed to get token: {response.text}")
            return None
    except Exception as e:
        log(f"❌ Exception in get_token: {str(e)}")
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
    
    try:
        response = requests.post(url, headers=headers, json=data)
        log(f"Bucket response: {response.status_code}")
        
        if response.status_code in [200, 409]:
            log(f"✅ Bucket ready: {bucket_name}")
            return bucket_name
        else:
            log(f"❌ Bucket creation failed: {response.text}")
            return None
    except Exception as e:
        log(f"❌ Exception in create_bucket: {str(e)}")
        return None

def upload_file_direct(token, bucket_name, file_path):
    """Upload file directly to OSS"""
    import os
    
    file_name = os.path.basename(file_path)
    log(f"📤 Uploading file: {file_name} to bucket: {bucket_name}")
    
    url = f"https://developer.api.autodesk.com/oss/v2/buckets/{bucket_name}/objects/{file_name}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/octet-stream"
    }
    
    try:
        with open(file_path, 'rb') as f:
            file_data = f.read()
            
        log(f"File size: {len(file_data)} bytes")
        headers["Content-Length"] = str(len(file_data))
        
        response = requests.put(url, headers=headers, data=file_data)
        log(f"Upload response: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            object_id = result["objectId"]
            log(f"✅ File uploaded: {object_id}")
            
            # Create base64 URN
            import base64
            urn = base64.b64encode(object_id.encode()).decode('utf-8')
            return urn
        else:
            log(f"❌ Upload failed: {response.text}")
            return None
    except Exception as e:
        log(f"❌ Exception in upload_file: {str(e)}")
        return None

def main():
    log("🚀 DEBUG FORGE API TEST")
    log("=" * 40)
    
    # Step 1: Get token
    token = get_access_token()
    if not token:
        return
    
    # Step 2: Create bucket
    bucket_name = create_bucket(token)
    if not bucket_name:
        return
    
    # Step 3: Upload file
    log("\n3. Testing file upload...")
    
    # First check if file exists
    import os
    file_path = "100.rvt"
    if not os.path.exists(file_path):
        log(f"❌ File not found: {file_path}")
        log(f"Current directory: {os.getcwd()}")
        log(f"Files in directory: {os.listdir('.')}")
        return
    
    urn = upload_file_direct(token, bucket_name, file_path)
    if not urn:
        return
    
    log(f"✅ Test complete! URN: {urn}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"❌ UNHANDLED EXCEPTION: {str(e)}")
        import traceback
        log(traceback.format_exc())
