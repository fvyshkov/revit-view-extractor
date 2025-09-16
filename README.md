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

## 🔧 Command-Line Utilities

### List Views
```bash
# List all views in a Revit file
python scripts/list_views.py 100.rvt

# List only Floor Plan views
python scripts/list_views.py 100.rvt --type FloorPlan

# List only exportable views in JSON format
python scripts/list_views.py 100.rvt --exportable --json
```

### Export Views
```bash
# Export a specific view as PNG
python scripts/export_view.py 100.rvt "Level 1"

# Export a specific view with custom output and format
python scripts/export_view.py 100.rvt "3D View 1" --output custom_view.jpg --format jpg
```

### Batch Processing
```bash
# Process all Revit files in a directory
python scripts/batch_process.py /path/to/revit/files

# Batch export only Floor Plan views as PDF
python scripts/batch_process.py /path/to/revit/files --type FloorPlan --format pdf

# Batch process with parallel workers and output directory
python scripts/batch_process.py /path/to/revit/files --output-dir exports --workers 10
```

### Upload and Process
```bash
# Upload and process a Revit file in the cloud
python scripts/upload_and_process.py 100.rvt

# Filter views by type
python scripts/upload_and_process.py 100.rvt --type FloorPlan

# Show only exportable views in JSON
python scripts/upload_and_process.py 100.rvt --exportable --json
```

## 🔧 Technologies

- **Languages**: C#, Python
- **Platforms**: 
  - Revit Desktop 2026
  - Autodesk Design Automation
- **APIs**: 
  - Revit API
  - Autodesk Forge Design Automation

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
