#!/usr/bin/env python3
"""
Get exact bundle versions
"""

import requests
from config import CLIENT_ID, CLIENT_SECRET

def get_access_token():
    url = "https://developer.api.autodesk.com/authentication/v2/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials",
        "scope": "code:all"
    }
    
    response = requests.post(url, headers=headers, data=data)
    return response.json()["access_token"] if response.status_code == 200 else None

def get_bundle_versions(token, bundle_name):
    """Get all versions of a specific bundle"""
    url = f"https://developer.api.autodesk.com/da/us-east/v3/appbundles/{bundle_name}/versions"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        versions = response.json()["data"]
        print(f"Versions for {bundle_name}:")
        for version in versions:
            print(f"  - {version}")
        return versions
    else:
        print(f"Failed to get versions: {response.text}")
        return []

def main():
    token = get_access_token()
    if not token:
        return
    
    bundle_name = f"{CLIENT_ID}.RevitViewExtractor4"
    print(f"Getting versions for: {bundle_name}")
    
    versions = get_bundle_versions(token, bundle_name)
    
    if versions:
        latest_version = versions[0]  # Usually first is latest
        print(f"\n✓ Use this exact reference: {bundle_name}+{latest_version}")
    else:
        print("No versions found")

if __name__ == "__main__":
    main()




