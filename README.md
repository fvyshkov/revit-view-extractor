# 🏗️ RevitViewExtractor

## 🚀 Overview

RevitViewExtractor is a powerful Revit plugin that enables advanced view management and extraction, both locally and in the cloud.

## ✨ Features

### 1. Local Revit Plugin Capabilities
- List all views in a Revit document
- Export selected views as images
- Categorize views by type and exportability

### 2. Cloud Processing
- Process Revit files at scale using Autodesk Design Automation
- Generate structured view reports
- Batch extract view information

## 🔧 Usage Examples

### 1. List Views in Revit Desktop
```csharp
// In Revit, click "List All Views" plugin button
// This will show a dialog with all document views
public void ListViews(Document doc)
{
    List<View> allViews = GetAllViews(doc);
    ShowViewsList(allViews);
}
```

### 2. Export a Specific View
```csharp
// Select and export a view as PNG
public void ExportSelectedView(Document doc, View selectedView)
{
    string outputPath = Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.Desktop), 
        "extracted_view.png"
    );
    ExportViewToImage(doc, selectedView, outputPath);
}
```

### 3. Cloud View Extraction
```python
# Python script for cloud processing
def extract_views_from_revit_file(revit_file_path):
    """
    Process Revit file in Autodesk Design Automation
    Returns structured view information
    """
    # Authenticate with Autodesk
    token = get_access_token()
    
    # Create workitem to process file
    workitem_id = create_workitem(
        activity_id="RevitViewExtractor",
        input_file=revit_file_path
    )
    
    # Retrieve view information
    view_report = get_workitem_result(workitem_id)
    return view_report
```

## 📊 View Analysis Details

- **Total Views**: Counts all views in the document
- **Exportable Views**: Identifies views that can be printed/exported
- **View Types**: 
  - Floor Plans
  - 3D Views
  - Elevations
  - Sections
  - Schedules
  - Drafting Views

## 🔍 View Filtering Criteria
- Excludes template views
- Filters out non-printable views
- Removes system and browser views

## 💻 Technologies

- **Languages**: C#, Python
- **Platforms**: 
  - Revit Desktop 2026
  - Autodesk Design Automation
- **APIs**: 
  - Revit API
  - Autodesk Forge Design Automation

## 🚀 Quick Start

1. Install Revit plugin
2. Configure Autodesk Forge credentials
3. Use local plugin or cloud processing scripts

## 📦 Installation

1. Clone repository
2. Build Visual Studio solution
3. Install `.addin` file in Revit
4. Configure Python environment

## 🤝 Contributing

Contributions welcome! Please read the contributing guidelines.

## 📄 License

[Specify your license]

---

**Automate Your Revit View Management!** 🏗️
