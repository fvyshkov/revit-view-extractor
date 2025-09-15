#!/usr/bin/env python3
"""
APS Design Automation Controller
Uploads bundle, creates activity, and runs workitem to extract view from Revit file
"""

import os
import json
import time
import requests
import zipfile
from config import *

class APSController:
    def __init__(self):
        self.access_token = None
        self.bucket_key = f"revit-view-extractor-{int(time.time())}"
        self.app_bundle_id = "RevitViewExtractor"
        self.activity_id = "ExtractViewActivity"
        
    def authenticate(self):
        """Get access token from APS"""
        print("Authenticating with APS...")
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'grant_type': 'client_credentials',
            'scope': ' '.join(SCOPES)
        }
        
        response = requests.post(AUTH_URL, headers=headers, data=data)
        
        if response.status_code == 200:
            token_data = response.json()
            self.access_token = token_data['access_token']
            print("✓ Authentication successful")
            return True
        else:
            print(f"✗ Authentication failed: {response.status_code} - {response.text}")
            return False
    
    def create_bucket(self):
        """Create OSS bucket for file storage"""
        print(f"Creating bucket: {self.bucket_key}")
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'bucketKey': self.bucket_key,
            'policyKey': 'temporary'
        }
        
        response = requests.post(BUCKET_URL, headers=headers, json=data)
        
        if response.status_code in [200, 409]:  # 409 means bucket already exists
            print("✓ Bucket created/exists")
            return True
        else:
            print(f"✗ Bucket creation failed: {response.status_code} - {response.text}")
            return False
    
    def upload_file(self, file_path, object_name):
        """Upload file to OSS bucket"""
        print(f"Uploading {file_path} as {object_name}...")
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/octet-stream'
        }
        
        with open(file_path, 'rb') as f:
            response = requests.put(
                f"{UPLOAD_URL}/{self.bucket_key}/objects/{object_name}",
                headers=headers,
                data=f
            )
        
        if response.status_code == 200:
            print(f"✓ File uploaded successfully")
            return response.json()
        else:
            print(f"✗ File upload failed: {response.status_code} - {response.text}")
            return None
    
    def create_app_bundle(self, bundle_zip_path):
        """Create or update app bundle"""
        print("Creating app bundle...")
        
        # First, upload the bundle zip
        bundle_upload = self.upload_file(bundle_zip_path, "bundle.zip")
        if not bundle_upload:
            return False
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'id': self.app_bundle_id,
            'engine': 'Autodesk.Revit+2024',
            'description': 'Extract first view from Revit file',
            'package': bundle_upload['objectId']
        }
        
        # Try to create new bundle
        response = requests.post(
            f"{APS_BASE_URL}/da/us-east/v3/appbundles",
            headers=headers,
            json=data
        )
        
        if response.status_code in [200, 201]:
            print("✓ App bundle created")
            return True
        elif response.status_code == 409:
            # Bundle exists, create new version
            print("Bundle exists, creating new version...")
            response = requests.post(
                f"{APS_BASE_URL}/da/us-east/v3/appbundles/{self.app_bundle_id}/versions",
                headers=headers,
                json={'package': bundle_upload['objectId']}
            )
            if response.status_code in [200, 201]:
                print("✓ App bundle version created")
                return True
        
        print(f"✗ App bundle creation failed: {response.status_code} - {response.text}")
        return False
    
    def create_activity(self):
        """Create or update activity"""
        print("Creating activity...")
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'id': self.activity_id,
            'commandLine': ['$(engine.path)\\\\revitcoreconsole.exe /i "$(args[inputFile].path)" /al "$(appbundles[{0}].path)"'.format(self.app_bundle_id)],
            'parameters': {
                'inputFile': {
                    'verb': 'get',
                    'description': 'Input Revit file'
                },
                'outputImage': {
                    'verb': 'put',
                    'description': 'Output image file',
                    'localName': 'extracted_view.png'
                }
            },
            'engine': 'Autodesk.Revit+2024',
            'appbundles': [self.app_bundle_id],
            'description': 'Extract first view from Revit file'
        }
        
        # Try to create new activity
        response = requests.post(
            f"{APS_BASE_URL}/da/us-east/v3/activities",
            headers=headers,
            json=data
        )
        
        if response.status_code in [200, 201]:
            print("✓ Activity created")
            return True
        elif response.status_code == 409:
            # Activity exists, create new version
            print("Activity exists, creating new version...")
            response = requests.post(
                f"{APS_BASE_URL}/da/us-east/v3/activities/{self.activity_id}/versions",
                headers=headers,
                json=data
            )
            if response.status_code in [200, 201]:
                print("✓ Activity version created")
                return True
        
        print(f"✗ Activity creation failed: {response.status_code} - {response.text}")
        return False
    
    def run_workitem(self, input_file_path):
        """Run workitem to process the Revit file"""
        print("Running workitem...")
        
        # Upload input file
        input_upload = self.upload_file(input_file_path, "input.rvt")
        if not input_upload:
            return None
        
        # Get signed URLs for input and output
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        # Get signed URL for input
        input_url_response = requests.post(
            f"{UPLOAD_URL}/{self.bucket_key}/objects/input.rvt/signed",
            headers=headers,
            json={'access': 'read'}
        )
        
        if input_url_response.status_code != 200:
            print("✗ Failed to get input signed URL")
            return None
        
        input_signed_url = input_url_response.json()['signedUrl']
        
        # Get signed URL for output
        output_url_response = requests.post(
            f"{UPLOAD_URL}/{self.bucket_key}/objects/output.png/signed",
            headers=headers,
            json={'access': 'readwrite'}
        )
        
        if output_url_response.status_code != 200:
            print("✗ Failed to get output signed URL")
            return None
        
        output_signed_url = output_url_response.json()['signedUrl']
        
        # Create workitem
        workitem_data = {
            'activityId': self.activity_id,
            'arguments': {
                'inputFile': {
                    'url': input_signed_url
                },
                'outputImage': {
                    'url': output_signed_url,
                    'verb': 'put'
                }
            }
        }
        
        workitem_response = requests.post(
            f"{APS_BASE_URL}/da/us-east/v3/workitems",
            headers=headers,
            json=workitem_data
        )
        
        if workitem_response.status_code not in [200, 201]:
            print(f"✗ Workitem creation failed: {workitem_response.status_code} - {workitem_response.text}")
            return None
        
        workitem_id = workitem_response.json()['id']
        print(f"✓ Workitem created: {workitem_id}")
        
        # Poll for completion
        return self.wait_for_completion(workitem_id)
    
    def wait_for_completion(self, workitem_id):
        """Wait for workitem to complete"""
        print("Waiting for workitem completion...")
        
        headers = {
            'Authorization': f'Bearer {self.access_token}'
        }
        
        max_attempts = 60  # 5 minutes max
        attempt = 0
        
        while attempt < max_attempts:
            response = requests.get(
                f"{APS_BASE_URL}/da/us-east/v3/workitems/{workitem_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                status_data = response.json()
                status = status_data['status']
                
                print(f"Status: {status}")
                
                if status == 'success':
                    print("✓ Workitem completed successfully")
                    return self.download_result()
                elif status == 'failed':
                    print("✗ Workitem failed")
                    if 'reportUrl' in status_data:
                        print(f"Report URL: {status_data['reportUrl']}")
                    return None
                elif status in ['pending', 'inprogress']:
                    time.sleep(5)
                    attempt += 1
                else:
                    print(f"Unknown status: {status}")
                    return None
            else:
                print(f"✗ Failed to get workitem status: {response.status_code}")
                return None
        
        print("✗ Workitem timed out")
        return None
    
    def download_result(self):
        """Download the result image"""
        print("Downloading result image...")
        
        headers = {
            'Authorization': f'Bearer {self.access_token}'
        }
        
        response = requests.get(
            f"{UPLOAD_URL}/{self.bucket_key}/objects/output.png",
            headers=headers
        )
        
        if response.status_code == 200:
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            output_path = os.path.join(OUTPUT_DIR, "extracted_view.png")
            
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            print(f"✓ Result downloaded to: {output_path}")
            return output_path
        else:
            print(f"✗ Failed to download result: {response.status_code}")
            return None

def main():
    """Main execution function"""
    controller = APSController()
    
    # Check if bundle zip exists
    bundle_zip = "RevitViewExtractor.zip"
    if not os.path.exists(bundle_zip):
        print(f"✗ Bundle zip not found: {bundle_zip}")
        print("Please run build_bundle.bat on Windows first to create the bundle")
        return
    
    # Check if input file exists
    if not os.path.exists(RVT_FILE_PATH):
        print(f"✗ Input file not found: {RVT_FILE_PATH}")
        return
    
    # Execute the workflow
    if not controller.authenticate():
        return
    
    if not controller.create_bucket():
        return
    
    if not controller.create_app_bundle(bundle_zip):
        return
    
    if not controller.create_activity():
        return
    
    result_path = controller.run_workitem(RVT_FILE_PATH)
    
    if result_path:
        print(f"\n🎉 Success! View extracted to: {result_path}")
    else:
        print("\n❌ Failed to extract view")

if __name__ == "__main__":
    main()
