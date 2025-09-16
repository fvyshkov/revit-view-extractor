#!/usr/bin/env python3
"""
Alternative approach using Forge Model Derivative API
This API can extract metadata from Revit files
"""

import requests
import json
import base64
import time

# Using the new credentials
CLIENT_ID = "H3nGeDHGOZINPwBBltL0dAtUnJKG6jQrdShz1bOggsAswmzU"
CLIENT_SECRET = "ZW2ViZrysoHleclZRBR5PdgMO8KeWbwKMmtvGLL4OxGAwkuDICaSG8h3Np02fhUO"

def get_access_token():
    """Get 2-legged OAuth token"""
    url = "https://developer.api.autodesk.com/authentication/v2/token"
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials",
        "scope": "data:read data:write data:create bucket:create bucket:read viewables:read"
    }
    response = requests.post(url, headers={"Content-Type": "application/x-www-form-urlencoded"}, data=data)
    
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Failed to get token: {response.text}")
        return None

def create_bucket(token):
    """Create bucket for file storage"""
    bucket_name = f"revitviews{int(time.time())}"
    
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
        print(f"✅ Bucket ready: {bucket_name}")
        return bucket_name
    else:
        print(f"❌ Bucket creation failed: {response.text}")
        return None

def upload_file_signed(token, bucket_name, file_path):
    """Upload file using signed URL approach"""
    import os
    
    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)
    
    # Get signed upload URL
    url = f"https://developer.api.autodesk.com/oss/v2/buckets/{bucket_name}/objects/{file_name}/signeds3upload"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # First, check if we need multi-part upload
    if file_size > 5 * 1024 * 1024:  # 5MB
        # For large files, use multi-part upload
        parts = 1  # Simplified for now
        
    # Get signed URL
    params = {"minutesExpiration": 60}
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        upload_info = response.json()
        
        # Upload to S3
        with open(file_path, 'rb') as f:
            upload_response = requests.put(
                upload_info["urls"][0], 
                data=f.read(),
                headers={"Content-Type": "application/octet-stream"}
            )
        
        if upload_response.status_code == 200:
            # Finalize upload
            finalize_url = f"https://developer.api.autodesk.com/oss/v2/buckets/{bucket_name}/objects/{file_name}/signeds3upload"
            finalize_data = {
                "uploadKey": upload_info["uploadKey"]
            }
            
            finalize_response = requests.post(finalize_url, headers=headers, json=finalize_data)
            
            if finalize_response.status_code == 200:
                result = finalize_response.json()
                object_id = result["objectId"]
                print(f"✅ File uploaded: {object_id}")
                
                # Create URN
                urn = base64.b64encode(object_id.encode()).decode('utf-8')
                # Remove padding
                urn = urn.rstrip('=')
                return urn
            else:
                print(f"❌ Finalize failed: {finalize_response.text}")
    else:
        print(f"❌ Failed to get signed URL: {response.text}")
    
    return None

def start_translation(token, urn):
    """Start Model Derivative translation to extract metadata"""
    url = "https://developer.api.autodesk.com/modelderivative/v2/designdata/job"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "x-ads-force": "true"  # Force re-translation
    }
    
    # Request metadata extraction
    data = {
        "input": {
            "urn": urn
        },
        "output": {
            "formats": [
                {
                    "type": "svf2",
                    "views": ["2d", "3d"],
                    "advanced": {
                        "generateMasterViews": True
                    }
                }
            ],
            "destination": {
                "region": "us"
            }
        }
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code in [200, 201]:
        print("✅ Translation started")
        return True
    else:
        print(f"❌ Translation failed: {response.text}")
        return False

def get_metadata(token, urn):
    """Get metadata from translated model"""
    # Check translation status first
    manifest_url = f"https://developer.api.autodesk.com/modelderivative/v2/designdata/{urn}/manifest"
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n⏳ Waiting for translation...")
    for i in range(60):  # Wait up to 5 minutes
        response = requests.get(manifest_url, headers=headers)
        
        if response.status_code == 200:
            manifest = response.json()
            status = manifest.get("status", "")
            progress = manifest.get("progress", "")
            
            print(f"[{i*5}s] Status: {status} {progress}")
            
            if status == "success":
                print("✅ Translation complete!")
                
                # Get metadata
                metadata_url = f"https://developer.api.autodesk.com/modelderivative/v2/designdata/{urn}/metadata"
                meta_response = requests.get(metadata_url, headers=headers)
                
                if meta_response.status_code == 200:
                    metadata = meta_response.json()
                    
                    # Get object tree for the first viewable
                    if metadata.get("data", {}).get("metadata"):
                        guid = metadata["data"]["metadata"][0]["guid"]
                        
                        # Get properties
                        props_url = f"https://developer.api.autodesk.com/modelderivative/v2/designdata/{urn}/metadata/{guid}/properties"
                        props_response = requests.get(props_url, headers=headers)
                        
                        if props_response.status_code == 200:
                            return props_response.json()
                
                return metadata
            elif status == "failed":
                print("❌ Translation failed")
                return None
        
        time.sleep(5)
    
    print("⏱️ Translation timeout")
    return None

def extract_views_from_metadata(metadata):
    """Extract view information from metadata"""
    views = []
    
    if metadata and "data" in metadata:
        collection = metadata["data"].get("collection", [])
        
        for item in collection:
            # Look for view-related properties
            props = item.get("properties", {})
            
            # Check different property categories
            for category, properties in props.items():
                if "View" in category or "view" in category.lower():
                    view_info = {
                        "objectid": item.get("objectid"),
                        "name": item.get("name", "Unknown"),
                        "category": category,
                        "properties": properties
                    }
                    views.append(view_info)
    
    return views

def main():
    print("🚀 FORGE MODEL DERIVATIVE API APPROACH")
    print("=" * 60)
    print("This uses a different API that might work with 48-char CLIENT_ID")
    
    # Step 1: Get token
    print("\n1. Getting access token...")
    token = get_access_token()
    if not token:
        return
    print("✅ Token obtained")
    
    # Step 2: Create bucket
    print("\n2. Creating bucket...")
    bucket_name = create_bucket(token)
    if not bucket_name:
        return
    
    # Step 3: Upload file
    print("\n3. Uploading Revit file...")
    urn = upload_file_signed(token, bucket_name, "100.rvt")
    if not urn:
        print("❌ Upload failed")
        return
    
    print(f"✅ File URN: {urn}")
    
    # Step 4: Start translation
    print("\n4. Starting Model Derivative translation...")
    if not start_translation(token, urn):
        return
    
    # Step 5: Get metadata
    print("\n5. Extracting metadata...")
    metadata = get_metadata(token, urn)
    
    if metadata:
        # Extract views
        views = extract_views_from_metadata(metadata)
        
        print(f"\n✅ Found {len(views)} view-related objects")
        
        if views:
            print("\n📋 VIEWS FOUND:")
            print("=" * 60)
            for view in views[:10]:  # Show first 10
                print(f"Name: {view['name']}")
                print(f"Category: {view['category']}")
                print(f"ID: {view['objectid']}")
                print("-" * 40)
        
        # Save full metadata
        with open("metadata_result.json", "w") as f:
            json.dump(metadata, f, indent=2)
        print("\n📄 Full metadata saved to metadata_result.json")
    else:
        print("❌ Failed to get metadata")

if __name__ == "__main__":
    main()
