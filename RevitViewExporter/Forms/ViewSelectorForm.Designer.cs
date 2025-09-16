namespace RevitViewExporter.Forms
{
    partial class ViewSelectorForm
    {
        /// <summary>
        /// Required designer variable.
        /// </summary>
        private System.ComponentModel.IContainer components = null;

        /// <summary>
        /// Clean up any resources being used.
        /// </summary>
        /// <param name="disposing">true if managed resources should be disposed; otherwise, false.</param>
        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
            {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        #region Windows Form Designer generated code

        /// <summary>
        /// Required method for Designer support - do not modify
        /// the contents of this method with the code editor.
        /// </summary>
        private void InitializeComponent()
        {
            this.lblTitle = new System.Windows.Forms.Label();
            this.lblFilter = new System.Windows.Forms.Label();
            this.txtFilter = new System.Windows.Forms.TextBox();
            this.lblViewType = new System.Windows.Forms.Label();
            this.cboViewType = new System.Windows.Forms.ComboBox();
            this.lstViews = new System.Windows.Forms.ListView();
            this.colName = ((System.Windows.Forms.ColumnHeader)(new System.Windows.Forms.ColumnHeader()));
            this.colType = ((System.Windows.Forms.ColumnHeader)(new System.Windows.Forms.ColumnHeader()));
            this.colId = ((System.Windows.Forms.ColumnHeader)(new System.Windows.Forms.ColumnHeader()));
            this.chkSelectAll = new System.Windows.Forms.CheckBox();
            this.btnExport = new System.Windows.Forms.Button();
            this.btnCancel = new System.Windows.Forms.Button();
            this.lblCount = new System.Windows.Forms.Label();
            this.SuspendLayout();
            // 
            // lblTitle
            // 
            this.lblTitle.AutoSize = true;
            this.lblTitle.Font = new System.Drawing.Font("Microsoft Sans Serif", 12F, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.lblTitle.Location = new System.Drawing.Point(12, 9);
            this.lblTitle.Name = "lblTitle";
            this.lblTitle.Size = new System.Drawing.Size(269, 20);
            this.lblTitle.TabIndex = 0;
            this.lblTitle.Text = "Select views to export as images:";
            // 
            // lblFilter
            // 
            this.lblFilter.AutoSize = true;
            this.lblFilter.Location = new System.Drawing.Point(13, 45);
            this.lblFilter.Name = "lblFilter";
            this.lblFilter.Size = new System.Drawing.Size(79, 13);
            this.lblFilter.TabIndex = 1;
            this.lblFilter.Text = "Filter by name:";
            // 
            // txtFilter
            // 
            this.txtFilter.Location = new System.Drawing.Point(98, 42);
            this.txtFilter.Name = "txtFilter";
            this.txtFilter.Size = new System.Drawing.Size(200, 20);
            this.txtFilter.TabIndex = 2;
            this.txtFilter.TextChanged += new System.EventHandler(this.txtFilter_TextChanged);
            // 
            // lblViewType
            // 
            this.lblViewType.AutoSize = true;
            this.lblViewType.Location = new System.Drawing.Point(323, 45);
            this.lblViewType.Name = "lblViewType";
            this.lblViewType.Size = new System.Drawing.Size(58, 13);
            this.lblViewType.TabIndex = 3;
            this.lblViewType.Text = "View type:";
            // 
            // cboViewType
            // 
            this.cboViewType.DropDownStyle = System.Windows.Forms.ComboBoxStyle.DropDownList;
            this.cboViewType.FormattingEnabled = true;
            this.cboViewType.Location = new System.Drawing.Point(387, 42);
            this.cboViewType.Name = "cboViewType";
            this.cboViewType.Size = new System.Drawing.Size(180, 21);
            this.cboViewType.TabIndex = 4;
            this.cboViewType.SelectedIndexChanged += new System.EventHandler(this.cboViewType_SelectedIndexChanged);
            // 
            // lstViews
            // 
            this.lstViews.CheckBoxes = true;
            this.lstViews.Columns.AddRange(new System.Windows.Forms.ColumnHeader[] {
            this.colName,
            this.colType,
            this.colId});
            this.lstViews.FullRowSelect = true;
            this.lstViews.HideSelection = false;
            this.lstViews.Location = new System.Drawing.Point(12, 76);
            this.lstViews.Name = "lstViews";
            this.lstViews.Size = new System.Drawing.Size(555, 320);
            this.lstViews.TabIndex = 5;
            this.lstViews.UseCompatibleStateImageBehavior = false;
            this.lstViews.View = System.Windows.Forms.View.Details;
            // 
            // colName
            // 
            this.colName.Text = "Name";
            this.colName.Width = 250;
            // 
            // colType
            // 
            this.colType.Text = "Type";
            this.colType.Width = 150;
            // 
            // colId
            // 
            this.colId.Text = "ID";
            this.colId.Width = 100;
            // 
            // chkSelectAll
            // 
            this.chkSelectAll.AutoSize = true;
            this.chkSelectAll.Location = new System.Drawing.Point(12, 408);
            this.chkSelectAll.Name = "chkSelectAll";
            this.chkSelectAll.Size = new System.Drawing.Size(70, 17);
            this.chkSelectAll.TabIndex = 6;
            this.chkSelectAll.Text = "Select All";
            this.chkSelectAll.UseVisualStyleBackColor = true;
            this.chkSelectAll.CheckedChanged += new System.EventHandler(this.chkSelectAll_CheckedChanged);
            // 
            // btnExport
            // 
            this.btnExport.Location = new System.Drawing.Point(387, 408);
            this.btnExport.Name = "btnExport";
            this.btnExport.Size = new System.Drawing.Size(87, 28);
            this.btnExport.TabIndex = 7;
            this.btnExport.Text = "Export";
            this.btnExport.UseVisualStyleBackColor = true;
            this.btnExport.Click += new System.EventHandler(this.btnExport_Click);
            // 
            // btnCancel
            // 
            this.btnCancel.DialogResult = System.Windows.Forms.DialogResult.Cancel;
            this.btnCancel.Location = new System.Drawing.Point(480, 408);
            this.btnCancel.Name = "btnCancel";
            this.btnCancel.Size = new System.Drawing.Size(87, 28);
            this.btnCancel.TabIndex = 8;
            this.btnCancel.Text = "Cancel";
            this.btnCancel.UseVisualStyleBackColor = true;
            this.btnCancel.Click += new System.EventHandler(this.btnCancel_Click);
            // 
            // lblCount
            // 
            this.lblCount.AutoSize = true;
            this.lblCount.Location = new System.Drawing.Point(95, 409);
            this.lblCount.Name = "lblCount";
            this.lblCount.Size = new System.Drawing.Size(107, 13);
            this.lblCount.TabIndex = 9;
            this.lblCount.Text = "Showing 0 of 0 views";
            // 
            // ViewSelectorForm
            // 
            this.AcceptButton = this.btnExport;
            this.AutoScaleDimensions = new System.Drawing.SizeF(6F, 13F);
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.CancelButton = this.btnCancel;
            this.ClientSize = new System.Drawing.Size(579, 448);
            this.Controls.Add(this.lblCount);
            this.Controls.Add(this.btnCancel);
            this.Controls.Add(this.btnExport);
            this.Controls.Add(this.chkSelectAll);
            this.Controls.Add(this.lstViews);
            this.Controls.Add(this.cboViewType);
            this.Controls.Add(this.lblViewType);
            this.Controls.Add(this.txtFilter);
            this.Controls.Add(this.lblFilter);
            this.Controls.Add(this.lblTitle);
            this.FormBorderStyle = System.Windows.Forms.FormBorderStyle.FixedDialog;
            this.MaximizeBox = false;
            this.MinimizeBox = false;
            this.Name = "ViewSelectorForm";
            this.StartPosition = System.Windows.Forms.FormStartPosition.CenterScreen;
            this.Text = "Revit View Exporter";
            this.ResumeLayout(false);
            this.PerformLayout();

        }

        #endregion

        private System.Windows.Forms.Label lblTitle;
        private System.Windows.Forms.Label lblFilter;
        private System.Windows.Forms.TextBox txtFilter;
        private System.Windows.Forms.Label lblViewType;
        private System.Windows.Forms.ComboBox cboViewType;
        private System.Windows.Forms.ListView lstViews;
        private System.Windows.Forms.ColumnHeader colName;
        private System.Windows.Forms.ColumnHeader colType;
        private System.Windows.Forms.ColumnHeader colId;
        private System.Windows.Forms.CheckBox chkSelectAll;
        private System.Windows.Forms.Button btnExport;
        private System.Windows.Forms.Button btnCancel;
        private System.Windows.Forms.Label lblCount;
    }
}
