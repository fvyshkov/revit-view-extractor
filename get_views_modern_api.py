#!/usr/bin/env python3
"""
Get views using modern OSS API with signed URLs
"""

import os
import json
import time
import requests
from config import CLIENT_ID, CLIENT_SECRET

class ModernCloudExtractor:
    def __init__(self):
        self.access_token = None
        self.bucket_key = f"revit-modern-{int(time.time())}"
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

    def get_upload_url(self, object_name):
        """Get signed upload URL"""
        url = f"https://developer.api.autodesk.com/oss/v2/buckets/{self.bucket_key}/objects/{object_name}/signeds3upload"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        # Send empty JSON body
        response = requests.post(url, headers=headers, json={})
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"✗ Failed to get upload URL: {response.text}")
            return None

    def upload_with_signed_url(self, file_path, object_name):
        """Upload file using signed URL"""
        print(f"Getting signed URL for {object_name}...")
        
        upload_data = self.get_upload_url(object_name)
        if not upload_data:
            return False
        
        upload_url = upload_data["uploadUrl"]
        print(f"✓ Got signed URL")
        
        print(f"Uploading {file_path}...")
        with open(file_path, 'rb') as f:
            response = requests.put(upload_url, data=f)
        
        if response.status_code == 200:
            print(f"✓ File uploaded successfully")
            return True
        else:
            print(f"✗ Upload failed: {response.status_code} - {response.text}")
            return False

    def get_download_url(self, object_name):
        """Get signed download URL"""
        url = f"https://developer.api.autodesk.com/oss/v2/buckets/{self.bucket_key}/objects/{object_name}/signeds3download"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, headers=headers, json={})
        
        if response.status_code == 200:
            return response.json()["url"]
        else:
            print(f"✗ Failed to get download URL: {response.text}")
            return None

    def create_workitem(self):
        """Create workitem with signed URLs"""
        url = "https://developer.api.autodesk.com/da/us-east/v3/workitems"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        # Get signed URLs for input and output
        input_url = self.get_download_url("input.rvt")
        output_upload_data = self.get_upload_url("result.txt")
        
        if not input_url or not output_upload_data:
            print("✗ Failed to get signed URLs for workitem")
            return None
        
        output_url = output_upload_data["uploadUrl"]
        
        workitem_data = {
            "activityId": self.activity_id,
            "arguments": {
                "inputFile": {
                    "url": input_url,
                    "verb": "get"
                },
                "result": {
                    "url": output_url,
                    "verb": "put"
                }
            }
        }
        
        print("Creating workitem...")
        response = requests.post(url, headers=headers, json=workitem_data)
        
        if response.status_code == 200:
            workitem_id = response.json()["id"]
            print(f"✓ Workitem created: {workitem_id}")
            return workitem_id
        else:
            print(f"✗ Failed to create workitem: {response.text}")
            return None

    def wait_for_completion(self, workitem_id):
        """Wait for completion"""
        url = f"https://developer.api.autodesk.com/da/us-east/v3/workitems/{workitem_id}"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        print("Processing in the cloud...")
        
        for i in range(120):
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                status = data["status"]
                
                if i % 6 == 0:
                    print(f"Status: {status} (elapsed: {i*10}s)")
                
                if status == "success":
                    print("✓ Processing completed!")
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
                print(f"Error: {response.text}")
                return False
        
        print("✗ Timeout")
        return False

    def download_result(self):
        """Download result"""
        download_url = self.get_download_url("result.txt")
        if not download_url:
            return False
        
        response = requests.get(download_url)
        if response.status_code == 200:
            result = response.text
            print("\n" + "="*60)
            print("🎉 VIEWS FROM 100.RVT:")
            print("="*60)
            print(result)
            print("="*60)
            
            with open("views_extracted.txt", "w") as f:
                f.write(result)
            print("✓ Saved to views_extracted.txt")
            return True
        else:
            print(f"✗ Download failed: {response.text}")
            return False

    def extract_views(self, file_path):
        """Main extraction function"""
        print("🚀 MODERN API VIEW EXTRACTION")
        print("="*50)
        
        if not self.get_access_token():
            return False
        
        if not self.create_bucket():
            return False
        
        if not self.upload_with_signed_url(file_path, "input.rvt"):
            return False
        
        workitem_id = self.create_workitem()
        if not workitem_id:
            return False
        
        if not self.wait_for_completion(workitem_id):
            return False
        
        return self.download_result()

def main():
    if not os.path.exists("100.rvt"):
        print("✗ 100.rvt not found")
        return
    
    extractor = ModernCloudExtractor()
    success = extractor.extract_views("100.rvt")
    
    if success:
        print("\n🎉 SUCCESS! Views extracted!")
    else:
        print("\n❌ Failed to extract views")

if __name__ == "__main__":
    main()



