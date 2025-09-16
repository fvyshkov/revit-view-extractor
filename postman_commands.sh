#!/bin/bash

# Autodesk API Commands for Postman/Curl

CLIENT_ID="2ceGWNLbW8QeWElmqiBGQAj2BLkNJuB8kNIWUCJHwKHhYUzN"
CLIENT_SECRET="QbHFWvsR0V49buWiqQYXTIOcwlh8Q5pgkJpa9MmqxiY1wukDkkZ2MgqNWHaOfkvD"

echo "🚀 AUTODESK API COMMANDS"
echo "========================"

# 1. Get Access Token
echo ""
echo "1. Get Access Token:"
echo "-------------------"
cat << 'EOF'
curl -X POST \
  https://developer.api.autodesk.com/authentication/v2/token \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'client_id=2ceGWNLbW8QeWElmqiBGQAj2BLkNJuB8kNIWUCJHwKHhYUzN&client_secret=QbHFWvsR0V49buWiqQYXTIOcwlh8Q5pgkJpa9MmqxiY1wukDkkZ2MgqNWHaOfkvD&grant_type=client_credentials&scope=code:all data:write data:read bucket:create bucket:delete'
EOF

# 2. Test with NOP Activity (this works!)
echo ""
echo ""
echo "2. Test with NOP Activity (WORKS!):"
echo "-----------------------------------"
cat << 'EOF'
curl -X POST \
  https://developer.api.autodesk.com/da/us-east/v3/workitems \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
    "activityId": "Autodesk.Nop+Latest",
    "arguments": {}
  }'
EOF

# 3. Create Custom Activity (will create but not usable)
echo ""
echo ""
echo "3. Create Activity (creates but has issues):"
echo "-------------------------------------------"
cat << 'EOF'
curl -X POST \
  https://developer.api.autodesk.com/da/us-east/v3/activities \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
    "id": "ViewExtractor",
    "commandLine": ["\"$(engine.path)\\revitcoreconsole.exe\" /i \"$(args[inputFile].path)\" /al \"$(appbundles[RevitViewExtractor4].path)\""],
    "parameters": {
      "inputFile": {
        "verb": "get",
        "description": "Input Revit file",
        "required": true,
        "localName": "input.rvt"
      },
      "result": {
        "verb": "put",
        "description": "Results",
        "localName": "result.txt",
        "required": true
      }
    },
    "engine": "Autodesk.Revit+2026",
    "appbundles": ["2ceGWNLbW8QeWElmqiBGQAj2BLkNJuB8kNIWUCJHwKHhYUzN.RevitViewExtractor4+1"],
    "description": "Extract views"
  }'
EOF

echo ""
echo ""
echo "⚠️  IMPORTANT NOTES:"
echo "===================="
echo "1. Replace YOUR_ACCESS_TOKEN with the token from step 1"
echo "2. The 48-character CLIENT_ID causes 'Cannot parse id' errors"
echo "3. Only system activities like Autodesk.Nop+Latest work"
echo "4. Custom activities are created but cannot be used"
echo ""
echo "📱 RECOMMENDED: Use Postman GUI instead of curl"
echo "   - Import Autodesk collection"
echo "   - It may handle the long CLIENT_ID better"
echo "   - Has built-in environment variable management"
