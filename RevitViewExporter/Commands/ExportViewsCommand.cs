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
                        
                        // After image export, also export annotations JSON with pixel-space boxes
                        var annotations = GetWindowTagAnnotations(doc, view);
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
                        WriteAnnotationsJson(jsonPath, view, annotations, imgW, imgH, crop, actualImagePath);

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

        private List<AnnotationBox> GetWindowTagAnnotations(Document doc, View view)
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

                // Bounding box in model coordinates for this view
                BoundingBoxXYZ bb = tag.get_BoundingBox(view);
                if (bb == null)
                {
                    continue;
                }

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

                // Fallback: if no text was resolved, keep empty string
                result.Add(new AnnotationBox
                {
                    Type = tagType,
                    ElementId = hostElementId,
                    TagId = tag.Id.ToString(),
                    Text = text ?? string.Empty,
                    Min = bb.Min,
                    Max = bb.Max
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

        private void WriteAnnotationsJson(string path, View view, List<AnnotationBox> annotations, int imgW, int imgH, BoundingBoxXYZ crop, string imagePath)
        {
            var sb = new StringBuilder();
            sb.Append("{\n");
            sb.AppendFormat("  \"viewId\": \"{0}\",\n", EscapeJsonString(view.Id.ToString()));
            sb.AppendFormat("  \"viewName\": \"{0}\",\n", EscapeJsonString(view.Name));
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
            sb.Append("  \"annotations\": [\n");
            for (int i = 0; i < annotations.Count; i++)
            {
                var a = annotations[i];
                sb.Append("    {\n");
                sb.AppendFormat("      \"type\": \"{0}\",\n", EscapeJsonString(a.Type));
                sb.AppendFormat("      \"elementId\": \"{0}\",\n", EscapeJsonString(a.ElementId ?? string.Empty));
                sb.AppendFormat("      \"tagId\": \"{0}\",\n", EscapeJsonString(a.TagId ?? string.Empty));
                sb.AppendFormat("      \"text\": \"{0}\",\n", EscapeJsonString(a.Text ?? string.Empty));
                sb.Append("      \"bbox\": {\n");
                sb.AppendFormat("        \"min\": {{ \"x\": {0}, \"y\": {1}, \"z\": {2} }},\n", a.Min.X.ToString(System.Globalization.CultureInfo.InvariantCulture), a.Min.Y.ToString(System.Globalization.CultureInfo.InvariantCulture), a.Min.Z.ToString(System.Globalization.CultureInfo.InvariantCulture));
                sb.AppendFormat("        \"max\": {{ \"x\": {0}, \"y\": {1}, \"z\": {2} }}\n", a.Max.X.ToString(System.Globalization.CultureInfo.InvariantCulture), a.Max.Y.ToString(System.Globalization.CultureInfo.InvariantCulture), a.Max.Z.ToString(System.Globalization.CultureInfo.InvariantCulture));
                sb.Append("      }\n");
                // Also include pixel-space bbox by projecting to view plane using Right/Up and scaling by crop extents
                if (crop != null && imgW > 0 && imgH > 0)
                {
                    XYZ origin = view.Origin;
                    XYZ right = view.RightDirection;
                    XYZ up = view.UpDirection;

                    Func<XYZ, (double u, double v)> proj = (pt) =>
                    {
                        XYZ d = pt - origin;
                        double u = d.DotProduct(right);
                        double v = d.DotProduct(up);
                        return (u, v);
                    };

                    // Crop extents in (u,v)
                    List<XYZ> cropCorners = new List<XYZ>();
                    foreach (double cx in new[] { crop.Min.X, crop.Max.X })
                    foreach (double cy in new[] { crop.Min.Y, crop.Max.Y })
                    foreach (double cz in new[] { crop.Min.Z, crop.Max.Z })
                        cropCorners.Add(new XYZ(cx, cy, cz));

                    double cuMin = double.PositiveInfinity, cvMin = double.PositiveInfinity;
                    double cuMax = double.NegativeInfinity, cvMax = double.NegativeInfinity;
                    foreach (var cpt in cropCorners)
                    {
                        var (u, v) = proj(cpt);
                        if (u < cuMin) cuMin = u; if (u > cuMax) cuMax = u;
                        if (v < cvMin) cvMin = v; if (v > cvMax) cvMax = v;
                    }
                    double du = Math.Max(1e-9, cuMax - cuMin);
                    double dv = Math.Max(1e-9, cvMax - cvMin);

                    // Tag bbox corners in (u,v)
                    List<XYZ> tagCorners = new List<XYZ>();
                    foreach (double tx in new[] { a.Min.X, a.Max.X })
                    foreach (double ty in new[] { a.Min.Y, a.Max.Y })
                    foreach (double tz in new[] { a.Min.Z, a.Max.Z })
                        tagCorners.Add(new XYZ(tx, ty, tz));

                    double tuMin = double.PositiveInfinity, tvMin = double.PositiveInfinity;
                    double tuMax = double.NegativeInfinity, tvMax = double.NegativeInfinity;
                    foreach (var tpt in tagCorners)
                    {
                        var (u, v) = proj(tpt);
                        if (u < tuMin) tuMin = u; if (u > tuMax) tuMax = u;
                        if (v < tvMin) tvMin = v; if (v > tvMax) tvMax = v;
                    }

                    int px1 = (int)Math.Round(((tuMin - cuMin) / du) * imgW);
                    int px2 = (int)Math.Round(((tuMax - cuMin) / du) * imgW);
                    int py1 = imgH - (int)Math.Round(((tvMin - cvMin) / dv) * imgH);
                    int py2 = imgH - (int)Math.Round(((tvMax - cvMin) / dv) * imgH);

                    sb.Append(",\n");
                    sb.Append("      \"pixelBBox\": {\n");
                    sb.AppendFormat("        \"min\": {{ \"x\": {0}, \"y\": {1} }},\n", Math.Min(px1, px2), Math.Min(py1, py2));
                    sb.AppendFormat("        \"max\": {{ \"x\": {0}, \"y\": {1} }}\n", Math.Max(px1, px2), Math.Max(py1, py2));
                    sb.Append("      }\n");
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
    }
}
