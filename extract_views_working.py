#!/usr/bin/env python3
"""
Working Revit View Extractor based on Autodesk documentation
"""

import requests
import json
import time
import os
from config import CLIENT_ID, CLIENT_SECRET

def get_access_token():
    """Get access token from Autodesk"""
    url = "https://developer.api.autodesk.com/authentication/v2/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials",
        "scope": "code:all data:write data:read bucket:create bucket:delete"
    }
    
    response = requests.post(url, headers=headers, data=data)
    
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Failed to get token: {response.text}")
        return None

def get_nickname(token):
    """Get forge app nickname"""
    url = "https://developer.api.autodesk.com/da/us-east/v3/forgeapps/me"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        # Response is a plain string, not JSON
        return response.text.strip('"')
    else:
        print(f"Failed to get nickname: {response.text}")
        return None

def create_bucket(token, bucket_name):
    """Create OSS bucket"""
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
    
    if response.status_code in [200, 409]:  # 409 means bucket already exists
        return True
    else:
        print(f"Failed to create bucket: {response.text}")
        return False

def upload_file(token, bucket_name, file_path):
    """Upload file to OSS"""
    file_name = os.path.basename(file_path)
    
    # Direct upload
    url = f"https://developer.api.autodesk.com/oss/v2/buckets/{bucket_name}/objects/{file_name}"
    
    # Get file size
    file_size = os.path.getsize(file_path)
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/octet-stream",
        "Content-Length": str(file_size)
    }
    
    with open(file_path, 'rb') as f:
        file_data = f.read()
    
    response = requests.put(url, headers=headers, data=file_data)
    
    if response.status_code == 200:
        result = response.json()
        return result["objectId"]
    else:
        print(f"Failed to upload file: {response.text}")
        return None

def create_simple_activity(token, nickname):
    """Create a simple test activity following Autodesk documentation"""
    
    activity_name = "ExtractViews"
    
    # Delete existing activity if any
    delete_url = f"https://developer.api.autodesk.com/da/us-east/v3/activities/{nickname}.{activity_name}"
    headers = {"Authorization": f"Bearer {token}"}
    requests.delete(delete_url, headers=headers)
    
    # Create new activity
    url = "https://developer.api.autodesk.com/da/us-east/v3/activities"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Simple activity that just copies input to output
    activity_data = {
        "id": activity_name,
        "commandLine": ["$(engine.path)\\\\revitcoreconsole.exe /i \"$(args[inputFile].path)\" /al \"$(appbundles[RevitViewExtractor4].path)\""],
        "parameters": {
            "inputFile": {
                "verb": "get",
                "description": "Input Revit file",
                "required": True,
                "localName": "input.rvt"
            },
            "result": {
                "verb": "put",
                "description": "Results",
                "localName": "result.txt",
                "required": True
            }
        },
        "engine": "Autodesk.Revit+2026",
        "appbundles": [f"{nickname}.RevitViewExtractor4+1"],
        "description": "Extract views from Revit file"
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(activity_data))
    
    if response.status_code == 200:
        print(f"✅ Activity created: {nickname}.{activity_name}")
        return f"{nickname}.{activity_name}"
    else:
        print(f"❌ Failed to create activity: {response.text}")
        return None

def create_alias(token, activity_id):
    """Create alias for activity"""
    base_url = "https://developer.api.autodesk.com/da/us-east/v3/activities"
    
    # Create alias
    alias_url = f"{base_url}/{activity_id}/aliases"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    alias_data = {
        "id": "prod",
        "version": 1
    }
    
    response = requests.post(alias_url, headers=headers, json=alias_data)
    
    if response.status_code in [200, 409]:  # 409 means alias exists
        print(f"✅ Alias 'prod' created for {activity_id}")
        return True
    else:
        print(f"❌ Failed to create alias: {response.text}")
        return False

