using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Autodesk.Revit.ApplicationServices;
using Autodesk.Revit.Attributes;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitViewExtractor
{
    [Transaction(TransactionMode.Manual)]
    [Regeneration(RegenerationOption.Manual)]
    public class ViewExtractorApp : IExternalCommand
    {
        public Result Execute(ExternalCommandData commandData, ref string message, ElementSet elements)
        {
            try
            {
                UIApplication uiApp = commandData.Application;
                UIDocument uiDoc = uiApp.ActiveUIDocument;
                Document doc = uiDoc.Document;

                // Extract first view from the document
                ExtractFirstView(doc);

                return Result.Succeeded;
            }
            catch (Exception ex)
            {
                message = $"Error: {ex.Message}";
                return Result.Failed;
            }
        }

        private void ExtractFirstView(Document doc)
        {
            if (doc == null) return;

            try
            {
                // Get all available views
                List<View> allViews = GetAllExportableViews(doc);
                
                if (allViews.Count == 0)
                {
                    TaskDialog.Show("Warning", "No exportable views found in the document");
                    return;
                }

                // Show dialog to select view
                View selectedView = ShowViewSelectionDialog(allViews);
                
                if (selectedView != null)
                {
                    ExportViewAsImage(doc, selectedView);
                    TaskDialog.Show("Success", $"Successfully exported view: {selectedView.Name}");
                }
            }
            catch (Exception ex)
            {
                TaskDialog.Show("Error", $"Error extracting view: {ex.Message}");
                throw;
            }
        }

        private View ShowViewSelectionDialog(List<View> views)
        {
            // Create a simple selection dialog
            string viewList = "Available views:\n\n";
            for (int i = 0; i < views.Count; i++)
            {
                viewList += $"{i + 1}. {views[i].Name} ({views[i].ViewType})\n";
            }
            
            TaskDialog dialog = new TaskDialog("Select View to Export");
            dialog.MainInstruction = "Choose a view to export:";
            dialog.MainContent = viewList;
            dialog.CommonButtons = TaskDialogCommonButtons.Cancel;
            
            // Add buttons for each view (limit to first 10 for UI reasons)
            int maxButtons = Math.Min(views.Count, 10);
            for (int i = 0; i < maxButtons; i++)
            {
                dialog.AddCommandLink((TaskDialogCommandLinkId)(100 + i), 
                    $"{views[i].Name}", 
                    $"Export {views[i].ViewType}: {views[i].Name}");
            }
            
            TaskDialogResult result = dialog.Show();
            
            // Handle selection
            if (result >= (TaskDialogResult)100 && result < (TaskDialogResult)(100 + maxButtons))
            {
                int selectedIndex = (int)result - 100;
                return views[selectedIndex];
            }
            
            return null; // User cancelled
        }

        private List<View> GetAllExportableViews(Document doc)
        {
            List<View> exportableViews = new List<View>();
            
            // Get all views in the document
            FilteredElementCollector collector = new FilteredElementCollector(doc);
            ICollection<Element> allViews = collector.OfClass(typeof(View)).ToElements();
            
            foreach (View view in allViews.Cast<View>())
            {
                // Skip templates and non-printable views
                if (view.IsTemplate || !view.CanBePrinted)
                    continue;
                    
                // Skip system views like {3D}, Browser Organization, etc.
                if (view.Name.StartsWith("{") || view.Name.Contains("Browser"))
                    continue;
                    
                exportableViews.Add(view);
            }
            
            // Sort views by type and name for better organization
            exportableViews.Sort((v1, v2) => 
            {
                int typeCompare = v1.ViewType.ToString().CompareTo(v2.ViewType.ToString());
                return typeCompare != 0 ? typeCompare : v1.Name.CompareTo(v2.Name);
            });
            
            return exportableViews;
        }

        private void ExportViewAsImage(Document doc, View view)
        {
            string outputPath = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.Desktop), "extracted_view.png");
            
            ImageExportOptions imageOptions = new ImageExportOptions
            {
                ZoomType = ZoomFitType.FitToPage,
                PixelSize = 1024,
                ImageResolution = ImageResolution.DPI_150,
                FitDirection = FitDirectionType.Horizontal,
                ExportRange = ExportRange.SetOfViews,
                FilePath = outputPath.Replace(".png", ""), // Revit adds extension automatically
                HLRandWFViewsFileType = ImageFileType.PNG
            };

            imageOptions.SetViewsAndSheets(new List<ElementId> { view.Id });

            using (Transaction trans = new Transaction(doc, "Export View"))
            {
                trans.Start();
                doc.ExportImage(imageOptions);
                trans.Commit();
            }

            TaskDialog.Show("Export Complete", $"View exported to: {outputPath}");
        }
    }

    // Command to list all views
    [Transaction(TransactionMode.ReadOnly)]
    [Regeneration(RegenerationOption.Manual)]
    public class ListViewsCommand : IExternalCommand
    {
        public Result Execute(ExternalCommandData commandData, ref string message, ElementSet elements)
        {
            try
            {
                UIApplication uiApp = commandData.Application;
                UIDocument uiDoc = uiApp.ActiveUIDocument;
                Document doc = uiDoc.Document;

                List<View> allViews = GetAllViews(doc);
                ShowViewsList(allViews);

                return Result.Succeeded;
            }
            catch (Exception ex)
            {
                message = $"Error: {ex.Message}";
                return Result.Failed;
            }
        }

        private List<View> GetAllViews(Document doc)
        {
            List<View> allViews = new List<View>();
            
            FilteredElementCollector collector = new FilteredElementCollector(doc);
            ICollection<Element> views = collector.OfClass(typeof(View)).ToElements();
            
            foreach (View view in views.Cast<View>())
            {
                allViews.Add(view);
            }
            
            // Sort by type and name
            allViews.Sort((v1, v2) => 
            {
                int typeCompare = v1.ViewType.ToString().CompareTo(v2.ViewType.ToString());
                return typeCompare != 0 ? typeCompare : v1.Name.CompareTo(v2.Name);
            });
            
            return allViews;
        }

        private void ShowViewsList(List<View> views)
        {
            string viewsList = "ALL VIEWS IN DOCUMENT:\n\n";
            string currentType = "";
            
            foreach (View view in views)
            {
                if (view.ViewType.ToString() != currentType)
                {
                    currentType = view.ViewType.ToString();
                    viewsList += $"\n=== {currentType} ===\n";
                }
                
                string status = "";
                if (view.IsTemplate) status += " [TEMPLATE]";
                if (!view.CanBePrinted) status += " [NOT PRINTABLE]";
                
                viewsList += $"• {view.Name}{status}\n";
            }
            
            viewsList += $"\nTotal views: {views.Count}";
            
            TaskDialog dialog = new TaskDialog("All Views in Document");
            dialog.MainInstruction = "Complete list of views:";
            dialog.MainContent = viewsList;
            dialog.Show();
        }
    }

    // Design Automation version for cloud processing
    [Transaction(TransactionMode.Manual)]
    [Regeneration(RegenerationOption.Manual)]
    public class ViewExtractorCloud : IExternalDBApplication
    {
        public ExternalDBApplicationResult OnStartup(ControlledApplication app)
        {
            // Subscribe to document opening event for Design Automation
            app.DocumentOpened += OnDocumentOpened;
            return ExternalDBApplicationResult.Succeeded;
        }

        public ExternalDBApplicationResult OnShutdown(ControlledApplication app)
        {
            return ExternalDBApplicationResult.Succeeded;
        }

        private void OnDocumentOpened(object sender, Autodesk.Revit.DB.Events.DocumentOpenedEventArgs e)
        {
            try
            {
                Document doc = e.Document;
                Console.WriteLine($"Document opened: {doc.Title}");
                
                // Process the document
                ProcessDocument(doc);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"ERROR in OnDocumentOpened: {ex.Message}");
                throw;
            }
        }

        private void ProcessDocument(Document doc)
        {
            try
            {
                // Get output folder from environment or use current directory
                string outputFolder = Environment.GetEnvironmentVariable("OUTPUT_FOLDER") ?? Directory.GetCurrentDirectory();
                Console.WriteLine($"Output folder: {outputFolder}");

                // Ensure output directory exists
                Directory.CreateDirectory(outputFolder);

                // Create simple result file
                string resultFile = Path.Combine(outputFolder, "result.txt");
                
                // Get basic document info
                string documentInfo = GetDocumentInfo(doc);
                
                // Write to file
                File.WriteAllText(resultFile, documentInfo);
                
                Console.WriteLine($"Result file created: {resultFile}");
                Console.WriteLine("Processing completed successfully");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"ERROR in ProcessDocument: {ex.Message}");
                throw;
            }
        }

        private string GetDocumentInfo(Document doc)
        {
            try
            {
                // Get all views
                List<View> allViews = GetAllViewsForCloud(doc);
                
                // Count different types of views
                int totalViews = allViews.Count;
                int exportableViews = allViews.Count(v => !v.IsTemplate && v.CanBePrinted && 
                    !v.Name.StartsWith("{") && !v.Name.Contains("Browser"));
                
                // Get first few view names
                var viewNames = allViews
                    .Where(v => !v.IsTemplate && v.CanBePrinted)
                    .Take(5)
                    .Select(v => $"{v.Name} ({v.ViewType})")
                    .ToList();

                // Create result string
                string result = $"Document: {doc.Title}\n";
                result += $"Total views: {totalViews}\n";
                result += $"Exportable views: {exportableViews}\n";
                result += $"Processing time: {DateTime.Now:yyyy-MM-dd HH:mm:ss}\n";
                result += "\nFirst 5 exportable views:\n";
                
                foreach (string viewName in viewNames)
                {
                    result += $"- {viewName}\n";
                }

                return result;
            }
            catch (Exception ex)
            {
                return $"ERROR getting document info: {ex.Message}";
            }
        }

        private void ExportFirstExportableView(Document doc, List<View> allViews, string outputFolder)
        {
            View firstView = allViews.FirstOrDefault(v => !v.IsTemplate && v.CanBePrinted && 
                !v.Name.StartsWith("{") && !v.Name.Contains("Browser"));
                
            if (firstView != null)
            {
                ExportViewToCloud(doc, firstView, outputFolder);
                Console.WriteLine($"Exported first exportable view: {firstView.Name}");
            }
            else
            {
                Console.WriteLine("No exportable views found");
            }
        }

        private static List<View> GetAllViewsForCloud(Document doc)
        {
            List<View> allViews = new List<View>();
            
            FilteredElementCollector collector = new FilteredElementCollector(doc);
            ICollection<Element> views = collector.OfClass(typeof(View)).ToElements();
            
            foreach (View view in views.Cast<View>())
            {
                allViews.Add(view);
            }
            
            return allViews;
        }

        private static void ExportAllViews(Document doc, List<View> allViews, string outputFolder)
        {
            int exportedCount = 0;
            
            foreach (View view in allViews)
            {
                if (view.IsTemplate || !view.CanBePrinted)
                    continue;
                    
                if (view.Name.StartsWith("{") || view.Name.Contains("Browser"))
                    continue;

                try
                {
                    ExportViewToCloud(doc, view, outputFolder);
                    exportedCount++;
                    Console.WriteLine($"Exported: {view.Name} ({view.ViewType})");
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"Failed to export {view.Name}: {ex.Message}");
                }
            }
            
            Console.WriteLine($"Total exported views: {exportedCount}");
        }

        private static void ExportViewByName(Document doc, List<View> allViews, string viewName, string outputFolder)
        {
            View targetView = allViews.FirstOrDefault(v => v.Name.Equals(viewName, StringComparison.OrdinalIgnoreCase));
            
            if (targetView == null)
            {
                Console.WriteLine($"ERROR: View '{viewName}' not found");
                Console.WriteLine("Available views:");
                foreach (var view in allViews.Where(v => !v.IsTemplate && v.CanBePrinted))
                {
                    Console.WriteLine($"  - {view.Name} ({view.ViewType})");
                }
                return;
            }

            try
            {
                ExportViewToCloud(doc, targetView, outputFolder);
                Console.WriteLine($"Successfully exported view: {targetView.Name}");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Failed to export view '{viewName}': {ex.Message}");
                throw;
            }
        }

        private static void ExportViewToCloud(Document doc, View view, string outputFolder)
        {
            string fileName = $"{view.Name}_{view.ViewType}".Replace(" ", "_").Replace("/", "_").Replace("\\", "_");
            string outputPath = Path.Combine(outputFolder, fileName);
            
            ImageExportOptions imageOptions = new ImageExportOptions
            {
                ZoomType = ZoomFitType.FitToPage,
                PixelSize = 1024,
                ImageResolution = ImageResolution.DPI_150,
                FitDirection = FitDirectionType.Horizontal,
                ExportRange = ExportRange.SetOfViews,
                FilePath = outputPath,
                HLRandWFViewsFileType = ImageFileType.PNG
            };

            imageOptions.SetViewsAndSheets(new List<ElementId> { view.Id });

            using (Transaction trans = new Transaction(doc, "Export View"))
            {
                trans.Start();
                doc.ExportImage(imageOptions);
                trans.Commit();
            }
        }
    }
}
