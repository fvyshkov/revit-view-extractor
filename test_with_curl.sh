#!/bin/bash

# Получаем токен из Python
echo "Getting access token..."
TOKEN=$(python3 -c "
from config import *
import requests
url = 'https://developer.api.autodesk.com/authentication/v2/token'
data = {
    'client_id': CLIENT_ID,
    'client_secret': CLIENT_SECRET, 
    'grant_type': 'client_credentials',
    'scope': 'code:all'
}
response = requests.post(url, headers={'Content-Type': 'application/x-www-form-urlencoded'}, data=data)
if response.status_code == 200:
    print(response.json()['access_token'])
else:
    print('ERROR')
")

if [ "$TOKEN" = "ERROR" ]; then
    echo "Failed to get token"
    exit 1
fi

echo "Token obtained: ${TOKEN:0:20}..."

# Тестируем наши Activities через curl
echo -e "\n=== Testing our activities with curl ==="

ACTIVITIES=(
    "rfZQOaSWaILCGB3wRheGj994IH1qCoy9f0tZiPrGs117K48n.ExtractViewsActivity"
    "rfZQOaSWaILCGB3wRheGj994IH1qCoy9f0tZiPrGs117K48n.FreshViewExtractor1757953464"
    "rfZQOaSWaILCGB3wRheGj994IH1qCoy9f0tZiPrGs117K48n.RevitViewExtractorFinal"
)

for ACTIVITY in "${ACTIVITIES[@]}"; do
    echo -e "\nTesting activity: $ACTIVITY"
    
    # Создаем workitem через curl
    curl -X POST \
        "https://developer.api.autodesk.com/da/us-east/v3/workitems" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "activityId": "'$ACTIVITY'",
            "arguments": {
                "inputFile": {
                    "url": "https://github.com/Developer-Autodesk/forge-tutorial-postman/raw/master/Collections/DA4R-Tutorial/SampleFiles/DeleteWalls.rvt"
                },
                "result": {
                    "url": "https://httpbin.org/put"
                }
            }
        }' \
        -w "\nHTTP Status: %{http_code}\n" \
        -s
    
    echo -e "\n---"
done

echo -e "\n=== Testing with different formats ==="

# Пробуем разные форматы ID
FORMATS=(
    "rfZQOaSWaILCGB3wRheGj994IH1qCoy9f0tZiPrGs117K48n.ExtractViewsActivity+1"
    "ExtractViewsActivity"
    "rfZQOaSWaILCGB3wRheGj994IH1qCoy9f0tZiPrGs117K48n.ExtractViewsActivity+\$LATEST"
)

for FORMAT in "${FORMATS[@]}"; do
    echo -e "\nTesting format: $FORMAT"
    
    curl -X POST \
        "https://developer.api.autodesk.com/da/us-east/v3/workitems" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "activityId": "'$FORMAT'",
            "arguments": {
                "inputFile": {
                    "url": "https://github.com/Developer-Autodesk/forge-tutorial-postman/raw/master/Collections/DA4R-Tutorial/SampleFiles/DeleteWalls.rvt"
                },
                "result": {
                    "url": "https://httpbin.org/put"
                }
            }
        }' \
        -w "\nHTTP Status: %{http_code}\n" \
        -s
    
    echo -e "\n---"
done