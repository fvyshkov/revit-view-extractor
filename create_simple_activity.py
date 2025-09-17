#!/usr/bin/env python3

import requests
import time
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

def create_minimal_activity():
    """Создать минимальную Activity без сложных параметров"""
    token = get_access_token()
    timestamp = int(time.time())
    
    # Минимальная Activity - просто echo
    activity_data = {
        "id": f"MinimalTest{timestamp}",
        "commandLine": ["echo 'Hello from Design Automation' > result.txt"],
        "parameters": {
            "result": {
                "verb": "put",
                "description": "Output result file",
                "localName": "result.txt"
            }
        },
        "engine": "Autodesk.Revit+2026",
        "description": "Minimal test activity"
    }
    
    print(f"Creating minimal activity: MinimalTest{timestamp}")
    
    response = requests.post(
        "https://developer.api.autodesk.com/da/us-east/v3/activities",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json=activity_data
    )
    
    print(f"Activity creation: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        activity_id = response.json()["id"]
        print(f"SUCCESS: Activity created: {activity_id}")
        
        # Сразу тестируем workitem
        workitem_data = {
            "activityId": activity_id,
            "arguments": {
                "result": {
                    "url": "https://httpbin.org/put"
                }
            }
        }
        
        workitem_response = requests.post(
            "https://developer.api.autodesk.com/da/us-east/v3/workitems",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json=workitem_data
        )
        
        print(f"Workitem creation: {workitem_response.status_code}")
        print(f"Workitem response: {workitem_response.text}")
        
        if workitem_response.status_code == 200:
            workitem_id = workitem_response.json()["id"]
            print(f"SUCCESS! Workitem created: {workitem_id}")
            return activity_id, workitem_id
        else:
            print("Workitem failed")
            return activity_id, None
    else:
        print("Activity creation failed")
        return None, None

if __name__ == "__main__":
    create_minimal_activity()





