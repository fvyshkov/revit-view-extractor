using System;
using System.IO;
using System.Reflection;
using System.Windows.Media.Imaging;
using Autodesk.Revit.UI;

namespace RevitViewExporter
{
    public class App : IExternalApplication
    {
        public Result OnStartup(UIControlledApplication application)
        {
            // Create a ribbon tab
            string tabName = "View Exporter";
            application.CreateRibbonTab(tabName);

            // Create a ribbon panel
            RibbonPanel ribbonPanel = application.CreateRibbonPanel(tabName, "Export Tools");

            // Get assembly path
            string assemblyPath = Assembly.GetExecutingAssembly().Location;

            // Create push button data
            PushButtonData buttonData = new PushButtonData(
                "ExportViews",
                "Export\nViews",
                assemblyPath,
                "RevitViewExporter.Commands.ExportViewsCommand")
            {
                ToolTip = "Export views as images",
                LongDescription = "Select and export Revit views as high-quality PNG images.",
                Image = GetEmbeddedImage("RevitViewExporter.Images.ExportViews_16.png"),
                LargeImage = GetEmbeddedImage("RevitViewExporter.Images.ExportViews_32.png")
            };

            // Add button to panel
            ribbonPanel.AddItem(buttonData);

            return Result.Succeeded;
        }

        public Result OnShutdown(UIControlledApplication application)
        {
            return Result.Succeeded;
        }

        private BitmapSource GetEmbeddedImage(string resourceName)
        {
            try
            {
                // Get current assembly
                Assembly assembly = Assembly.GetExecutingAssembly();

                // Load image from embedded resource
                using (Stream stream = assembly.GetManifestResourceStream(resourceName))
                {
                    if (stream != null)
                    {
                        // Create bitmap image
                        BitmapImage image = new BitmapImage();
                        image.BeginInit();
                        image.StreamSource = stream;
                        image.CacheOption = BitmapCacheOption.OnLoad;
                        image.EndInit();
                        image.Freeze();
                        return image;
                    }
                }
            }
            catch (Exception ex)
            {
                // Log error
                string message = $"Error loading image resource: {ex.Message}";
                System.Diagnostics.Debug.WriteLine(message);
            }

            return null;
        }
    }
}
