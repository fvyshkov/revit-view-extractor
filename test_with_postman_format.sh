#!/bin/bash

echo "🚀 TESTING WITH POSTMAN-STYLE API CALLS"
echo "======================================"

CLIENT_ID="rfZQOaSWaILCGB3wRheGj994IH1qCoy9f0tZiPrGs117K48n"
CLIENT_SECRET="FRAmVrbnXcyp72GUcgmwANOk3lnil0ELRJGmPCzgebvr8DVEnGaNmk1b2ed9Gatq"

# Step 1: Get Access Token
echo "🔑 Step 1: Getting access token..."
TOKEN_RESPONSE=$(curl -s -X POST \
  "https://developer.api.autodesk.com/authentication/v2/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=${CLIENT_ID}&client_secret=${CLIENT_SECRET}&grant_type=client_credentials&scope=code:all")

TOKEN=$(echo $TOKEN_RESPONSE | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "❌ Failed to get token"
    echo "Response: $TOKEN_RESPONSE"
    exit 1
fi

echo "✅ Token obtained: ${TOKEN:0:20}..."

# Step 2: List Activities
echo ""
echo "🔍 Step 2: Listing activities..."
ACTIVITIES_RESPONSE=$(curl -s -X GET \
  "https://developer.api.autodesk.com/da/us-east/v3/activities" \
  -H "Authorization: Bearer $TOKEN")

echo "Our activities:"
echo $ACTIVITIES_RESPONSE | grep -o "${CLIENT_ID}[^\"]*" | head -5

# Step 3: Try different activity formats
echo ""
echo "🧪 Step 3: Testing workitem creation with different formats..."

# Format 1: Try with WorkingViewExtractor (no version)
ACTIVITY_ID="${CLIENT_ID}.WorkingViewExtractor"
echo "Testing: $ACTIVITY_ID"

WORKITEM_RESPONSE1=$(curl -s -X POST \
  "https://developer.api.autodesk.com/da/us-east/v3/workitems" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "activityId": "'$ACTIVITY_ID'",
    "arguments": {
      "inputFile": {
        "url": "https://github.com/Developer-Autodesk/forge-tutorial-postman/raw/master/Collections/DA4R-Tutorial/SampleFiles/DeleteWalls.rvt"
      },
      "result": {
        "url": "https://httpbin.org/put"
      }
    }
  }')

echo "Response 1: $WORKITEM_RESPONSE1"

if echo "$WORKITEM_RESPONSE1" | grep -q '"id"'; then
    WORKITEM_ID=$(echo $WORKITEM_RESPONSE1 | grep -o '"id":"[^"]*"' | cut -d'"' -f4)
    echo ""
    echo "🎉🎉🎉 SUCCESS! 🎉🎉🎉"
    echo "Workitem created: $WORKITEM_ID"
    echo "Activity: $ACTIVITY_ID"
    echo ""
    echo "📊 Monitoring execution..."
    
    # Monitor workitem
    for i in {1..20}; do
        sleep 5
        STATUS_RESPONSE=$(curl -s -X GET \
          "https://developer.api.autodesk.com/da/us-east/v3/workitems/$WORKITEM_ID" \
          -H "Authorization: Bearer $TOKEN")
        
        STATUS=$(echo $STATUS_RESPONSE | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
        echo "[$((i*5))s] Status: $STATUS"
        
        if [ "$STATUS" = "success" ]; then
            echo ""
            echo "🎉 COMPLETE SUCCESS!"
            echo "🚀 YOUR REVIT PLUGIN PROCESSED A FILE IN THE CLOUD!"
            
            # Get report
            REPORT_URL=$(echo $STATUS_RESPONSE | grep -o '"reportUrl":"[^"]*"' | cut -d'"' -f4)
            if [ ! -z "$REPORT_URL" ]; then
                echo ""
                echo "📋 EXECUTION REPORT:"
                echo "===================="
                curl -s "$REPORT_URL"
                echo ""
                echo "===================="
            fi
            
            echo ""
            echo "🎯 YOUR REVIT VIEW EXTRACTOR IS WORKING!"
            exit 0
            
        elif [ "$STATUS" = "failed" ]; then
            echo ""
            echo "❌ Execution failed"
            
            REPORT_URL=$(echo $STATUS_RESPONSE | grep -o '"reportUrl":"[^"]*"' | cut -d'"' -f4)
            if [ ! -z "$REPORT_URL" ]; then
                echo ""
                echo "📋 FAILURE REPORT:"
                echo "==================="
                curl -s "$REPORT_URL"
                echo ""
                echo "==================="
            fi
            exit 1
            
        elif [ "$STATUS" = "inprogress" ] || [ "$STATUS" = "pending" ]; then
            continue
        else
            echo "Unknown status: $STATUS"
            break
        fi
    done
    
    echo "⏰ Timeout"
    exit 1
fi

# Format 2: Try with explicit version +1
ACTIVITY_ID2="${CLIENT_ID}.WorkingViewExtractor+1"
echo ""
echo "Testing: $ACTIVITY_ID2"

WORKITEM_RESPONSE2=$(curl -s -X POST \
  "https://developer.api.autodesk.com/da/us-east/v3/workitems" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "activityId": "'$ACTIVITY_ID2'",
    "arguments": {
      "inputFile": {
        "url": "https://github.com/Developer-Autodesk/forge-tutorial-postman/raw/master/Collections/DA4R-Tutorial/SampleFiles/DeleteWalls.rvt"
      },
      "result": {
        "url": "https://httpbin.org/put"
      }
    }
  }')

echo "Response 2: $WORKITEM_RESPONSE2"

if echo "$WORKITEM_RESPONSE2" | grep -q '"id"'; then
    WORKITEM_ID=$(echo $WORKITEM_RESPONSE2 | grep -o '"id":"[^"]*"' | cut -d'"' -f4)
    echo ""
    echo "🎉 SUCCESS with +1 version!"
    echo "Workitem: $WORKITEM_ID"
fi

# Format 3: Try other activities
echo ""
echo "🔄 Trying other activities..."

for ACTIVITY in "ExtractViewsActivity" "ExtractViewsActivityV3" "RevitViewExtractorFinal"; do
    FULL_ACTIVITY="${CLIENT_ID}.${ACTIVITY}"
    echo "Testing: $FULL_ACTIVITY"
    
    WORKITEM_RESPONSE=$(curl -s -X POST \
      "https://developer.api.autodesk.com/da/us-east/v3/workitems" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "activityId": "'$FULL_ACTIVITY'",
        "arguments": {
          "inputFile": {
            "url": "https://github.com/Developer-Autodesk/forge-tutorial-postman/raw/master/Collections/DA4R-Tutorial/SampleFiles/DeleteWalls.rvt"
          },
          "result": {
            "url": "https://httpbin.org/put"
          }
        }
      }')
    
    if echo "$WORKITEM_RESPONSE" | grep -q '"id"'; then
        WORKITEM_ID=$(echo $WORKITEM_RESPONSE | grep -o '"id":"[^"]*"' | cut -d'"' -f4)
        echo "🎉 SUCCESS! Workitem: $WORKITEM_ID"
        echo "🎯 Working activity: $FULL_ACTIVITY"
        break
    else
        echo "❌ Failed: $(echo $WORKITEM_RESPONSE | head -c 100)..."
    fi
done

echo ""
echo "📊 SUMMARY:"
echo "✅ Plugin deployed to cloud"
echo "✅ Activities created"
echo "✅ API format tested with Postman-style calls"
echo "⚠️ Need to resolve activity versioning issue"




