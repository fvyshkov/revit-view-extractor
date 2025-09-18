using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Windows.Forms;
using Autodesk.Revit.Attributes;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;
using RevitViewExporter.Forms;
using View = Autodesk.Revit.DB.View;
using Form = System.Windows.Forms.Form;

namespace RevitViewExporter.Commands
{
    [Transaction(TransactionMode.Manual)]
    public class ExportViewsCommand : IExternalCommand
    {
        public Result Execute(ExternalCommandData commandData, ref string message, ElementSet elements)
        {
            try
            {
                // Get the Revit application and document
                UIApplication uiapp = commandData.Application;
                UIDocument uidoc = uiapp.ActiveUIDocument;
                Document doc = uidoc.Document;

                // Get all views from the document
                List<View> views = GetExportableViews(doc);

                if (views.Count == 0)
                {
                    TaskDialog.Show("Warning", "No exportable views found in the document.");
                    return Result.Succeeded;
                }

                // Show the view selector dialog
                using (ViewSelectorForm form = new ViewSelectorForm(views))
                {
                    if (form.ShowDialog() == System.Windows.Forms.DialogResult.OK)
                    {
                        // Get selected views
                        List<View> selectedViews = form.SelectedViews;
                        
                        if (selectedViews.Count == 0)
                        {
                            TaskDialog.Show("Warning", "No views selected for export.");
                            return Result.Succeeded;
                        }

                        // Ask for export folder
                        System.Windows.Forms.FolderBrowserDialog folderDialog = new System.Windows.Forms.FolderBrowserDialog();
                        folderDialog.Description = "Select folder for exported images";
                        
                        if (folderDialog.ShowDialog() == System.Windows.Forms.DialogResult.OK)
                        {
                            string exportFolder = folderDialog.SelectedPath;
                            
                            // Export selected views
                            int exportedCount = ExportViewsToImages(doc, selectedViews, exportFolder);
                            
                            // Show success message
                            TaskDialog.Show("Success", $"Successfully exported {exportedCount} view(s) to:\n{exportFolder}");
                        }
                    }
                }

                return Result.Succeeded;
            }
            catch (Exception ex)
            {
                message = ex.Message;
                return Result.Failed;
            }
        }

        private List<View> GetExportableViews(Document doc)
        {
            // Get all views that can be exported
            FilteredElementCollector collector = new FilteredElementCollector(doc);
            collector.OfClass(typeof(View));
            
            List<View> exportableViews = new List<View>();
            
            foreach (View view in collector)
            {
                // Skip view templates, system views, and non-exportable views
                if (view.IsTemplate || view.ViewType == ViewType.SystemBrowser || 
                    view.ViewType == ViewType.ProjectBrowser || view.ViewType == ViewType.Internal ||
                    view.ViewType == ViewType.Undefined || !view.CanBePrinted)
                {
                    continue;
                }
                
                // Skip views with <3D> in the name (typically section boxes)
                if (view.Name.Contains("<3D>"))
                {
                    continue;
                }
                
                exportableViews.Add(view);
            }
            
            // Sort views by name
            return exportableViews.OrderBy(v => v.Name).ToList();
        }

