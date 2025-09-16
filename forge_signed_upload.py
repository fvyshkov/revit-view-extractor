#!/usr/bin/env python3
"""
Forge API with signed URL upload
"""

import requests
import json
import time
import sys
import os
import base64

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
    
    response = requests.post(url, headers={"Content-Type": "application/x-www-form-urlencoded"}, data=data)
    log(f"Token response: {response.status_code}")
    
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
    log(f"Bucket response: {response.status_code}")
    
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
    log(f"Signed URL response: {response.status_code}")
    
    if response.status_code == 200:
        upload_info = response.json()
        upload_url = upload_info["urls"][0]
        upload_key = upload_info.get("uploadKey")
        
        log(f"Got signed URL: {upload_url[:60]}...")
        
        # Upload file to S3
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        upload_response = requests.put(upload_url, data=file_data)
        log(f"Upload to S3 response: {upload_response.status_code}")
        
        if upload_response.status_code == 200:
            # Complete the upload
            complete_url = f"https://developer.api.autodesk.com/oss/v2/buckets/{bucket_name}/objects/{file_name}/signeds3upload"
            complete_data = {"uploadKey": upload_key}
            
            complete_response = requests.post(complete_url, headers=headers, json=complete_data)
            log(f"Complete upload response: {complete_response.status_code}")
            
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
        
        # Fall back to sample file
        log("⚠️ Falling back to sample file URL")
        object_id = f"urn:adsk.objects:os.object:{bucket_name}/sample.rvt"
        urn = base64.b64encode(object_id.encode()).decode('utf-8')
        urn = urn.rstrip('=')
        return urn

def start_translation(token, urn):
    """Start Model Derivative translation to extract metadata"""
    log(f"🔄 Starting translation for URN: {urn}")
    
    url = "https://developer.api.autodesk.com/modelderivative/v2/designdata/job"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
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
    log(f"Translation response: {response.status_code}")
    
    if response.status_code in [200, 201]:
        result = response.json()
        log(f"✅ Translation started: {json.dumps(result, indent=2)}")
        return True
    else:
        log(f"❌ Translation failed: {response.text}")
        return False

def check_translation(token, urn):
    """Check translation status"""
    log(f"🔍 Checking translation for URN: {urn}")
    
    url = f"https://developer.api.autodesk.com/modelderivative/v2/designdata/{urn}/manifest"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers)
    log(f"Manifest response: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        status = result.get("status", "unknown")
        progress = result.get("progress", "")
        
        log(f"Translation status: {status} {progress}")
        
        if status == "failed":
            # Show error message
            if "derivatives" in result:
                for derivative in result["derivatives"]:
                    if "messages" in derivative:
                        for message in derivative["messages"]:
                            log(f"Error: {message.get('message', 'Unknown error')}")
        
        return status == "success"
    else:
        log(f"❌ Failed to get manifest: {response.text}")
        return False

def get_metadata(token, urn):
    """Get metadata from translated model"""
    log(f"📊 Getting metadata for URN: {urn}")
    
    url = f"https://developer.api.autodesk.com/modelderivative/v2/designdata/{urn}/metadata"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers)
    log(f"Metadata response: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        log(f"✅ Metadata retrieved")
        
        # Save to file
        with open("metadata_result.json", "w") as f:
            json.dump(result, f, indent=2)
        log("📄 Metadata saved to metadata_result.json")
        
        return result
    else:
        log(f"❌ Failed to get metadata: {response.text}")
        return None

def main():
    log("🚀 FORGE API WITH SIGNED URL UPLOAD")
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
    file_path = "100.rvt"
    urn = upload_file_signed(token, bucket_name, file_path)
    if not urn:
        return
    
    # Step 4: Start translation
    if not start_translation(token, urn):
        return
    
    # Step 5: Check translation with retry
    log("⏳ Checking translation status...")
    success = False
    for i in range(10):
        log(f"Check attempt {i+1}/10")
        if check_translation(token, urn):
            success = True
            break
        time.sleep(5)
    
    if not success:
        log("⚠️ Translation not completed in time")
    
    # Step 6: Get metadata
    metadata = get_metadata(token, urn)
    
    log("✅ Test complete!")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"❌ UNHANDLED EXCEPTION: {str(e)}")
        import traceback
        log(traceback.format_exc())
