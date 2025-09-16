using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Autodesk.Revit.DB;
using Autodesk.Revit.ApplicationServices;
using Autodesk.Revit.UI;

namespace RevitViewExporter
{
    public class HeadlessApp : Autodesk.Revit.DB.IExternalDBApplication
    {
        public Autodesk.Revit.DB.ExternalDBApplicationResult OnStartup(ControlledApplication application)
        {
            try
            {
                string rvtPath = Environment.GetEnvironmentVariable("RVE_RVT");
                string viewName = Environment.GetEnvironmentVariable("RVE_VIEW");
                string outDir = Environment.GetEnvironmentVariable("RVE_OUT");

                if (string.IsNullOrWhiteSpace(rvtPath) || string.IsNullOrWhiteSpace(viewName) || string.IsNullOrWhiteSpace(outDir))
                {
                    return ExternalDBApplicationResult.Succeeded;
                }

                if (!Directory.Exists(outDir)) Directory.CreateDirectory(outDir);

                // Subscribe to document opened to perform work
                application.DocumentOpened += (sender, args) =>
                {
                    try
                    {
                        ExecuteHeadless(args.Document, viewName, outDir);
                    }
                    catch (Exception ex)
                    {
                        // Best-effort logging
                        try { File.WriteAllText(Path.Combine(outDir, "headless_error.txt"), ex.ToString()); } catch { }
                    }
                };
            }
            catch { }

            return Autodesk.Revit.DB.ExternalDBApplicationResult.Succeeded;
        }

        public Autodesk.Revit.DB.ExternalDBApplicationResult OnShutdown(ControlledApplication application)
        {
            return Autodesk.Revit.DB.ExternalDBApplicationResult.Succeeded;
        }

        private void ExecuteHeadless(Document doc, string viewName, string exportFolder)
        {
            // Find view by name
            View target = new FilteredElementCollector(doc)
                .OfClass(typeof(View))
                .Cast<View>()
                .FirstOrDefault(v => !v.IsTemplate && v.Name.Equals(viewName, StringComparison.OrdinalIgnoreCase));

            if (target == null)
            {
                File.WriteAllText(Path.Combine(exportFolder, "headless_log.txt"), $"View not found: {viewName}");
                return;
            }

            // Reuse existing ExportViewsCommand logic by calling private methods is not possible.
            // Implement minimal export here.
            ImageExportOptions options = new ImageExportOptions
            {
                ZoomType = ZoomFitType.FitToPage,
                PixelSize = 2000,
                ImageResolution = ImageResolution.DPI_300,
                ExportRange = ExportRange.SetOfViews,
                HLRandWFViewsFileType = ImageFileType.PNG,
                ShadowViewsFileType = ImageFileType.PNG
            };

            using (Transaction tx = new Transaction(doc, "Headless Export"))
            {
                tx.Start();
                options.SetViewsAndSheets(new List<ElementId> { target.Id });
                string fileName = SanitizeFileName(target.Name);
                string filePath = Path.Combine(exportFolder, fileName);
                options.FilePath = filePath;
                doc.ExportImage(options);
                tx.Commit();
            }

            // Write basic JSON without pixel mapping (the interactive path has full JSON)
            var jsonPath = Path.Combine(exportFolder, Path.GetFileNameWithoutExtension(SanitizeFileName(target.Name)) + ".annotations.json");
            var anns = CollectAnnotations(doc, target);
            WriteSimpleJson(jsonPath, target, anns);
        }

        private List<IndependentTag> CollectAnnotations(Document doc, View view)
        {
            return new FilteredElementCollector(doc, view.Id)
                .WhereElementIsNotElementType()
                .OfClass(typeof(IndependentTag))
                .Cast<IndependentTag>()
                .ToList();
        }

        private void WriteSimpleJson(string path, View view, List<IndependentTag> tags)
        {
            using (var sw = new StreamWriter(path))
            {
                sw.WriteLine("{");
                sw.WriteLine($"  \"viewId\": \"{view.Id}\",");
                sw.WriteLine($"  \"viewName\": \"{Escape(view.Name)}\",");
                sw.WriteLine("  \"annotations\": [");
                for (int i = 0; i < tags.Count; i++)
                {
                    var t = tags[i];
                    var bb = t.get_BoundingBox(view);
                    sw.WriteLine("    {");
                    sw.WriteLine($"      \"tagId\": \"{t.Id}\",");
                    sw.WriteLine($"      \"text\": \"{Escape(Safe(() => t.TagText))}\",");
                    if (bb != null)
                    {
                        sw.WriteLine("      \"bbox\": {");
                        sw.WriteLine($"        \"min\": {{ \"x\": {bb.Min.X}, \"y\": {bb.Min.Y}, \"z\": {bb.Min.Z} }},");
                        sw.WriteLine($"        \"max\": {{ \"x\": {bb.Max.X}, \"y\": {bb.Max.Y}, \"z\": {bb.Max.Z} }}");
                        sw.WriteLine("      }");
                    }
                    sw.Write("    }");
                    if (i < tags.Count - 1) sw.Write(",");
                    sw.WriteLine();
                }
                sw.WriteLine("  ]");
                sw.WriteLine("}");
            }
        }

        private static string Escape(string s) => string.IsNullOrEmpty(s) ? string.Empty : s.Replace("\\", "\\\\").Replace("\"", "\\\"");
        private static T Safe<T>(Func<T> f) { try { return f(); } catch { return default(T); } }
        private static string SanitizeFileName(string fileName)
        {
            foreach (char c in Path.GetInvalidFileNameChars()) fileName = fileName.Replace(c, '_');
            if (!fileName.EndsWith(".png", StringComparison.OrdinalIgnoreCase)) fileName += ".png";
            return fileName;
        }
    }
}