        private int ExportViewsToImages(Document doc, List<View> views, string exportFolder)
        {
            int exportedCount = 0;
            
            // Create log file for debugging
            string logPath = Path.Combine(exportFolder, "export_log.txt");
            using (StreamWriter log = new StreamWriter(logPath, false, Encoding.UTF8))
            {
                log.WriteLine($"Export started at {DateTime.Now}");
                log.WriteLine($"Export folder: {exportFolder}");
                log.WriteLine($"Views to export: {views.Count}");
                log.WriteLine("----------------------------------------");
                log.Flush();
            
                // Create export options
                ImageExportOptions options = new ImageExportOptions();
                options.ZoomType = ZoomFitType.FitToPage;
                options.PixelSize = 2000; // Image width in pixels
                options.ImageResolution = ImageResolution.DPI_300;
                options.ExportRange = ExportRange.SetOfViews;
                options.HLRandWFViewsFileType = ImageFileType.PNG;
                options.ShadowViewsFileType = ImageFileType.PNG;
            
                // Create transaction for exporting
                using (Transaction t = new Transaction(doc, "Export Views to Images"))
                {
                    t.Start();
                
                // Создаем простую форму прогресса
                System.Windows.Forms.Form progressForm = new System.Windows.Forms.Form();
                progressForm.Text = "Exporting Views...";
                progressForm.Size = new System.Drawing.Size(400, 100);
                progressForm.StartPosition = System.Windows.Forms.FormStartPosition.CenterScreen;
                progressForm.FormBorderStyle = System.Windows.Forms.FormBorderStyle.FixedDialog;
                progressForm.MaximizeBox = false;
                progressForm.MinimizeBox = false;

                System.Windows.Forms.ProgressBar progressBar = new System.Windows.Forms.ProgressBar();
                progressBar.Minimum = 0;
                progressBar.Maximum = views.Count;
                progressBar.Value = 0;
                progressBar.Width = 360;
                progressBar.Location = new System.Drawing.Point(20, 20);

                System.Windows.Forms.Label progressLabel = new System.Windows.Forms.Label();
                progressLabel.Text = "Preparing...";
                progressLabel.Location = new System.Drawing.Point(20, 50);
                progressLabel.Width = 360;

                progressForm.Controls.Add(progressBar);
                progressForm.Controls.Add(progressLabel);
                progressForm.Show();
                
                // Export each view
                foreach (View view in views)
                {
                    log.WriteLine($"Exporting view: {view.Name}");
                    try
                    {
                        // Update progress
                        progressBar.Value = exportedCount + 1;
                        progressLabel.Text = $"Exporting {exportedCount + 1} of {views.Count}: {view.Name}";
                        System.Windows.Forms.Application.DoEvents();
                        
                        // Set the view to export
                        List<ElementId> viewSet = new List<ElementId> { view.Id };
                        options.SetViewsAndSheets(viewSet);
                        
                        // Set the file name (sanitize view name)
                        string fileName = SanitizeFileName(view.Name);
                        string filePath = Path.Combine(exportFolder, fileName);
                        
                        // Track existing PNGs to detect the actual file that Revit creates
                        var beforePngs = new HashSet<string>(Directory.GetFiles(exportFolder, "*.png"), StringComparer.OrdinalIgnoreCase);

                        // Export the view
                        options.FilePath = filePath;
                        doc.ExportImage(options);

                        // Detect newly created PNG for this export
                        string actualImagePath = filePath;
                        try
                        {
                            var afterPngs = Directory.GetFiles(exportFolder, "*.png");
                            string newest = null;
                            DateTime newestTime = DateTime.MinValue;
                            foreach (var p in afterPngs)
                            {
                                if (!beforePngs.Contains(p))
                                {
                                    var ts = File.GetLastWriteTime(p);
                                    if (ts > newestTime)
                                    {
                                        newestTime = ts;
                                        newest = p;
                                    }
                                }
                            }
                            if (!string.IsNullOrEmpty(newest))
                            {
                                actualImagePath = newest;
                            }
                        }
                        catch (Exception ex)
                        {
                            log.WriteLine($"WARN: Failed to detect actual PNG path: {ex.Message}");
                        }

                        // Fallback: if the detected path doesn't exist, try to find the best matching PNG
                        try
                        {
                            if (!File.Exists(actualImagePath))
                            {
                                var allPngs = Directory.GetFiles(exportFolder, "*.png");
                                // Prefer filenames containing the view name
                                string best = allPngs
                                    .OrderByDescending(p => File.GetLastWriteTime(p))
                                    .FirstOrDefault(p => Path.GetFileName(p).IndexOf(view.Name, StringComparison.OrdinalIgnoreCase) >= 0);
                                if (string.IsNullOrEmpty(best) && allPngs.Length > 0)
                                {
                                    best = allPngs.OrderByDescending(p => File.GetLastWriteTime(p)).First();
                                }
                                if (!string.IsNullOrEmpty(best))
                                {
                                    actualImagePath = best;
                                }
                            }
                        }
                        catch (Exception ex)
                        {
                            log.WriteLine($"WARN: PNG fallback search failed: {ex.Message}");
                        }
                        
                        // After image export, get viewport corner coordinates for reference
                        var cornerCoords = GetViewportCornerCoordinates(doc, view, log);
                        
                        // After image export, also export annotations JSON with pixel-space boxes
                        var annotations = GetWindowTagAnnotations(doc, view, log);
                        log.WriteLine($"Found {annotations.Count} annotations");
                        string jsonPath = Path.Combine(exportFolder, Path.GetFileNameWithoutExtension(fileName) + ".annotations.json");

                        // Read actual image size to compute mapping
                        int imgW = 0, imgH = 0;
                        try
                        {
                            using (var bmp = System.Drawing.Image.FromFile(actualImagePath))
                            {
                                imgW = bmp.Width;
                                imgH = bmp.Height;
                            }
                        }
                        catch (Exception ex)
                        {
                            log.WriteLine($"WARN: Failed to read image size: {ex.Message}");
                        }

                        // Log annotation info
                        log.WriteLine($"View: {view.Name}");
                        log.WriteLine($"  Image: {actualImagePath} ({imgW}x{imgH})");
                        log.WriteLine($"  JSON: {jsonPath}");
                        log.WriteLine($"  Found {annotations.Count} annotations");

                        var typeCounts = annotations
                            .GroupBy(a => a.Type)
                            .Select(g => $"{g.Key}: {g.Count()}")
                            .ToList();
                        if (typeCounts.Any())
                        {
                            log.WriteLine($"  Types: {string.Join(", ", typeCounts)}");
                        }
                        log.Flush();

                        // Provide crop box for mapping
                        var crop = view.CropBox;
                        WriteAnnotationsJson(jsonPath, view, annotations, imgW, imgH, crop, actualImagePath, cornerCoords);

                        exportedCount++;
                    }
                    catch (Exception ex)
                    {
                        // Log error and show dialog
                        log.WriteLine($"ERROR: Failed to export view '{view.Name}': {ex.Message}");
                        log.WriteLine($"  Stack trace: {ex.StackTrace}");
                        log.Flush();
                        
                        TaskDialog.Show("Export Error", $"Error exporting view '{view.Name}': {ex.Message}");
                    }
                }
                
                    // Close progress dialog
                    progressForm.Close();
                    
                    t.Commit();
                }
                
                log.WriteLine("----------------------------------------");
                log.WriteLine($"Export completed at {DateTime.Now}");
                log.WriteLine($"Total views exported: {exportedCount}");
                log.Close();
            }
            
            return exportedCount;
        }

