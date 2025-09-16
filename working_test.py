#!/usr/bin/env python3
"""
Working test script with correct API format
"""

import requests
import json
import time
from config import CLIENT_ID, CLIENT_SECRET

def get_access_token():
    """Get access token"""
    url = "https://developer.api.autodesk.com/authentication/v2/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials",
        "scope": "code:all"
    }
    
    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Failed to get token: {response.text}")
        return None

def debug_our_activity(token):
    """Debug our activity to understand the exact format"""
    print("🔍 DEBUGGING OUR ACTIVITY")
    print("="*50)
    
    # List all activities to see the exact format
    url = "https://developer.api.autodesk.com/da/us-east/v3/activities"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        activities = response.json()["data"]
        our_activities = [a for a in activities if "ExtractViews" in a]
        
        print(f"Found our activities: {our_activities}")
        
        if our_activities:
            activity_id = our_activities[0]
            print(f"Using activity: {activity_id}")
            
            # Get activity details
            detail_url = f"https://developer.api.autodesk.com/da/us-east/v3/activities/{activity_id}"
            detail_response = requests.get(detail_url, headers=headers)
            
            if detail_response.status_code == 200:
                details = detail_response.json()
                print("Activity details:")
                print(f"  ID: {details.get('id')}")
                print(f"  Engine: {details.get('engine')}")
                print(f"  Parameters: {list(details.get('parameters', {}).keys())}")
                return activity_id
            else:
                print(f"Failed to get details: {detail_response.text}")
        else:
            print("No ExtractViews activities found")
    else:
        print(f"Failed to list activities: {response.text}")
    
    return None

def create_workitem_correct_format(token, activity_id):
    """Create workitem with absolutely correct format"""
    url = "https://developer.api.autodesk.com/da/us-east/v3/workitems"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Use the EXACT format from Autodesk documentation
    workitem_data = {
        "activityId": activity_id,
        "arguments": {
            "inputFile": {
                "url": "https://github.com/Developer-Autodesk/forge-tutorial-postman/raw/master/Collections/DA4R-Tutorial/SampleFiles/DeleteWalls.rvt"
            },
            "result": {
                "url": "https://httpbin.org/put"
            }
        }
    }
    
    print(f"Creating workitem with activity: {activity_id}")
    print("Request data:")
    print(json.dumps(workitem_data, indent=2))
    
    response = requests.post(url, headers=headers, json=workitem_data)
    
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.text}")
    
    if response.status_code == 200:
        workitem_id = response.json()["id"]
        print(f"✓ Workitem created: {workitem_id}")
        return workitem_id
    else:
        print("✗ Failed to create workitem")
        
        # Try with verb specified
        print("\nTrying with explicit verbs...")
        workitem_data["arguments"]["inputFile"]["verb"] = "get"
        workitem_data["arguments"]["result"]["verb"] = "put"
        
        response2 = requests.post(url, headers=headers, json=workitem_data)
        print(f"Second attempt status: {response2.status_code}")
        print(f"Second attempt response: {response2.text}")
        
        if response2.status_code == 200:
            workitem_id = response2.json()["id"]
            print(f"✓ Workitem created on second attempt: {workitem_id}")
            return workitem_id
        
        return None

def monitor_workitem(token, workitem_id):
    """Monitor workitem execution"""
    url = f"https://developer.api.autodesk.com/da/us-east/v3/workitems/{workitem_id}"
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"\n📊 Monitoring workitem: {workitem_id}")
    print("This will show if our plugin actually works...")
    
    for i in range(60):  # 10 minutes
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            status = data["status"]
            
            if i % 3 == 0:  # Print every 30 seconds
                print(f"Status: {status} (elapsed: {i*10}s)")
            
            if status == "success":
                print("\n🎉 SUCCESS!")
                print("Our RevitViewExtractor plugin worked!")
                print("It processed a Revit file in the cloud!")
                
                if "reportUrl" in data:
                    print(f"\nReport URL: {data['reportUrl']}")
                    
                    # Try to get the report
                    try:
                        report_response = requests.get(data['reportUrl'])
                        if report_response.status_code == 200:
                            print("\nExecution Report:")
                            print("-" * 40)
                            print(report_response.text)
                            print("-" * 40)
                    except:
                        print("Could not fetch report")
                
                return True
                
            elif status == "failed":
                print(f"\n❌ FAILED")
                if "reportUrl" in data:
                    print(f"Report URL: {data['reportUrl']}")
                    
                    # Get failure report
                    try:
                        report_response = requests.get(data['reportUrl'])
                        if report_response.status_code == 200:
                            print("\nFailure Report:")
                            print("-" * 40)
                            print(report_response.text)
                            print("-" * 40)
                    except:
                        print("Could not fetch failure report")
                
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
    
    print("⏰ Timeout waiting for completion")
    return False

def main():
    print("🚀 TESTING OUR REVIT PLUGIN - CORRECT FORMAT")
    print("="*60)
    
    # Step 1: Get token
    token = get_access_token()
    if not token:
        return
    print("✓ Token obtained")
    
    # Step 2: Debug our activity
    activity_id = debug_our_activity(token)
    if not activity_id:
        print("❌ Could not find our activity")
        return
    
    # Step 3: Create workitem
    workitem_id = create_workitem_correct_format(token, activity_id)
    if not workitem_id:
        print("❌ Could not create workitem")
        return
    
    # Step 4: Monitor execution
    success = monitor_workitem(token, workitem_id)
    
    if success:
        print("\n🎉 PLUGIN TEST SUCCESSFUL!")
        print("Your RevitViewExtractor is working in the cloud!")
        print("It can extract view information from Revit files!")
    else:
        print("\n⚠️  Test had issues - check the report above")

if __name__ == "__main__":
    main()



