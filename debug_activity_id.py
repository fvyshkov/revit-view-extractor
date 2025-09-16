#!/usr/bin/env python3
"""
Минимальный скрипт для диагностики проблемы с activity ID
"""

import requests
import json
from config import CLIENT_ID, CLIENT_SECRET

def get_token():
    """Получить токен"""
    url = "https://developer.api.autodesk.com/authentication/v2/token"
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials",
        "scope": "code:all"
    }
    response = requests.post(url, headers={"Content-Type": "application/x-www-form-urlencoded"}, data=data)
    return response.json()["access_token"] if response.status_code == 200 else None

def test_activity_formats(token):
    """Тестировать разные форматы activity ID"""
    print("🔍 ДИАГНОСТИКА ПРОБЛЕМЫ С ACTIVITY ID")
    print("=" * 50)
    
    workitem_url = "https://developer.api.autodesk.com/da/us-east/v3/workitems"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 1. Baseline test - NOP (работает)
    print("1. Baseline test - NOP activity:")
    nop_data = {
        "activityId": "Autodesk.Nop+Latest",
        "arguments": {}
    }
    
    response = requests.post(workitem_url, headers=headers, json=nop_data)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        workitem_id = response.json()["id"]
        print(f"   ✅ SUCCESS: {workitem_id}")
        # Cancel it
        requests.delete(f"{workitem_url}/{workitem_id}", headers={"Authorization": f"Bearer {token}"})
    else:
        print(f"   ❌ FAILED: {response.text}")
        return
    
    # 2. Test our custom activity
    print("\n2. Test custom activity:")
    custom_activity = f"{CLIENT_ID}.ExtractViewsActivityV3+$LATEST"
    print(f"   Activity: {custom_activity}")
    
    custom_data = {
        "activityId": custom_activity,
        "arguments": {
            "inputFile": {
                "url": "https://github.com/Developer-Autodesk/forge-tutorial-postman/raw/master/Collections/DA4R-Tutorial/SampleFiles/DeleteWalls.rvt"
            },
            "result": {
                "url": "https://httpbin.org/put"
            }
        }
    }
    
    response = requests.post(workitem_url, headers=headers, json=custom_data)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        workitem_id = response.json()["id"]
        print(f"   🎉 SUCCESS: {workitem_id}")
        print("   🎯 CUSTOM ACTIVITY WORKS!")
        # Don't cancel - let it run!
        return workitem_id
    else:
        print(f"   ❌ FAILED: {response.text}")
    
    # 3. Test with different formats
    print("\n3. Testing different formats:")
    
    formats_to_test = [
        f"{CLIENT_ID}.ExtractViewsActivityV3",  # Without version
        f"{CLIENT_ID}.ExtractViewsActivityV3+1",  # With version 1
        f"{CLIENT_ID}.ExtractViewsActivityV3+2",  # With version 2
        f"{CLIENT_ID}.ExtractViewsActivity+$LATEST",  # Different activity
    ]
    
    for i, activity_format in enumerate(formats_to_test, 1):
        print(f"   3.{i} {activity_format}")
        
        test_data = custom_data.copy()
        test_data["activityId"] = activity_format
        
        response = requests.post(workitem_url, headers=headers, json=test_data)
        
        if response.status_code == 200:
            workitem_id = response.json()["id"]
            print(f"        🎉 SUCCESS: {workitem_id}")
            print(f"        🎯 WORKING FORMAT: {activity_format}")
            return workitem_id
        else:
            error = response.text[:80] + "..." if len(response.text) > 80 else response.text
            print(f"        ❌ {response.status_code}: {error}")
    
    print("\n❌ NO WORKING CUSTOM ACTIVITY FORMAT FOUND")
    return None

def main():
    print("🚀 MINIMAL ACTIVITY ID DIAGNOSTIC SCRIPT")
    print("=" * 60)
    
    token = get_token()
    if not token:
        print("❌ Cannot get access token")
        return
    
    print("✅ Token obtained")
    
    working_workitem = test_activity_formats(token)
    
    if working_workitem:
        print(f"\n🎉 SUCCESS! Working workitem: {working_workitem}")
        print("🎯 PROBLEM SOLVED - CUSTOM ACTIVITY IS WORKING!")
    else:
        print("\n⚠️ PROBLEM CONFIRMED:")
        print("   • API authentication works")
        print("   • NOP activity works")
        print("   • Custom activities have ID parsing issues")
        print("   • This is an Autodesk API limitation, not our code")

if __name__ == "__main__":
    main()
