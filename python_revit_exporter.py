#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Python Revit View Exporter
This script can be run in pyRevit or through RevitPythonShell
"""

import os
import sys
import clr

# Add references to Revit API
clr.AddReference("RevitAPI")
clr.AddReference("RevitAPIUI")
clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Drawing")

from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *
import System.Windows.Forms as WinForms
import System.Drawing as Drawing

# Get the current Revit application and document
try:
    # For use in pyRevit
    from pyrevit import revit
    doc = revit.doc
    uidoc = revit.uidoc
    app = revit.app
except:
    # For use in RevitPythonShell
    try:
        doc = __revit__.ActiveUIDocument.Document
        uidoc = __revit__.ActiveUIDocument
        app = __revit__
    except:
        print("Error: This script must be run from within Revit using pyRevit or RevitPythonShell")
        sys.exit(1)

class ViewSelectorForm(WinForms.Form):
    """Form for selecting views to export"""
    
    def __init__(self, views):
        self.views = views
        self.selected_views = []
        self.InitializeComponent()
        self.PopulateViews()
    
    def InitializeComponent(self):
        """Initialize the form components"""
        self.Text = "Revit View Exporter"
        self.Width = 600
        self.Height = 500
        self.StartPosition = WinForms.FormStartPosition.CenterScreen
        
        # Create label
        self.label = WinForms.Label()
        self.label.Text = "Select views to export as images:"
        self.label.Location = Drawing.Point(10, 10)
        self.label.Width = 300
        self.Controls.Add(self.label)
        
        # Create filter controls
        self.filterLabel = WinForms.Label()
        self.filterLabel.Text = "Filter by name:"
        self.filterLabel.Location = Drawing.Point(10, 40)
        self.filterLabel.Width = 100
        self.Controls.Add(self.filterLabel)
        
        self.filterTextBox = WinForms.TextBox()
        self.filterTextBox.Location = Drawing.Point(110, 37)
        self.filterTextBox.Width = 200
        self.filterTextBox.TextChanged += self.FilterTextChanged
        self.Controls.Add(self.filterTextBox)
        
        # Create view type filter
        self.typeLabel = WinForms.Label()
        self.typeLabel.Text = "View type:"
        self.typeLabel.Location = Drawing.Point(320, 40)
        self.typeLabel.Width = 70
        self.Controls.Add(self.typeLabel)
        
        self.typeComboBox = WinForms.ComboBox()
        self.typeComboBox.Location = Drawing.Point(390, 37)
        self.typeComboBox.Width = 180
        self.typeComboBox.DropDownStyle = WinForms.ComboBoxStyle.DropDownList
        self.typeComboBox.SelectedIndexChanged += self.TypeFilterChanged
        self.Controls.Add(self.typeComboBox)
        
        # Create listview for views
        self.listView = WinForms.ListView()
        self.listView.Location = Drawing.Point(10, 70)
        self.listView.Width = 560
        self.listView.Height = 330
        self.listView.View = WinForms.View.Details
        self.listView.FullRowSelect = True
        self.listView.CheckBoxes = True
        self.listView.Columns.Add("Name", 250)
        self.listView.Columns.Add("Type", 150)
        self.listView.Columns.Add("ID", 100)
        self.Controls.Add(self.listView)
        
        # Select all checkbox
        self.selectAllCheckBox = WinForms.CheckBox()
        self.selectAllCheckBox.Text = "Select All"
        self.selectAllCheckBox.Location = Drawing.Point(10, 410)
        self.selectAllCheckBox.Width = 100
        self.selectAllCheckBox.CheckedChanged += self.SelectAllChanged
        self.Controls.Add(self.selectAllCheckBox)
        
        # Create buttons
        self.exportButton = WinForms.Button()
        self.exportButton.Text = "Export"
        self.exportButton.Location = Drawing.Point(400, 410)
        self.exportButton.Width = 80
        self.exportButton.Click += self.ExportButtonClick
        self.Controls.Add(self.exportButton)
        
        self.cancelButton = WinForms.Button()
        self.cancelButton.Text = "Cancel"
        self.cancelButton.Location = Drawing.Point(490, 410)
        self.cancelButton.Width = 80
        self.cancelButton.Click += self.CancelButtonClick
        self.Controls.Add(self.cancelButton)
    
    def PopulateViews(self):
        """Populate the listview with views"""
        # Get unique view types
        view_types = set()
        view_types.add("All Types")
        
        for view in self.views:
            view_types.add(str(view.ViewType))
        
        # Add view types to combo box
        for view_type in sorted(view_types):
            self.typeComboBox.Items.Add(view_type)
        
        self.typeComboBox.SelectedIndex = 0
        
        # Add views to listview
        self.PopulateListView()
    
    def PopulateListView(self):
        """Populate the listview based on current filters"""
        self.listView.Items.Clear()
        
        filter_text = self.filterTextBox.Text.lower()
        selected_type = self.typeComboBox.SelectedItem
        
        for view in self.views:
            # Apply filters
            if filter_text and filter_text not in view.Name.lower():
                continue
                
            if selected_type != "All Types" and str(view.ViewType) != selected_type:
                continue
            
            # Create list item
            item = WinForms.ListViewItem(view.Name)
            item.SubItems.Add(str(view.ViewType))
            item.SubItems.Add(str(view.Id.IntegerValue))
            item.Tag = view
            
            self.listView.Items.Add(item)
    
    def FilterTextChanged(self, sender, event):
        """Handle filter text changed event"""
        self.PopulateListView()
    
    def TypeFilterChanged(self, sender, event):
        """Handle type filter changed event"""
        self.PopulateListView()
    
    def SelectAllChanged(self, sender, event):
        """Handle select all checkbox changed event"""
        checked = self.selectAllCheckBox.Checked
        for i in range(self.listView.Items.Count):
            self.listView.Items[i].Checked = checked
    
    def ExportButtonClick(self, sender, event):
        """Handle export button click event"""
        # Get selected views
        self.selected_views = []
        for i in range(self.listView.Items.Count):
            if self.listView.Items[i].Checked:
                self.selected_views.append(self.listView.Items[i].Tag)
        
        if not self.selected_views:
            WinForms.MessageBox.Show("No views selected for export.", "Warning", 
                                    WinForms.MessageBoxButtons.OK, 
                                    WinForms.MessageBoxIcon.Warning)
            return
        
        # Select export folder
        folderDialog = WinForms.FolderBrowserDialog()
        folderDialog.Description = "Select folder for exported images"
        
        if folderDialog.ShowDialog() == WinForms.DialogResult.OK:
            self.export_folder = folderDialog.SelectedPath
            self.DialogResult = WinForms.DialogResult.OK
            self.Close()
        
    def CancelButtonClick(self, sender, event):
        """Handle cancel button click event"""
        self.DialogResult = WinForms.DialogResult.Cancel
        self.Close()

def get_exportable_views(doc):
    """Get all exportable views from the document"""
    collector = FilteredElementCollector(doc)
    collector.OfClass(typeof(View))
    
    exportable_views = []
    
    for view in collector:
        # Skip view templates, system views, and non-exportable views
        if (view.IsTemplate or 
            view.ViewType == ViewType.SystemBrowser or 
            view.ViewType == ViewType.ProjectBrowser or 
            view.ViewType == ViewType.Internal or
            view.ViewType == ViewType.Undefined or 
            not view.CanBePrinted):
            continue
        
        # Skip views with <3D> in the name (typically section boxes)
        if "<3D>" in view.Name:
            continue
        
        exportable_views.append(view)
    
    # Sort views by name
    return sorted(exportable_views, key=lambda v: v.Name)

def export_views_to_images(doc, views, export_folder):
    """Export views to images"""
    # Create export options
    options = ImageExportOptions()
    options.ZoomType = ZoomFitType.FitToPage
    options.PixelSize = 2000  # Image width in pixels
    options.ImageResolution = ImageResolution.DPI_300
    options.ExportRange = ExportRange.SetOfViews
    options.HLRandWFViewsFileType = ImageFileType.PNG
    options.ShadowViewsFileType = ImageFileType.PNG
    
    # Create transaction for exporting
    with Transaction(doc, "Export Views to Images") as t:
        t.Start()
        
        # Export each view
        for view in views:
            try:
                # Set the view to export
                view_set = List[ElementId]()
                view_set.Add(view.Id)
                options.SetViewsAndSheets(view_set)
                
                # Set the file name (sanitize view name)
                file_name = view.Name
                for c in ['<', '>', ':', '"', '/', '\\', '|', '?', '*']:
                    file_name = file_name.replace(c, '_')
                
                if not file_name.lower().endswith('.png'):
                    file_name += '.png'
                
                file_path = os.path.join(export_folder, file_name)
                
                # Export the view
                options.FilePath = file_path
                doc.ExportImage(options)
                
                print(f"Exported: {file_name}")
            except Exception as ex:
                print(f"Error exporting view '{view.Name}': {ex}")
        
        t.Commit()

def main():
    """Main function"""
    try:
        # Get exportable views
        views = get_exportable_views(doc)
        
        if not views:
            print("No exportable views found in the document.")
            return
        
        # Show view selector form
        form = ViewSelectorForm(views)
        result = form.ShowDialog()
        
        if result == WinForms.DialogResult.OK:
            selected_views = form.selected_views
            export_folder = form.export_folder
            
            # Export views
            export_views_to_images(doc, selected_views, export_folder)
            
            # Show success message
            WinForms.MessageBox.Show(
                f"Successfully exported {len(selected_views)} view(s) to:\n{export_folder}", 
                "Success", 
                WinForms.MessageBoxButtons.OK, 
                WinForms.MessageBoxIcon.Information
            )
    
    except Exception as ex:
        print(f"Error: {ex}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    main()
