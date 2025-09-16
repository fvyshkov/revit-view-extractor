#!/usr/bin/env python3

import requests
from config import *

def get_access_token():
    url = "https://developer.api.autodesk.com/authentication/v2/token"
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials",
        "scope": "code:all"
    }
    response = requests.post(url, headers={"Content-Type": "application/x-www-form-urlencoded"}, data=data)
    return response.json()["access_token"] if response.status_code == 200 else None

def list_our_activities():
    """Список всех наших Activities"""
    token = get_access_token()
    
    response = requests.get(
        "https://developer.api.autodesk.com/da/us-east/v3/activities",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        activities = response.json()["data"]
        our_activities = [a for a in activities if CLIENT_ID in a]
        
        print(f"Found {len(our_activities)} our activities:")
        for activity in our_activities:
            print(f"- {activity}")
        return our_activities
    else:
        print(f"Failed to list activities: {response.text}")
        return []

def list_our_bundles():
    """Список всех наших AppBundles"""
    token = get_access_token()
    
    response = requests.get(
        "https://developer.api.autodesk.com/da/us-east/v3/appbundles",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        bundles = response.json()["data"]
        our_bundles = [b for b in bundles if CLIENT_ID in b]
        
        print(f"Found {len(our_bundles)} our bundles:")
        for bundle in our_bundles:
            print(f"- {bundle}")
        return our_bundles
    else:
        print(f"Failed to list bundles: {response.text}")
        return []

def test_system_activities():
    """Тестируем системные Activities"""
    token = get_access_token()
    
    system_activities = [
        "Autodesk.Nop+Latest",
        "Autodesk.ExportSheetImage+Latest"
    ]
    
    for activity_id in system_activities:
        print(f"\nTesting system activity: {activity_id}")
        
        workitem_data = {
            "activityId": activity_id,
            "arguments": {
                "inputFile": {
                    "url": "https://github.com/Developer-Autodesk/forge-tutorial-postman/raw/master/Collections/DA4R-Tutorial/SampleFiles/DeleteWalls.rvt"
                }
            }
        }
        
        response = requests.post(
            "https://developer.api.autodesk.com/da/us-east/v3/workitems",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json=workitem_data
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            workitem_id = response.json()["id"]
            print(f"SUCCESS! System activity works: {activity_id}")
            print(f"Workitem: {workitem_id}")
        else:
            print(f"Failed: {response.text[:100]}...")

if __name__ == "__main__":
    print("=== Our Activities ===")
    list_our_activities()
    
    print("\n=== Our Bundles ===")
    list_our_bundles()
    
    print("\n=== Testing System Activities ===")
    test_system_activities()