        private class AnnotationBox
        {
            public string Type { get; set; }
            public string ElementId { get; set; }
            public string TagId { get; set; }
            public string Text { get; set; }
            public XYZ Min { get; set; }
            public XYZ Max { get; set; }
        }

        private List<AnnotationBox> GetWindowTagAnnotations(Document doc, View view, StreamWriter log)
        {
            var result = new List<AnnotationBox>();

            // Collect all tags visible in the view
            var collector = new FilteredElementCollector(doc, view.Id)
                .WhereElementIsNotElementType()
                .OfClass(typeof(IndependentTag))
                .ToElements();

            foreach (var el in collector)
            {
                var tag = el as IndependentTag;
                log.WriteLine($"tag: {tag}");
                tag.get_BoundingBox(view);
                log.WriteLine($"tag bounding box: {tag.get_BoundingBox(view)}");
                ///////////////////
                XYZ tagPosition2D = tag.TagHeadPosition;
                double x = tagPosition2D.X;
                double y = tagPosition2D.Y;
                log.WriteLine($"tag position 2D: ({x}, {y})");
                //TaskDialog.Show("Revit",messageInfo);
                ///////////////////

                if (tag == null)
                {
                    continue;
                }

                // Get tag category - include windows, doors, and other common tags
                string tagType = "UnknownTag";
                bool isValidTag = false;
                
                if (tag.Category == null)
                {
                    continue;
                }
                
                // Check for various tag categories
                if (tag.Category.Id == new ElementId(BuiltInCategory.OST_WindowTags))
                {
                    tagType = "WindowTag";
                    isValidTag = true;
                }
                else if (tag.Category.Id == new ElementId(BuiltInCategory.OST_DoorTags))
                {
                    tagType = "DoorTag";
                    isValidTag = true;
                }
                else if (tag.Category.Id == new ElementId(BuiltInCategory.OST_RoomTags))
                {
                    tagType = "RoomTag";
                    isValidTag = true;
                }
                else if (tag.Category.Id == new ElementId(BuiltInCategory.OST_WallTags))
                {
                    tagType = "WallTag";
                    isValidTag = true;
                }
                else
                {
                    // Include all other tags as well
                    tagType = tag.Category.Name;
                    isValidTag = true;
                }
                
                if (!isValidTag)
                {
                    continue;
                }

                // Get 2D coordinates in view plane instead of 3D model coordinates
                BoundingBoxXYZ bb3D = tag.get_BoundingBox(view);
                if (bb3D == null)
                {
                    continue;
                }

                // Use the tag's actual bounding box in the view coordinate system
                // This gives us the real screen coordinates where the tag appears
                BoundingBoxXYZ tagBB = tag.get_BoundingBox(view);
                if (tagBB == null)
                {
                    continue; // Skip if we can't get tag bounds
                }

                // Get view's crop box for reference
                BoundingBoxXYZ cropBox = view.CropBox;
                if (cropBox == null)
                {
                    continue; // Skip if no crop box
                }

                // Get tag position in MODEL coordinates (not view coordinates)
                // This will ensure consistency with viewport corners
                XYZ tagHeadPosition = tag.TagHeadPosition;
                
                // Get crop box dimensions in model coordinates
                XYZ cropMin = cropBox.Min;
                XYZ cropMax = cropBox.Max;
                
                // DEBUG: Log the coordinates for comparison
                using (var debugLog = new System.IO.StreamWriter(System.IO.Path.Combine(System.IO.Path.GetDirectoryName(System.Reflection.Assembly.GetExecutingAssembly().Location), "debug_coords.txt"), true, System.Text.Encoding.UTF8))
                {
                    debugLog.WriteLine($"=== COORDINATE COMPARISON ===\nTag: {tag.Id}\nText: {tag.TagText}\n");
                    debugLog.WriteLine($"TagHeadPosition: ({tagHeadPosition.X:F3}, {tagHeadPosition.Y:F3}, {tagHeadPosition.Z:F3})");
                    debugLog.WriteLine($"CropBox.Min: ({cropMin.X:F3}, {cropMin.Y:F3}, {cropMin.Z:F3})");
                    debugLog.WriteLine($"CropBox.Max: ({cropMax.X:F3}, {cropMax.Y:F3}, {cropMax.Z:F3})");
                    
                    // Check if the tag is within the crop box
                    bool isXInRange = tagHeadPosition.X >= cropMin.X && tagHeadPosition.X <= cropMax.X;
                    bool isYInRange = tagHeadPosition.Y >= cropMin.Y && tagHeadPosition.Y <= cropMax.Y;
                    bool isZInRange = tagHeadPosition.Z >= cropMin.Z && tagHeadPosition.Z <= cropMax.Z;
                    debugLog.WriteLine($"Is tag within crop box? X: {isXInRange}, Y: {isYInRange}, Z: {isZInRange}");
                    debugLog.WriteLine("===========================\n");
                }
                
                // Use tag head position for center, then create a box around it
                // For elevation views: X is horizontal, Z is vertical
                double tagSize = 3.0; // Size in model units (adjust as needed)
                
                // Create a box around the tag head position
                // Ensure the box is within the crop box bounds
                double tagX = Math.Max(cropMin.X + tagSize, Math.Min(cropMax.X - tagSize, tagHeadPosition.X));
                double relativeX = tagX - tagSize;
                double relativeY = Math.Max(cropMin.Z, Math.Min(cropMax.Z, tagHeadPosition.Z)); // Use Z for elevation vertical coordinate
                
                // Log Y coordinate for debugging
                double relativeY_usingY = tagHeadPosition.Y;
                
                // Calculate max coordinates
                // Ensure the box is within the crop box bounds and has width
                double maxX = tagX + tagSize;
                double maxY = Math.Max(cropMin.Z, Math.Min(cropMax.Z, tagHeadPosition.Z + tagSize)); // Make box taller than wide
                
                // Make sure box has width even at the edges of the view
                if (Math.Abs(maxX - relativeX) < 1.0)
                {
                    // If at left edge, move max right
                    if (Math.Abs(relativeX - cropMin.X) < 0.1)
                        maxX = relativeX + tagSize;
                    // If at right edge, move min left
                    else if (Math.Abs(maxX - cropMax.X) < 0.1)
                        relativeX = maxX - tagSize;
                }
                
                // Create 3D coordinates with all three dimensions (X, Y, Z)
                XYZ min2D = new XYZ(relativeX, tagHeadPosition.Y, relativeY);
                XYZ max2D = new XYZ(maxX, tagHeadPosition.Y, maxY);

                // Determine host element and tag text
                string text = string.Empty;
                string hostElementId = string.Empty;

                // Prefer tag text if available
                try
                {
                    text = tag.TagText;
                }
                catch
                {
                    text = string.Empty;
                }

                // Try to get tagged local element ids (host elements)
                try
                {
                    var localIds = tag.GetTaggedLocalElementIds(); // ISet<ElementId> in newer API
                    if (localIds != null && localIds.Count > 0)
                    {
                        var firstId = localIds.First();
                        if (firstId != ElementId.InvalidElementId)
                        {
                            hostElementId = firstId.ToString();
                        }
                    }
                }
                catch
                {
                    // ignore if API not available
                }

                // MAXIMUM DEBUG for each tag (after text is determined) - write to log file
                string tagDebugPath = System.IO.Path.Combine(System.IO.Path.GetDirectoryName(System.Reflection.Assembly.GetExecutingAssembly().Location), "debug_tags.txt");
                using (var tagLog = new System.IO.StreamWriter(tagDebugPath, true, System.Text.Encoding.UTF8)) // append mode
                {
                    tagLog.WriteLine($"--- TAG {tag.Id} DEBUG ---");
                    tagLog.WriteLine($"Tag Text: '{text}'");
                    tagLog.WriteLine($"Tag Head Position: ({tag.TagHeadPosition.X:F2}, {tag.TagHeadPosition.Y:F2}, {tag.TagHeadPosition.Z:F2})");
                    tagLog.WriteLine($"Tag Head Position (MODEL): ({tagHeadPosition.X:F2}, {tagHeadPosition.Y:F2}, {tagHeadPosition.Z:F2})");
                    tagLog.WriteLine($"Tag Box Min (MODEL): ({relativeX:F2}, {tagHeadPosition.Y:F2}, {relativeY:F2})");
                    tagLog.WriteLine($"Tag Box Max (MODEL): ({maxX:F2}, {tagHeadPosition.Y:F2}, {maxY:F2})");
                    tagLog.WriteLine($"Tag Box Size (MODEL): W={maxX - relativeX:F2}, H=0, D={maxY - relativeY:F2}");
                    tagLog.WriteLine($"Crop BoundingBox Min: ({cropMin.X:F2}, {cropMin.Y:F2}, {cropMin.Z:F2})");
                    tagLog.WriteLine($"Crop BoundingBox Max: ({cropMax.X:F2}, {cropMax.Y:F2}, {cropMax.Z:F2})");
                    tagLog.WriteLine($"Relative X (using X): {relativeX:F3}");
                    tagLog.WriteLine($"Relative Y (using Z): {relativeY:F3}");
                    tagLog.WriteLine($"Relative Y (using Y): {relativeY_usingY:F3}");
                    bool isInsideCrop = (relativeX >= 0 && relativeX <= 1 && relativeY >= 0 && relativeY <= 1);
                    tagLog.WriteLine($"Tag is {(isInsideCrop ? "INSIDE" : "OUTSIDE")} crop box");
                    tagLog.WriteLine("-------------------------");
                    tagLog.Flush();
                }

                // Store 2D coordinates
                result.Add(new AnnotationBox
                {
                    Type = tagType,
                    ElementId = hostElementId,
                    TagId = tag.Id.ToString(),
                    Text = text ?? string.Empty,
                    Min = min2D,  // 2D coordinates in view plane
                    Max = max2D   // 2D coordinates in view plane
                });
            }

            return result;
        }

