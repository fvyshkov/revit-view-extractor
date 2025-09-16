#!/usr/bin/env python3
"""
List existing activities to see the correct format
"""

import requests
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

def list_activities(token):
    """List all activities"""
    url = "https://developer.api.autodesk.com/da/us-east/v3/activities"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        activities = response.json()["data"]
        print("Available Activities:")
        for activity in activities:
            print(f"  - {activity}")
        return activities
    else:
        print(f"Failed to list activities: {response.text}")
        return []

def get_activity_details(token, activity_id):
    """Get details of a specific activity"""
    url = f"https://developer.api.autodesk.com/da/us-east/v3/activities/{activity_id}"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        details = response.json()
        print(f"\nActivity details for {activity_id}:")
        print(f"Engine: {details.get('engine', 'N/A')}")
        print(f"Command: {details.get('commandLine', 'N/A')}")
        print(f"AppBundles: {details.get('appbundles', 'N/A')}")
        return details
    else:
        print(f"Failed to get activity details: {response.text}")
        return None

def main():
    print("=== Listing Activities ===")
    
    # Get token
    token = get_access_token()
    if not token:
        return
    print("✓ Token obtained")
    
    # List activities
    activities = list_activities(token)
    
    # Get details of first few activities for reference
    user_activities = [a for a in activities if CLIENT_ID in a]
    if user_activities:
        print(f"\nFound {len(user_activities)} user activities:")
        for activity in user_activities[:3]:  # Show first 3
            get_activity_details(token, activity)

if __name__ == "__main__":
    main()




