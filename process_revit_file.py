#!/usr/bin/env python3
"""
Process 100.rvt file using our uploaded RevitViewExtractor4 bundle
"""

import os
import json
import time
import requests
from config import CLIENT_ID, CLIENT_SECRET

class RevitProcessor:
    def __init__(self):
        self.access_token = None
        self.bucket_key = f"revit-test-{int(time.time())}"
        self.bundle_name = f"{CLIENT_ID}.RevitViewExtractor4+$LATEST"
        
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
            "policyKey": "transient"  # Files deleted after 24 hours
        }
        
        response = requests.post(url, headers=headers, json=data)
        if response.status_code in [200, 409]:  # 409 = already exists
            print(f"✓ Bucket ready: {self.bucket_key}")
            return True
        else:
            print(f"✗ Failed to create bucket: {response.text}")
            return False

    def upload_file(self, file_path, object_name):
        """Upload file to OSS bucket"""
        url = f"https://developer.api.autodesk.com/oss/v2/buckets/{self.bucket_key}/objects/{object_name}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/octet-stream"
        }
        
        print(f"Uploading {file_path} as {object_name}...")
        with open(file_path, 'rb') as f:
            response = requests.put(url, headers=headers, data=f)
        
        if response.status_code == 200:
            print(f"✓ File uploaded: {object_name}")
            return response.json()["objectId"]
        else:
            print(f"✗ Failed to upload file: {response.text}")
            return None

    def create_workitem(self, input_object_id):
        """Create and execute workitem"""
        url = "https://developer.api.autodesk.com/da/us-east/v3/workitems"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        # Create workitem data
        workitem_data = {
            "activityId": f"{self.bundle_name}",  # Use bundle directly as activity
            "arguments": {
                "inputFile": {
                    "verb": "get",
                    "url": f"https://developer.api.autodesk.com/oss/v2/buckets/{self.bucket_key}/objects/input.rvt"
                },
                "result": {
                    "verb": "put",
                    "url": f"https://developer.api.autodesk.com/oss/v2/buckets/{self.bucket_key}/objects/result.txt"
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
        """Wait for workitem to complete"""
        url = f"https://developer.api.autodesk.com/da/us-east/v3/workitems/{workitem_id}"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        print("Waiting for completion...")
        for i in range(60):  # Wait up to 10 minutes
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                status = response.json()["status"]
                print(f"Status: {status}")
                
                if status == "success":
                    print("✓ Workitem completed successfully!")
                    return True
                elif status == "failed":
                    print("✗ Workitem failed!")
                    print("Report:", response.json().get("reportUrl", "No report"))
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
        """Download result file"""
        url = f"https://developer.api.autodesk.com/oss/v2/buckets/{self.bucket_key}/objects/result.txt"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            result_content = response.text
            print("✓ Result downloaded:")
            print("=" * 50)
            print(result_content)
            print("=" * 50)
            
            # Save to local file
            with open("result.txt", "w") as f:
                f.write(result_content)
            print("✓ Result saved to result.txt")
            return True
        else:
            print(f"✗ Failed to download result: {response.text}")
            return False

    def process_file(self, file_path):
        """Main processing function"""
        print("=== Processing Revit File ===")
        print(f"File: {file_path}")
        print(f"Bundle: {self.bundle_name}")
        print()
        
        # Step 1: Get token
        if not self.get_access_token():
            return False
        
        # Step 2: Create bucket
        if not self.create_bucket():
            return False
        
        # Step 3: Upload file
        object_id = self.upload_file(file_path, "input.rvt")
        if not object_id:
            return False
        
        # Step 4: Create workitem (this will likely fail due to missing activity)
        print("\n⚠️  Note: This may fail because we need to create an Activity first")
        print("But let's try using the bundle directly...")
        
        workitem_id = self.create_workitem(object_id)
        if not workitem_id:
            print("\n💡 As expected, we need to create an Activity first.")
            print("But the file is uploaded and ready for processing!")
            return False
        
        # Step 5: Wait for completion
        if not self.wait_for_completion(workitem_id):
            return False
        
        # Step 6: Download result
        return self.download_result()

def main():
    processor = RevitProcessor()
    success = processor.process_file("100.rvt")
    
    if success:
        print("\n🎉 Processing completed successfully!")
    else:
        print("\n⚠️  Processing incomplete, but progress made:")
        print("- Bundle is uploaded and ready")
        print("- File can be uploaded to OSS")
        print("- Next step: Create proper Activity")

if __name__ == "__main__":
    main()