        private static string EscapeJsonString(string s)
        {
            if (string.IsNullOrEmpty(s)) return string.Empty;
            return s
                .Replace("\\", "\\\\")
                .Replace("\"", "\\\"")
                .Replace("\n", "\\n")
                .Replace("\r", "\\r")
                .Replace("\t", "\\t");
        }

        private void WriteAnnotationsJson(string path, View view, List<AnnotationBox> annotations, int imgW, int imgH, BoundingBoxXYZ crop, string imagePath, Dictionary<string, XYZ> cornerCoords)
        {
            // MAXIMUM DEBUG INFO - write to log file
            string debugLogPath = System.IO.Path.Combine(System.IO.Path.GetDirectoryName(path), "debug_coordinates.txt");
            using (var debugLog = new System.IO.StreamWriter(debugLogPath, false, System.Text.Encoding.UTF8))
            {
                debugLog.WriteLine("=== MAXIMUM DEBUG INFO ===");
                debugLog.WriteLine($"View: {view.Name} (ID: {view.Id})");
                debugLog.WriteLine($"View Type: {view.ViewType}");
                debugLog.WriteLine($"Image Size: {imgW} x {imgH}");
                
                // View coordinate system info
                debugLog.WriteLine($"View Origin: ({view.Origin.X:F2}, {view.Origin.Y:F2}, {view.Origin.Z:F2})");
                debugLog.WriteLine($"View Direction: ({view.ViewDirection.X:F2}, {view.ViewDirection.Y:F2}, {view.ViewDirection.Z:F2})");
                debugLog.WriteLine($"View Up Direction: ({view.UpDirection.X:F2}, {view.UpDirection.Y:F2}, {view.UpDirection.Z:F2})");
                debugLog.WriteLine($"View Right Direction: ({view.RightDirection.X:F2}, {view.RightDirection.Y:F2}, {view.RightDirection.Z:F2})");
                
                // Crop box info
                if (crop != null)
                {
                    debugLog.WriteLine($"Export Crop Box Min: ({crop.Min.X:F2}, {crop.Min.Y:F2}, {crop.Min.Z:F2})");
                    debugLog.WriteLine($"Export Crop Box Max: ({crop.Max.X:F2}, {crop.Max.Y:F2}, {crop.Max.Z:F2})");
                    debugLog.WriteLine($"Export Crop Box Size: W={crop.Max.X - crop.Min.X:F2}, H={crop.Max.Y - crop.Min.Y:F2}, D={crop.Max.Z - crop.Min.Z:F2}");
                }
                
                // View CropBox info (different from export crop)
                BoundingBoxXYZ viewCrop = view.CropBox;
                if (viewCrop != null)
                {
                    debugLog.WriteLine($"View CropBox Min: ({viewCrop.Min.X:F2}, {viewCrop.Min.Y:F2}, {viewCrop.Min.Z:F2})");
                    debugLog.WriteLine($"View CropBox Max: ({viewCrop.Max.X:F2}, {viewCrop.Max.Y:F2}, {viewCrop.Max.Z:F2})");
                    debugLog.WriteLine($"View CropBox Size: W={viewCrop.Max.X - viewCrop.Min.X:F2}, H={viewCrop.Max.Y - viewCrop.Min.Y:F2}, D={viewCrop.Max.Z - viewCrop.Min.Z:F2}");
                }
                
                debugLog.WriteLine($"Total Annotations: {annotations.Count}");
                debugLog.WriteLine("=========================");
                debugLog.Flush();
            }

            var sb = new StringBuilder();
            sb.Append("{\n");
            sb.AppendFormat("  \"viewId\": \"{0}\",\n", EscapeJsonString(view.Id.ToString()));
            sb.AppendFormat("  \"viewName\": \"{0}\",\n", EscapeJsonString(view.Name));
            sb.AppendFormat("  \"viewType\": \"{0}\",\n", view.ViewType.ToString());
            sb.AppendFormat("  \"imageWidth\": {0},\n", imgW);
            sb.AppendFormat("  \"imageHeight\": {0},\n", imgH);
            if (!string.IsNullOrEmpty(imagePath))
            {
                sb.AppendFormat("  \"imagePath\": \"{0}\",\n", EscapeJsonString(imagePath));
            }
            if (crop != null)
            {
                sb.Append("  \"cropBox\": {\n");
                sb.AppendFormat("    \"min\": {{ \"x\": {0}, \"y\": {1}, \"z\": {2} }},\n", crop.Min.X.ToString(System.Globalization.CultureInfo.InvariantCulture), crop.Min.Y.ToString(System.Globalization.CultureInfo.InvariantCulture), crop.Min.Z.ToString(System.Globalization.CultureInfo.InvariantCulture));
                sb.AppendFormat("    \"max\": {{ \"x\": {0}, \"y\": {1}, \"z\": {2} }}\n", crop.Max.X.ToString(System.Globalization.CultureInfo.InvariantCulture), crop.Max.Y.ToString(System.Globalization.CultureInfo.InvariantCulture), crop.Max.Z.ToString(System.Globalization.CultureInfo.InvariantCulture));
                sb.Append("  },\n");
            }
            
            // Add viewport corner coordinates for reference mapping
            if (cornerCoords != null && cornerCoords.Count > 0)
            {
                sb.Append("  \"viewportCorners\": {\n");
                bool first = true;
                foreach (var kvp in cornerCoords)
                {
                    if (!first) sb.Append(",\n");
                    sb.AppendFormat("    \"{0}\": {{ \"x\": {1}, \"y\": {2}, \"z\": {3} }}", 
                        kvp.Key, 
                        kvp.Value.X.ToString(System.Globalization.CultureInfo.InvariantCulture),
                        kvp.Value.Y.ToString(System.Globalization.CultureInfo.InvariantCulture),
                        kvp.Value.Z.ToString(System.Globalization.CultureInfo.InvariantCulture));
                    first = false;
                }
                sb.Append("\n  },\n");
            }
            sb.Append("  \"annotations\": [\n");
            for (int i = 0; i < annotations.Count; i++)
            {
                var a = annotations[i];
                sb.Append("    {\n");
                sb.AppendFormat("      \"type\": \"{0}\",\n", EscapeJsonString(a.Type));
                sb.AppendFormat("      \"elementId\": \"{0}\",\n", EscapeJsonString(a.ElementId ?? string.Empty));
                sb.AppendFormat("      \"tagId\": \"{0}\",\n", EscapeJsonString(a.TagId ?? string.Empty));
                sb.AppendFormat("      \"text\": \"{0}\",\n", EscapeJsonString(a.Text ?? string.Empty));
                sb.Append("      \"bbox3D\": {\n");
                sb.AppendFormat("        \"min\": {{ \"x\": {0}, \"y\": {1}, \"z\": {2} }},\n", 
                    a.Min.X.ToString(System.Globalization.CultureInfo.InvariantCulture), 
                    a.Min.Y.ToString(System.Globalization.CultureInfo.InvariantCulture),
                    a.Min.Z.ToString(System.Globalization.CultureInfo.InvariantCulture));
                sb.AppendFormat("        \"max\": {{ \"x\": {0}, \"y\": {1}, \"z\": {2} }}\n", 
                    a.Max.X.ToString(System.Globalization.CultureInfo.InvariantCulture), 
                    a.Max.Y.ToString(System.Globalization.CultureInfo.InvariantCulture),
                    a.Max.Z.ToString(System.Globalization.CultureInfo.InvariantCulture));
                sb.Append("      }\n");
                
                // Also keep the old bbox2D for backward compatibility
                sb.Append("      \"bbox2D\": {\n");
                sb.AppendFormat("        \"min\": {{ \"x\": {0}, \"y\": {1} }},\n", a.Min.X.ToString(System.Globalization.CultureInfo.InvariantCulture), a.Min.Z.ToString(System.Globalization.CultureInfo.InvariantCulture));
                sb.AppendFormat("        \"max\": {{ \"x\": {0}, \"y\": {1} }}\n", a.Max.X.ToString(System.Globalization.CultureInfo.InvariantCulture), a.Max.Z.ToString(System.Globalization.CultureInfo.InvariantCulture));
                sb.Append("      }\n");
                // Convert 2D view coordinates to pixel coordinates
                if (crop != null && imgW > 0 && imgH > 0)
                {
                    // Get crop box bounds in view coordinates
                    XYZ origin = view.Origin;
                    XYZ right = view.RightDirection;
                    XYZ up = view.UpDirection;

                    // Project crop box corners to view coordinates
                    List<XYZ> cropCorners = new List<XYZ>();
                    foreach (double cx in new[] { crop.Min.X, crop.Max.X })
                    foreach (double cy in new[] { crop.Min.Y, crop.Max.Y })
                    foreach (double cz in new[] { crop.Min.Z, crop.Max.Z })
                        cropCorners.Add(new XYZ(cx, cy, cz));

                    double cuMin = double.PositiveInfinity, cvMin = double.PositiveInfinity;
                    double cuMax = double.NegativeInfinity, cvMax = double.NegativeInfinity;
                    foreach (var corner in cropCorners)
                    {
                        XYZ delta = corner - origin;
                        double u = delta.DotProduct(right);
                        double v = delta.DotProduct(up);
                        if (u < cuMin) cuMin = u; if (u > cuMax) cuMax = u;
                        if (v < cvMin) cvMin = v; if (v > cvMax) cvMax = v;
                    }
                    double du = Math.Max(1e-9, cuMax - cuMin);
                    double dv = Math.Max(1e-9, cvMax - cvMin);

                    // Tag coordinates are already in 2D view space (a.Min.X, a.Min.Y)
                    double tagUMin = a.Min.X;
                    double tagVMin = a.Min.Y;
                    double tagUMax = a.Max.X;
                    double tagVMax = a.Max.Y;

                    // Normalize to [0,1] range
                    double uNorm1 = (tagUMin - cuMin) / du;
                    double vNorm1 = 1.0 - (tagVMin - cvMin) / dv; // flip Y for image coordinates
                    double uNorm2 = (tagUMax - cuMin) / du;
                    double vNorm2 = 1.0 - (tagVMax - cvMin) / dv;
                    
                    double uMinN = Math.Min(uNorm1, uNorm2);
                    double uMaxN = Math.Max(uNorm1, uNorm2);
                    double vMinN = Math.Min(vNorm1, vNorm2);
                    double vMaxN = Math.Max(vNorm1, vNorm2);

                    // Add normalized coordinates
                    sb.Append(",\n");
                    sb.Append("      \"uvBBox\": {\n");
                    sb.AppendFormat("        \"min\": {{ \"u\": {0}, \"v\": {1} }},\n", uMinN.ToString(System.Globalization.CultureInfo.InvariantCulture), vMinN.ToString(System.Globalization.CultureInfo.InvariantCulture));
                    sb.AppendFormat("        \"max\": {{ \"u\": {0}, \"v\": {1} }}\n", uMaxN.ToString(System.Globalization.CultureInfo.InvariantCulture), vMaxN.ToString(System.Globalization.CultureInfo.InvariantCulture));
                    sb.Append("      }\n");

                    // Convert to pixel coordinates
                    int px1 = Math.Max(0, Math.Min(imgW-1, (int)Math.Round(uMinN * imgW)));
                    int px2 = Math.Max(0, Math.Min(imgW-1, (int)Math.Round(uMaxN * imgW)));
                    int py1 = Math.Max(0, Math.Min(imgH-1, (int)Math.Round(vMinN * imgH)));
                    int py2 = Math.Max(0, Math.Min(imgH-1, (int)Math.Round(vMaxN * imgH)));

                    // Add pixel coordinates if box is large enough
                    if (Math.Abs(px2 - px1) >= 2 && Math.Abs(py2 - py1) >= 2)
                    {
                        sb.Append(",\n");
                        sb.Append("      \"pixelBBox\": {\n");
                        sb.AppendFormat("        \"min\": {{ \"x\": {0}, \"y\": {1} }},\n", Math.Min(px1, px2), Math.Min(py1, py2));
                        sb.AppendFormat("        \"max\": {{ \"x\": {0}, \"y\": {1} }}\n", Math.Max(px1, px2), Math.Max(py1, py2));
                        sb.Append("      }\n");
                    }

                    // Also export viewport-based mapping using the same basis as viewportCorners (X,Z)
                    if (cornerCoords != null && cornerCoords.Count > 0)
                    {
                        XYZ tl = cornerCoords.ContainsKey("TopLeft") ? cornerCoords["TopLeft"] : null;
                        XYZ tr = cornerCoords.ContainsKey("TopRight") ? cornerCoords["TopRight"] : null;
                        XYZ bl = cornerCoords.ContainsKey("BottomLeft") ? cornerCoords["BottomLeft"] : null;
                        if (tl != null && tr != null && bl != null)
                        {
                            double tlx = tl.X; double trx = tr.X; double tlz = tl.Z; double blz = bl.Z;
                            // We're now using MODEL coordinates for both viewport corners and annotations
                            // For elevation views: X is horizontal, Z is vertical
                            double tagXMin = a.Min.X; // X coordinate in model
                            double tagZMin = a.Min.Y; // Y field now stores Z coordinate (vertical)
                            double tagXMax = a.Max.X; // X coordinate in model
                            double tagZMax = a.Max.Y; // Y field now stores Z coordinate (vertical)

                            // Calculate normalized coordinates in viewport space
                            // For X (horizontal): 0 = left edge, 1 = right edge
                            double uVp1 = (tagXMin - tlx) / Math.Max(1e-9, (trx - tlx));
                            double uVp2 = (tagXMax - tlx) / Math.Max(1e-9, (trx - tlx));
                            // For Z (vertical): 0 = bottom edge, 1 = top edge
                            double vVp1 = (tagZMin - blz) / Math.Max(1e-9, (tlz - blz));
                            double vVp2 = (tagZMax - blz) / Math.Max(1e-9, (tlz - blz));

                            double uVpMin = Math.Min(uVp1, uVp2); double uVpMax = Math.Max(uVp1, uVp2);
                            double vVpMin = Math.Min(vVp1, vVp2); double vVpMax = Math.Max(vVp1, vVp2);

                            // clamp to [0,1]
                            uVpMin = Math.Max(0.0, Math.Min(1.0, uVpMin));
                            uVpMax = Math.Max(0.0, Math.Min(1.0, uVpMax));
                            vVpMin = Math.Max(0.0, Math.Min(1.0, vVpMin));
                            vVpMax = Math.Max(0.0, Math.Min(1.0, vVpMax));

                            // write bboxViewport
                            sb.Append(",\n");
                            sb.Append("      \"bboxViewport\": {\n");
                            sb.AppendFormat("        \"min\": {{ \"u\": {0}, \"v\": {1} }},\n", uVpMin.ToString(System.Globalization.CultureInfo.InvariantCulture), vVpMin.ToString(System.Globalization.CultureInfo.InvariantCulture));
                            sb.AppendFormat("        \"max\": {{ \"u\": {0}, \"v\": {1} }}\n", uVpMax.ToString(System.Globalization.CultureInfo.InvariantCulture), vVpMax.ToString(System.Globalization.CultureInfo.InvariantCulture));
                            sb.Append("      }\n");

                            // pixelViewport
                            int pvx1 = Math.Max(0, Math.Min(imgW - 1, (int)Math.Round(uVpMin * imgW)));
                            int pvx2 = Math.Max(0, Math.Min(imgW - 1, (int)Math.Round(uVpMax * imgW)));
                            int pvy1 = Math.Max(0, Math.Min(imgH - 1, (int)Math.Round((1.0 - vVpMax) * imgH)));
                            int pvy2 = Math.Max(0, Math.Min(imgH - 1, (int)Math.Round((1.0 - vVpMin) * imgH)));

                            if (Math.Abs(pvx2 - pvx1) >= 1 && Math.Abs(pvy2 - pvy1) >= 1)
                            {
                                sb.Append(",\n");
                                sb.Append("      \"pixelViewport\": {\n");
                                sb.AppendFormat("        \"min\": {{ \"x\": {0}, \"y\": {1} }},\n", Math.Min(pvx1, pvx2), Math.Min(pvy1, pvy2));
                                sb.AppendFormat("        \"max\": {{ \"x\": {0}, \"y\": {1} }}\n", Math.Max(pvx1, pvx2), Math.Max(pvy1, pvy2));
                                sb.Append("      }\n");
                            }
                        }
                    }
                }
                sb.Append("    }");
                if (i < annotations.Count - 1) sb.Append(",");
                sb.Append("\n");
            }
            sb.Append("  ]\n");
            sb.Append("}\n");

            File.WriteAllText(path, sb.ToString(), Encoding.UTF8);
        }

