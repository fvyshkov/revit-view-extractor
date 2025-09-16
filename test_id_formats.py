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

def test_different_id_formats():
    """Тестируем разные форматы ID"""
    token = get_access_token()
    
    # Последняя созданная Activity
    base_id = "rfZQOaSWaILCGB3wRheGj994IH1qCoy9f0tZiPrGs117K48n.FreshViewExtractor1757953464"
    
    formats_to_try = [
        base_id,  # Полный ID
        base_id + "+1",  # С версией
        base_id + "+$LATEST",  # С $LATEST
        "FreshViewExtractor1757953464",  # Только имя
        f"{CLIENT_ID}.FreshViewExtractor1757953464+1",  # Другой формат
    ]
    
    for activity_id in formats_to_try:
        print(f"\nTesting format: {activity_id}")
        
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
            print(f"SUCCESS! Working format: {activity_id}")
            return activity_id
        else:
            print(f"Failed: {response.text[:100]}...")
    
    print("\nNo working formats found")
    return None

if __name__ == "__main__":
    test_different_id_formats()




