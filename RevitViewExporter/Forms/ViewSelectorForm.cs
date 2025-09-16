using System;
using System.Collections.Generic;
using System.Drawing;
using System.Linq;
using System.Windows.Forms;
using Autodesk.Revit.DB;
using View = Autodesk.Revit.DB.View;

namespace RevitViewExporter.Forms
{
    public partial class ViewSelectorForm : System.Windows.Forms.Form
    {
        private List<View> _allViews;
        private List<View> _selectedViews = new List<View>();
        
        public List<View> SelectedViews => _selectedViews;

        public ViewSelectorForm(List<View> views)
        {
            InitializeComponent();
            
            _allViews = views;
            
            // Populate view type filter
            PopulateViewTypes();
            
            // Populate views list
            FilterAndPopulateViews();
        }

        private void PopulateViewTypes()
        {
            // Get unique view types
            var viewTypes = _allViews
                .Select(v => v.ViewType.ToString())
                .Distinct()
                .OrderBy(t => t)
                .ToList();
            
            // Add "All Types" option
            viewTypes.Insert(0, "All Types");
            
            // Populate combo box
            cboViewType.DataSource = viewTypes;
            cboViewType.SelectedIndex = 0;
        }

        private void FilterAndPopulateViews()
        {
            // Clear list
            lstViews.Items.Clear();
            
            // Get filter values
            string nameFilter = txtFilter.Text.ToLower();
            string typeFilter = cboViewType.SelectedItem.ToString();
            
            // Filter views
            var filteredViews = _allViews.Where(v => 
                (string.IsNullOrEmpty(nameFilter) || v.Name.ToLower().Contains(nameFilter)) &&
                (typeFilter == "All Types" || v.ViewType.ToString() == typeFilter)
            );
            
            // Add views to list
            foreach (var view in filteredViews)
            {
                ListViewItem item = new ListViewItem(view.Name);
                item.SubItems.Add(view.ViewType.ToString());
                item.SubItems.Add(view.Id.ToString());
                item.Tag = view;
                
                lstViews.Items.Add(item);
            }
            
            // Update count label
            lblCount.Text = $"Showing {lstViews.Items.Count} of {_allViews.Count} views";
        }

        private void txtFilter_TextChanged(object sender, EventArgs e)
        {
            FilterAndPopulateViews();
        }

        private void cboViewType_SelectedIndexChanged(object sender, EventArgs e)
        {
            FilterAndPopulateViews();
        }

        private void chkSelectAll_CheckedChanged(object sender, EventArgs e)
        {
            // Select or deselect all items
            foreach (ListViewItem item in lstViews.Items)
            {
                item.Checked = chkSelectAll.Checked;
            }
        }

        private void btnExport_Click(object sender, EventArgs e)
        {
            // Get selected views
            _selectedViews.Clear();
            
            foreach (ListViewItem item in lstViews.Items)
            {
                if (item.Checked)
                {
                    _selectedViews.Add((View)item.Tag);
                }
            }
            
            // Check if any views are selected
            if (_selectedViews.Count == 0)
            {
                System.Windows.Forms.MessageBox.Show("Please select at least one view to export.", "No Views Selected", 
                    System.Windows.Forms.MessageBoxButtons.OK, System.Windows.Forms.MessageBoxIcon.Warning);
                return;
            }
            
            DialogResult = System.Windows.Forms.DialogResult.OK;
            Close();
        }

        private void btnCancel_Click(object sender, EventArgs e)
        {
            DialogResult = System.Windows.Forms.DialogResult.Cancel;
            Close();
        }
    }
}
