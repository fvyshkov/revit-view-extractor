using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Windows.Forms;
using Autodesk.Revit.Attributes;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitViewExporter
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

                // Show the view selector dialog
                using (ViewSelectorForm form = new ViewSelectorForm(views))
                {
                    if (form.ShowDialog() == DialogResult.OK)
                    {
                        // Get selected views
                        List<View> selectedViews = form.SelectedViews;
                        
                        if (selectedViews.Count == 0)
                        {
                            TaskDialog.Show("Warning", "No views selected for export.");
                            return Result.Succeeded;
                        }

                        // Ask for export folder
                        FolderBrowserDialog folderDialog = new FolderBrowserDialog();
                        folderDialog.Description = "Select folder for exported images";
                        
                        if (folderDialog.ShowDialog() == DialogResult.OK)
                        {
                            string exportFolder = folderDialog.SelectedPath;
                            
                            // Export selected views
                            ExportViewsToImages(doc, selectedViews, exportFolder);
                            
                            // Show success message
                            TaskDialog.Show("Success", $"Successfully exported {selectedViews.Count} view(s) to:\n{exportFolder}");
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

        private void ExportViewsToImages(Document doc, List<View> views, string exportFolder)
        {
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
                
                // Export each view
                foreach (View view in views)
                {
                    try
                    {
                        // Set the view to export
                        options.SetViewsAndSheets(new List<ElementId> { view.Id });
                        
                        // Set the file name (sanitize view name)
                        string fileName = SanitizeFileName(view.Name);
                        string filePath = Path.Combine(exportFolder, fileName);
                        
                        // Export the view
                        options.FilePath = filePath;
                        doc.ExportImage(options);
                    }
                    catch (Exception ex)
                    {
                        TaskDialog.Show("Export Error", $"Error exporting view '{view.Name}': {ex.Message}");
                    }
                }
                
                t.Commit();
            }
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
