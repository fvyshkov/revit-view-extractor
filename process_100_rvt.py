#!/usr/bin/env python3
"""
Process 100.rvt file using our RevitViewExtractor4 Activity
"""

import os
import json
import time
import requests
from config import CLIENT_ID, CLIENT_SECRET

class RevitFileProcessor:
    def __init__(self):
        self.access_token = None
        self.bucket_key = f"revit-process-{int(time.time())}"
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
        """Create OSS bucket for file storage"""
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

    def get_signed_url(self, object_name, access="write"):
        """Get signed URL for file upload/download"""
        url = f"https://developer.api.autodesk.com/oss/v2/buckets/{self.bucket_key}/objects/{object_name}/signeds3upload"
        if access == "read":
            url = f"https://developer.api.autodesk.com/oss/v2/buckets/{self.bucket_key}/objects/{object_name}/signeds3download"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"✗ Failed to get signed URL: {response.text}")
            return None

    def upload_file_with_signed_url(self, file_path, object_name):
        """Upload file using signed URL"""
        print(f"Uploading {file_path} as {object_name}...")
        
        # Get signed URL for upload
        signed_data = self.get_signed_url(object_name, "write")
        if not signed_data:
            return False
        
        upload_url = signed_data["uploadUrl"]
        
        # Upload file
        with open(file_path, 'rb') as f:
            response = requests.put(upload_url, data=f)
        
        if response.status_code == 200:
            print(f"✓ File uploaded successfully: {object_name}")
            return True
        else:
            print(f"✗ Failed to upload file: {response.status_code} - {response.text}")
            return False

    def create_workitem(self):
        """Create workitem to process the file"""
        url = "https://developer.api.autodesk.com/da/us-east/v3/workitems"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        # Get signed URLs for input and output
        input_signed = self.get_signed_url("input.rvt", "read")
        output_signed = self.get_signed_url("result.txt", "write")
        
        if not input_signed or not output_signed:
            print("✗ Failed to get signed URLs")
            return None
        
        workitem_data = {
            "activityId": self.activity_id,
            "arguments": {
                "inputFile": {
                    "verb": "get",
                    "url": input_signed["url"]
                },
                "result": {
                    "verb": "put", 
                    "url": output_signed["uploadUrl"]
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
        """Wait for workitem to complete"""
        url = f"https://developer.api.autodesk.com/da/us-east/v3/workitems/{workitem_id}"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        print("Waiting for processing to complete...")
        print("This may take a few minutes...")
        
        for i in range(120):  # Wait up to 20 minutes
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                status = data["status"]
                
                if i % 6 == 0:  # Print status every minute
                    print(f"Status: {status} (elapsed: {i*10}s)")
                
                if status == "success":
                    print("✓ Processing completed successfully!")
                    return True
                elif status == "failed":
                    print("✗ Processing failed!")
                    if "reportUrl" in data:
                        print(f"Report URL: {data['reportUrl']}")
                    return False
                elif status in ["pending", "inprogress"]:
                    time.sleep(10)
                    continue
                else:
                    print(f"Unknown status: {status}")
                    return False
            else:
                print(f"Error checking status: {response.text}")
                return False
        
        print("✗ Timeout waiting for completion")
        return False

    def download_result(self):
        """Download the result file"""
        # Get signed URL for download
        signed_data = self.get_signed_url("result.txt", "read")
        if not signed_data:
            return False
        
        download_url = signed_data["url"]
        
        response = requests.get(download_url)
        if response.status_code == 200:
            result_content = response.text
            print("✓ Result downloaded!")
            print("=" * 60)
            print("RESULT FROM REVIT VIEW EXTRACTOR:")
            print("=" * 60)
            print(result_content)
            print("=" * 60)
            
            # Save to local file
            with open("100_rvt_result.txt", "w") as f:
                f.write(result_content)
            print("✓ Result saved to 100_rvt_result.txt")
            return True
        else:
            print(f"✗ Failed to download result: {response.text}")
            return False

    def process_file(self, file_path):
        """Main processing function"""
        print("🚀 PROCESSING REVIT FILE WITH DESIGN AUTOMATION")
        print("=" * 60)
        print(f"File: {file_path}")
        print(f"Activity: {self.activity_id}")
        print(f"File size: {os.path.getsize(file_path) / 1024 / 1024:.1f} MB")
        print("=" * 60)
        
        # Step 1: Authentication
        print("\n1. Authenticating...")
        if not self.get_access_token():
            return False
        
        # Step 2: Create bucket
        print("\n2. Creating storage bucket...")
        if not self.create_bucket():
            return False
        
        # Step 3: Upload file
        print("\n3. Uploading Revit file...")
        if not self.upload_file_with_signed_url(file_path, "input.rvt"):
            return False
        
        # Step 4: Create workitem
        print("\n4. Creating processing job...")
        workitem_id = self.create_workitem()
        if not workitem_id:
            return False
        
        # Step 5: Wait for completion
        print("\n5. Processing file in the cloud...")
        if not self.wait_for_completion(workitem_id):
            return False
        
        # Step 6: Download result
        print("\n6. Downloading results...")
        return self.download_result()

def main():
    file_path = "100.rvt"
    
    if not os.path.exists(file_path):
        print(f"✗ File not found: {file_path}")
        return
    
    processor = RevitFileProcessor()
    success = processor.process_file(file_path)
    
    if success:
        print("\n🎉 SUCCESS! File processed successfully!")
        print("Check 100_rvt_result.txt for the extracted view information")
    else:
        print("\n❌ Processing failed")
        print("Check the error messages above")

if __name__ == "__main__":
    main()
