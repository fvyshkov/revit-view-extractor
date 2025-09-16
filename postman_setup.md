# 🚀 Postman Setup for Autodesk Design Automation API

## 1. Install Postman
Download from: https://www.postman.com/downloads/

## 2. Import Autodesk Collection

### Option A: Direct Import Link
1. Open Postman
2. Click "Import" button
3. Use this link: https://www.postman.com/autodesk-platform-services/workspace/autodesk-platform-services-public-workspace/collection/13401446-f2252dc8-5201-426c-b5e8-0b887a0fcea1

### Option B: Fork Collection
1. Go to: https://www.postman.com/autodesk-platform-services/
2. Find "Design Automation for Revit" collection
3. Click "Fork" to your workspace

## 3. Configure Environment Variables

Create new environment with these variables:

```
client_id: 2ceGWNLbW8QeWElmqiBGQAj2BLkNJuB8kNIWUCJHwKHhYUzN
client_secret: QbHFWvsR0V49buWiqQYXTIOcwlh8Q5pgkJpa9MmqxiY1wukDkkZ2MgqNWHaOfkvD
dasApiRoot: https://developer.api.autodesk.com/da/us-east/v3
dasNickName: 2ceGWNLbW8QeWElmqiBGQAj2BLkNJuB8kNIWUCJHwKHhYUzN
```

## 4. Steps to Extract Views

### Step 1: Get Access Token
1. Run: "Authentication" → "Get Access Token"
2. Token will be saved automatically

### Step 2: Upload Your Bundle
1. First upload the existing bundle ZIP file
2. Run: "App Bundle" → "Create App Bundle"
3. Use bundle name: `RevitViewExtractor4`

### Step 3: Create Activity
1. Run: "Activity" → "Create Activity"
2. Modify the request body:

```json
{
  "id": "ExtractViews",
  "commandLine": [
    "\"$(engine.path)\\\\revitcoreconsole.exe\" /i \"$(args[inputFile].path)\" /al \"$(appbundles[RevitViewExtractor4].path)\""
  ],
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
  "appbundles": ["{{dasNickName}}.RevitViewExtractor4+1"],
  "description": "Extract views from Revit"
}
```

### Step 4: Create Alias
1. Run: "Activity" → "Create Activity Alias"
2. Use alias name: `prod`
3. Version: 1

### Step 5: Upload Revit File
1. Create OSS bucket
2. Upload your `100.rvt` file
3. Get the URN

### Step 6: Create Workitem
1. Run: "Work Item" → "Create Work Item"
2. Use activity: `{{dasNickName}}.ExtractViews+prod`
3. Set input file URN and output location

## 5. Troubleshooting

### If "Cannot parse id" error:
1. Try using the activity without nickname:
   - Instead of: `2ceGWNLbW8QeWElmqiBGQAj2BLkNJuB8kNIWUCJHwKHhYUzN.ExtractViews+prod`
   - Try: `ExtractViews+prod`

2. Or use system activities:
   - `Autodesk.Nop+Latest` (for testing)

### Alternative: Use Pre-built Examples
1. Import "Design Automation for Revit Tutorial" collection
2. It includes working examples with shorter CLIENT_IDs

## 6. VSCode Extension Alternative

Install: "Autodesk Platform Services" extension
- Search in VSCode marketplace
- Provides GUI for Design Automation
- May handle long CLIENT_IDs better

## Expected Result

When successful, you'll get a `result.txt` file containing:
```json
{
  "views": [
    {"name": "Level 1", "type": "FloorPlan", "exportable": true},
    {"name": "3D View 1", "type": "3D", "exportable": true},
    ...
  ]
}
```