        private string SanitizeFileName(string fileName)
        {
            // Replace invalid file name characters
            foreach (char c in Path.GetInvalidFileNameChars())
            {
                fileName = fileName.Replace(c, '_');
            }
            
            // Add .png extension if not present
            if (!fileName.EndsWith(".png", StringComparison.OrdinalIgnoreCase))
            {
                fileName += ".png";
            }
            
            return fileName;
        }

        private Dictionary<string, XYZ> GetViewportCornerCoordinates(Document doc, View view, StreamWriter log)
        {
            var corners = new Dictionary<string, XYZ>();
            
            try
            {
                // Get the view's crop box which defines the viewport boundaries
                BoundingBoxXYZ cropBox = view.CropBox;
                if (cropBox == null)
                {
                    log.WriteLine("WARN: View has no crop box");
                    return corners;
                }

                // Get crop box corners in model coordinates
                XYZ cropMin = cropBox.Min;
                XYZ cropMax = cropBox.Max;
                
                // For elevation views, we need X and Z coordinates (Y is depth)
                // Define the 4 corners of the viewport using the SAME coordinate system as annotations
                corners["TopLeft"] = new XYZ(cropMin.X, cropMin.Y, cropMax.Z);
                corners["TopRight"] = new XYZ(cropMax.X, cropMin.Y, cropMax.Z);
                corners["BottomLeft"] = new XYZ(cropMin.X, cropMin.Y, cropMin.Z);
                corners["BottomRight"] = new XYZ(cropMax.X, cropMin.Y, cropMin.Z);
                
                // Log the corner coordinates
                log.WriteLine("=== VIEWPORT CORNER COORDINATES ===");
                log.WriteLine($"Crop Box Min: ({cropMin.X:F3}, {cropMin.Y:F3}, {cropMin.Z:F3})");
                log.WriteLine($"Crop Box Max: ({cropMax.X:F3}, {cropMax.Y:F3}, {cropMax.Z:F3})");
                log.WriteLine($"TopLeft (X,Z):     ({corners["TopLeft"].X:F3}, {corners["TopLeft"].Z:F3})");
                log.WriteLine($"TopRight (X,Z):    ({corners["TopRight"].X:F3}, {corners["TopRight"].Z:F3})");
                log.WriteLine($"BottomLeft (X,Z):  ({corners["BottomLeft"].X:F3}, {corners["BottomLeft"].Z:F3})");
                log.WriteLine($"BottomRight (X,Z): ({corners["BottomRight"].X:F3}, {corners["BottomRight"].Z:F3})");
                log.WriteLine("===================================");
            }
            catch (Exception ex)
            {
                log.WriteLine($"ERROR getting viewport corners: {ex.Message}");
            }
            
            return corners;
        }
    }
}
