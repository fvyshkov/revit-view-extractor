#!/bin/bash

echo "🧪 Testing with curl to eliminate Python issues"
echo "================================================"

# Get token
echo "Getting access token..."
TOKEN_RESPONSE=$(curl -s -X POST \
  "https://developer.api.autodesk.com/authentication/v2/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=$CLIENT_ID&client_secret=$CLIENT_SECRET&grant_type=client_credentials&scope=code:all")

TOKEN=$(echo $TOKEN_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

if [ -z "$TOKEN" ]; then
    echo "❌ Failed to get token"
    exit 1
fi

echo "✓ Token obtained"

# List our activities to see exact format
echo "Listing activities..."
ACTIVITIES=$(curl -s -X GET \
  "https://developer.api.autodesk.com/da/us-east/v3/activities" \
  -H "Authorization: Bearer $TOKEN")

echo "Our activities:"
echo $ACTIVITIES | python3 -c "
import sys, json
data = json.load(sys.stdin)
activities = data.get('data', [])
our_activities = [a for a in activities if 'ExtractViews' in a]
for activity in our_activities:
    print(f'  - {activity}')
if our_activities:
    print(f'Using: {our_activities[0]}')
"

# Try to create workitem
ACTIVITY_ID="${CLIENT_ID}.ExtractViewsActivity"
echo "Creating workitem with activity: $ACTIVITY_ID"

WORKITEM_DATA='{
  "activityId": "'$ACTIVITY_ID'",
  "arguments": {
    "inputFile": {
      "url": "https://github.com/Developer-Autodesk/forge-tutorial-postman/raw/master/Collections/DA4R-Tutorial/SampleFiles/DeleteWalls.rvt",
      "verb": "get"
    },
    "result": {
      "url": "https://httpbin.org/put",
      "verb": "put"
    }
  }
}'

echo "Request data:"
echo $WORKITEM_DATA | python3 -m json.tool

WORKITEM_RESPONSE=$(curl -s -X POST \
  "https://developer.api.autodesk.com/da/us-east/v3/workitems" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "$WORKITEM_DATA")

echo "Response:"
echo $WORKITEM_RESPONSE | python3 -m json.tool

# Check if successful
if echo $WORKITEM_RESPONSE | grep -q '"id"'; then
    WORKITEM_ID=$(echo $WORKITEM_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
    echo "✓ SUCCESS! Workitem created: $WORKITEM_ID"
    echo "🎉 Our plugin is working!"
else
    echo "❌ Failed to create workitem"
fi
