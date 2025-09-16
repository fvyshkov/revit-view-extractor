#!/usr/bin/env python3
"""
Design Automation Tools Approach - Using public URLs
"""

import requests
import json
import time
from config import CLIENT_ID, CLIENT_SECRET

def get_access_token():
    """Get Autodesk access token"""
    url = "https://developer.api.autodesk.com/authentication/v2/token"
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials",
        "scope": "code:all data:write data:read bucket:create bucket:delete"
    }
    response = requests.post(url, headers={"Content-Type": "application/x-www-form-urlencoded"}, data=data)
    
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Failed to get token: {response.text}")
        return None

def upload_bundle_to_github():
    """
    For testing, we need a public URL for our bundle.
    In production, you would upload to GitHub releases or another public host.
    """
    print("\n📦 BUNDLE UPLOAD INSTRUCTIONS:")
    print("=" * 50)
    print("1. Upload RevitViewExtractor_Bundle.zip to GitHub:")
    print("   - Go to your GitHub repo")
    print("   - Click 'Add file' > 'Upload files'")
    print("   - Upload RevitViewExtractor_Bundle.zip")
    print("   - Commit the file")
    print("")
    print("2. Get the raw URL:")
    print("   - Click on the uploaded file")
    print("   - Click 'Raw' button")
    print("   - Copy the URL (should start with https://raw.githubusercontent.com)")
    print("")
    print("Example URL format:")
    print("https://raw.githubusercontent.com/username/repo/main/RevitViewExtractor_Bundle.zip")
    print("=" * 50)
    
    # For now, return a placeholder
    return "REPLACE_WITH_YOUR_BUNDLE_URL"

def create_appbundle(token, bundle_url):
    """Create AppBundle using public URL"""
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Delete existing bundle if any
    delete_url = f"https://developer.api.autodesk.com/da/us-east/v3/appbundles/{CLIENT_ID}.RevitViewExtractor"
    requests.delete(delete_url, headers=headers)
    
    # Create new bundle
    bundle_data = {
        "id": "RevitViewExtractor",
        "engine": "Autodesk.Revit+2024",
        "description": "Extract views from Revit files"
    }
    
    create_url = "https://developer.api.autodesk.com/da/us-east/v3/appbundles"
    response = requests.post(create_url, headers=headers, json=bundle_data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ AppBundle created: {result['id']}")
        
        # Upload bundle using the provided upload parameters
        upload_params = result["uploadParameters"]
        
        # For public URL approach, we need to download and re-upload
        # This is where DA Tools approach differs - they expect you to provide the URL directly
        
        return result['id']
    else:
        print(f"❌ Failed to create bundle: {response.text}")
        return None

def create_activity_simple(token):
    """Create activity with minimal configuration"""
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    activity_name = "ExtractViewsSimple"
    
    # Delete if exists
    delete_url = f"https://developer.api.autodesk.com/da/us-east/v3/activities/{CLIENT_ID}.{activity_name}"
    requests.delete(delete_url, headers=headers)
    
    # Create activity
    activity_data = {
        "id": activity_name,
        "commandLine": [
            "$(engine.path)\\\\revitcoreconsole.exe /i \"$(args[inputFile].path)\" /al \"$(appbundles[RevitViewExtractor].path)\""
        ],
        "parameters": {
            "inputFile": {
                "verb": "get",
                "description": "Input Revit file",
                "required": True,
                "localName": "input.rvt"
            },
            "result": {
                "verb": "put",
                "description": "Result file",
                "localName": "result.txt",
                "required": True
            }
        },
        "engine": "Autodesk.Revit+2024",
        "appbundles": [f"{CLIENT_ID}.RevitViewExtractor+1"],
        "description": "Extract views from Revit"
    }
    
    response = requests.post("https://developer.api.autodesk.com/da/us-east/v3/activities", 
                            headers=headers, json=activity_data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Activity created: {result['id']}")
        return result['id']
    else:
        print(f"❌ Failed to create activity: {response.text}")
        return None

def test_with_public_urls(token, activity_id):
    """Test using publicly accessible URLs like DA Tools does"""
    
    print("\n🌐 TESTING WITH PUBLIC URLs")
    print("=" * 50)
    
    # Use Autodesk's sample file
    input_url = "https://github.com/Developer-Autodesk/forge-tutorial-postman/raw/master/Collections/DA4R-Tutorial/SampleFiles/DeleteWalls.rvt"
    
    # For output, we'll use httpbin for testing
    output_url = "https://httpbin.org/put"
    
    workitem_data = {
        "activityId": f"{activity_id}+1",
        "arguments": {
            "inputFile": {
                "url": input_url,
                "verb": "get"
            },
            "result": {
                "url": output_url,
                "verb": "put",
                "headers": {
                    "Content-Type": "text/plain"
                }
            }
        }
    }
    
    # Send request
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Use json.dumps and Content-Length
    json_str = json.dumps(workitem_data)
    headers["Content-Length"] = str(len(json_str))
    
    response = requests.post("https://developer.api.autodesk.com/da/us-east/v3/workitems",
                           headers=headers, data=json_str)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Workitem created: {result['id']}")
        return result['id']
    else:
        print(f"❌ Failed: {response.text}")
        return None

def monitor_workitem(token, workitem_id):
    """Monitor workitem progress"""
    
    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://developer.api.autodesk.com/da/us-east/v3/workitems/{workitem_id}"
    
    print("\nMonitoring workitem...")
    for i in range(30):
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            status = result.get("status", "unknown")
            print(f"[{i*5}s] Status: {status}")
            
            if status == "success":
                print("\n✅ SUCCESS!")
                if "reportUrl" in result:
                    print(f"Report: {result['reportUrl']}")
                return True
            elif status == "failed":
                print("\n❌ FAILED!")
                if "reportUrl" in result:
                    print(f"Report: {result['reportUrl']}")
                    # Get report content
                    report_response = requests.get(result['reportUrl'])
                    if report_response.status_code == 200:
                        print("\nReport content:")
                        print(report_response.text)
                return False
        
        time.sleep(5)
    
    return False

def main():
    print("🚀 DESIGN AUTOMATION TOOLS APPROACH")
    print("=" * 50)
    
    # Step 1: Get token
    print("\n1. Getting access token...")
    token = get_access_token()
    if not token:
        return
    print("✅ Token obtained")
    
    # Step 2: Show bundle upload instructions
    bundle_url = upload_bundle_to_github()
    
    # Step 3: Create activity
    print("\n3. Creating activity...")
    activity_id = create_activity_simple(token)
    if not activity_id:
        return
    
    # Step 4: Test with public URLs
    workitem_id = test_with_public_urls(token, activity_id)
    if workitem_id:
        # Step 5: Monitor
        success = monitor_workitem(token, workitem_id)
        
        if success:
            print("\n🎉 DA TOOLS APPROACH WORKS!")
            print("\nNext steps:")
            print("1. Upload your bundle to a public URL")
            print("2. Use https://da-manager.autodesk.io/ for visual management")
            print("3. Or continue with this script approach")

if __name__ == "__main__":
    main()
