#!/usr/bin/env python3
"""
Get list of views from 100.rvt using our cloud implementation
"""

import os
import json
import time
import requests
import base64
from config import CLIENT_ID, CLIENT_SECRET

class CloudViewExtractor:
    def __init__(self):
        self.access_token = None
        self.bucket_key = f"revit-views-{int(time.time())}"
        self.activity_id = f"{CLIENT_ID}.ExtractViewsActivity"
        
    def get_access_token(self):
        """Get access token"""
        url = "https://developer.api.autodesk.com/authentication/v2/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "client_credentials",
            "scope": "data:read data:write data:create bucket:create bucket:read code:all"
        }
        
        response = requests.post(url, headers=headers, data=data)
        if response.status_code == 200:
            self.access_token = response.json()["access_token"]
            print("✓ Access token obtained")
            return True
        else:
            print(f"✗ Failed to get token: {response.text}")
            return False

    def create_bucket(self):
        """Create OSS bucket"""
        url = "https://developer.api.autodesk.com/oss/v2/buckets"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        data = {
            "bucketKey": self.bucket_key,
            "policyKey": "transient"
        }
        
        response = requests.post(url, headers=headers, json=data)
        if response.status_code in [200, 409]:
            print(f"✓ Bucket created: {self.bucket_key}")
            return True
        else:
            print(f"✗ Failed to create bucket: {response.text}")
            return False

    def upload_file_chunked(self, file_path, object_name):
        """Upload large file in chunks"""
        print(f"Uploading {file_path} as {object_name}...")
        
        file_size = os.path.getsize(file_path)
        print(f"File size: {file_size / 1024 / 1024:.1f} MB")
        
        # For files > 100MB, use resumable upload
        if file_size > 100 * 1024 * 1024:
            return self.upload_large_file(file_path, object_name)
        else:
            return self.upload_small_file(file_path, object_name)
    
    def upload_small_file(self, file_path, object_name):
        """Upload small file directly"""
        url = f"https://developer.api.autodesk.com/oss/v2/buckets/{self.bucket_key}/objects/{object_name}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/octet-stream"
        }
        
        try:
            with open(file_path, 'rb') as f:
                response = requests.put(url, headers=headers, data=f, timeout=300)
            
            if response.status_code == 200:
                print(f"✓ File uploaded successfully")
                return response.json()["objectId"]
            else:
                print(f"✗ Upload failed: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"✗ Upload error: {e}")
            return None

    def upload_large_file(self, file_path, object_name):
        """Upload large file using resumable upload"""
        print("Using resumable upload for large file...")
        
        # Start resumable upload session
        url = f"https://developer.api.autodesk.com/oss/v2/buckets/{self.bucket_key}/objects/{object_name}/resumable"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, headers=headers, json={})
        if response.status_code != 200:
            print(f"✗ Failed to start resumable upload: {response.text}")
            return None
        
        upload_key = response.json()["uploadKey"]
        
        # Upload in 5MB chunks
        chunk_size = 5 * 1024 * 1024
        file_size = os.path.getsize(file_path)
        
        with open(file_path, 'rb') as f:
            chunk_index = 0
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                
                start_byte = chunk_index * chunk_size
                end_byte = min(start_byte + len(chunk) - 1, file_size - 1)
                
                print(f"Uploading chunk {chunk_index + 1} ({start_byte}-{end_byte}/{file_size})")
                
                chunk_url = f"https://developer.api.autodesk.com/oss/v2/buckets/{self.bucket_key}/objects/{object_name}/resumable"
                chunk_headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/octet-stream",
                    "Content-Range": f"bytes {start_byte}-{end_byte}/{file_size}",
                    "Session-Id": upload_key
                }
                
                chunk_response = requests.put(chunk_url, headers=chunk_headers, data=chunk)
                if chunk_response.status_code not in [200, 202]:
                    print(f"✗ Chunk upload failed: {chunk_response.text}")
                    return None
                
                chunk_index += 1
        
        print("✓ Large file uploaded successfully")
        return upload_key

    def create_workitem_simple(self, input_object_id):
        """Create workitem with simple format"""
        url = "https://developer.api.autodesk.com/da/us-east/v3/workitems"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        # Simple workitem format
        workitem_data = {
            "activityId": self.activity_id,
            "arguments": {
                "inputFile": {
                    "url": f"https://developer.api.autodesk.com/oss/v2/buckets/{self.bucket_key}/objects/input.rvt",
                    "verb": "get"
                },
                "result": {
                    "url": f"https://developer.api.autodesk.com/oss/v2/buckets/{self.bucket_key}/objects/result.txt",
                    "verb": "put"
                }
            }
        }
        
        print("Creating workitem...")
        print(f"Activity: {self.activity_id}")
        
        response = requests.post(url, headers=headers, json=workitem_data)
        
        if response.status_code == 200:
            workitem_id = response.json()["id"]
            print(f"✓ Workitem created: {workitem_id}")
            return workitem_id
        else:
            print(f"✗ Failed to create workitem: {response.text}")
            return None

    def wait_for_completion(self, workitem_id):
        """Wait for workitem completion"""
        url = f"https://developer.api.autodesk.com/da/us-east/v3/workitems/{workitem_id}"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        print("Processing file in the cloud...")
        print("This may take several minutes for large files...")
        
        for i in range(180):  # Wait up to 30 minutes
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                status = data["status"]
                
                if i % 12 == 0:  # Print every 2 minutes
                    print(f"Status: {status} (elapsed: {i*10}s)")
                
                if status == "success":
                    print("✓ Processing completed successfully!")
                    return True
                elif status == "failed":
                    print("✗ Processing failed!")
                    if "reportUrl" in data:
                        print(f"Report: {data['reportUrl']}")
                    return False
                elif status in ["pending", "inprogress"]:
                    time.sleep(10)
                    continue
            else:
                print(f"Error checking status: {response.text}")
                return False
        
        print("✗ Timeout waiting for completion")
        return False

    def download_result(self):
        """Download the result file"""
        url = f"https://developer.api.autodesk.com/oss/v2/buckets/{self.bucket_key}/objects/result.txt"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            result_content = response.text
            print("\n" + "="*60)
            print("🎉 VIEWS EXTRACTED FROM 100.RVT:")
            print("="*60)
            print(result_content)
            print("="*60)
            
            # Save result
            with open("views_list.txt", "w") as f:
                f.write(result_content)
            print("✓ Result saved to views_list.txt")
            return True
        else:
            print(f"✗ Failed to download result: {response.text}")
            return False

    def extract_views(self, file_path):
        """Main function to extract views"""
        print("🚀 EXTRACTING VIEWS FROM REVIT FILE")
        print("="*60)
        print(f"File: {file_path}")
        print(f"Size: {os.path.getsize(file_path) / 1024 / 1024:.1f} MB")
        print("="*60)
        
        # Step 1: Get token
        if not self.get_access_token():
            return False
        
        # Step 2: Create bucket
        if not self.create_bucket():
            return False
        
        # Step 3: Upload file
        object_id = self.upload_file_chunked(file_path, "input.rvt")
        if not object_id:
            return False
        
        # Step 4: Create workitem
        workitem_id = self.create_workitem_simple(object_id)
        if not workitem_id:
            return False
        
        # Step 5: Wait for completion
        if not self.wait_for_completion(workitem_id):
            return False
        
        # Step 6: Download result
        return self.download_result()

def main():
    file_path = "100.rvt"
    
    if not os.path.exists(file_path):
        print(f"✗ File not found: {file_path}")
        return
    
    extractor = CloudViewExtractor()
    success = extractor.extract_views(file_path)
    
    if success:
        print("\n🎉 SUCCESS!")
        print("Views list extracted from your Revit file!")
        print("Check views_list.txt for the complete list")
    else:
        print("\n❌ FAILED")
        print("Check the error messages above")

if __name__ == "__main__":
    main()