def create_workitem(token, activity_id, input_url, output_url):
    """Create and execute workitem"""
    url = "https://developer.api.autodesk.com/da/us-east/v3/workitems"
    
    workitem_data = {
        "activityId": f"{activity_id}+prod",
        "arguments": {
            "inputFile": {
                "url": input_url,
                "verb": "get",
                "headers": {
                    "Authorization": f"Bearer {token}"
                }
            },
            "result": {
                "url": output_url,
                "verb": "put",
                "headers": {
                    "Authorization": f"Bearer {token}"
                }
            }
        }
    }
    
    # Send as string with Content-Length
    json_str = json.dumps(workitem_data)
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Content-Length": str(len(json_str))
    }
    
    response = requests.post(url, headers=headers, data=json_str)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Workitem created: {result['id']}")
        return result['id']
    else:
        print(f"❌ Failed to create workitem: {response.text}")
        return None

def monitor_workitem(token, workitem_id):
    """Monitor workitem status"""
    url = f"https://developer.api.autodesk.com/da/us-east/v3/workitems/{workitem_id}"
    headers = {"Authorization": f"Bearer {token}"}
    
    print("Monitoring workitem...")
    for i in range(60):  # Check for up to 5 minutes
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            status = result.get("status", "unknown")
            print(f"Status: {status}")
            
            if status == "success":
                print("✅ Workitem completed successfully!")
                return result
            elif status == "failed":
                print("❌ Workitem failed!")
                if "reportUrl" in result:
                    print(f"Report: {result['reportUrl']}")
                return result
            elif status in ["pending", "inprogress"]:
                time.sleep(5)
            else:
                print(f"Unknown status: {status}")
                return result
        else:
            print(f"Failed to get status: {response.text}")
            return None
    
    print("Timeout waiting for workitem")
    return None

def get_result(token, bucket_name, object_name):
    """Download result from OSS"""
    url = f"https://developer.api.autodesk.com/oss/v2/buckets/{bucket_name}/objects/{object_name}"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.text
    else:
        print(f"Failed to get result: {response.text}")
        return None

def main():
    print("🚀 REVIT VIEW EXTRACTOR - WORKING VERSION")
    print("=" * 50)
    
    # 1. Get token
    print("\n1. Getting access token...")
    token = get_access_token()
    if not token:
        return
    print("✅ Token obtained")
    
    # 2. Get nickname
    print("\n2. Getting nickname...")
    nickname = get_nickname(token)
    if not nickname:
        return
    print(f"✅ Nickname: {nickname}")
    
    # 3. Create bucket
    print("\n3. Creating bucket...")
    bucket_name = f"revitviews{int(time.time())}"
    if not create_bucket(token, bucket_name):
        return
    print(f"✅ Bucket created: {bucket_name}")
    
    # 4. Upload file
    print("\n4. Uploading Revit file...")
    object_id = upload_file(token, bucket_name, "100.rvt")
    if not object_id:
        return
    print(f"✅ File uploaded: {object_id}")
    
    # 5. Create activity
    print("\n5. Creating activity...")
    activity_id = create_simple_activity(token, nickname)
    if not activity_id:
        return
    
    # 6. Create alias
    print("\n6. Creating alias...")
    if not create_alias(token, activity_id):
        return
    
    # 7. Create workitem
    print("\n7. Creating workitem...")
    input_url = f"urn:adsk.objects:os.object:{object_id}"
    output_url = f"urn:adsk.objects:os.object:{bucket_name}/result.txt"
    
    workitem_id = create_workitem(token, activity_id, input_url, output_url)
    if not workitem_id:
        return
    
    # 8. Monitor execution
    print("\n8. Monitoring execution...")
    result = monitor_workitem(token, workitem_id)
    
    if result and result.get("status") == "success":
        # 9. Get results
        print("\n9. Getting results...")
        views_data = get_result(token, bucket_name, "result.txt")
        if views_data:
            print("\n✅ VIEW EXTRACTION SUCCESSFUL!")
            print("=" * 50)
            print(views_data)
            print("=" * 50)
        else:
            print("❌ Could not retrieve results")
    else:
        print("❌ Workitem execution failed")

if __name__ == "__main__":
    main()
