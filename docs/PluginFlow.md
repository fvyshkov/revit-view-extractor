## RevitViewExporter Plugin – Process Overview

### High-level overview
- **Goal**: Export Revit views as images and structured annotation data.
- **Outputs**: One PNG per view, `<View>.annotations.json`, and `export_log.txt` in `addin-results`.

### Architecture diagram
```mermaid
flowchart TD
  U[User in Revit] -->|Runs Export Views| P[RevitViewExporter Plugin]
  P --> D[(ActiveDocument)]
  P --> S[Settings/Config]
  P --> C{Collect Views}
  C -->|Filter/Prepare| V[View List]
  V --> L[Loop: per View]
  L --> B[Compute: crop box, scale, transforms]
  L --> A[Collect: visible elements & annotations]
  B --> T[Project to 2D viewport coords]
  A --> T
  T --> R[Render Bitmap]
  R --> IMG[[Write PNG]]
  A --> JSON[[Write <view>.annotations.json]]
  L --> LOG[[Append export_log.txt]]
  IMG --> OUT[(addin-results)]
  JSON --> OUT
  LOG --> OUT
```

### Runtime sequence
```mermaid
sequenceDiagram
  participant U as User
  participant R as Revit
  participant P as RevitViewExporter
  participant FS as File System

  U->>R: Start "Export Views"
  R->>P: Execute(IExternalCommandData)
  P->>P: Load config, choose output folder
  P->>R: Get ActiveDocument, collect views
  P->>P: Filter by type/discipline/visibility

  loop For each view
    P->>R: (Optional) Activate view
    P->>R: Read crop box, scale, orientation
    P->>R: Collect visible elements & annotations
    P->>P: Compute world→view 2D transform
    P->>R: Render view to bitmap
    P->>FS: Save "<View>.png"
    P->>FS: Save "<View>.annotations.json"
    P->>FS: Append export_log.txt
  end

  P-->>U: Success summary (counts, paths, errors if any)
```

### Data model (simplified)
```mermaid
classDiagram
  class ViewExport {
    string viewId
    string viewName
    string viewType
    int scale
    Bounds3D cropBox
    Matrix4 worldToView
  }

  class ExportedImage {
    string filePath
    int width
    int height
    int dpi
  }

  class Annotation {
    string elementId
    string category
    Bounds2D bbox2d
    Bounds3D bbox3d
    string text
    float rotation
    map~string, any~ properties
  }

  ViewExport "1" o-- "1" ExportedImage
  ViewExport "1" o-- "0..*" Annotation
```

### Notes
- Files are saved under `addin-results` at the repository root.
- The log file `export_log.txt` records view-level processing details.
- The process can also be triggered headlessly via `run_headless_export.bat` if supported.


