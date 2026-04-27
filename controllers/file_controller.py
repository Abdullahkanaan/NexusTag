"""
File Operations Controller
Handles file and folder operations, data import/export functionality.
"""

import os
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from PyQt5.QtGui import QStandardItem, QBrush, QColor

from utils.exporters import AnnotationExporter
from dialogs.export_dialog import ExportDialog


class FileController:
    """Controller for file and folder operations."""
    
    def __init__(self, main_window):
        """Initialize the file controller."""
        self.main_window = main_window
        
    def open_images_folder(self):
        """Open and load images from a folder."""
        folder_path = QFileDialog.getExistingDirectory(self.main_window, "Open Images Folder")
        if folder_path:
            self.main_window.dataset.load_images(folder_path)
            self.check_labels_folder()
            self.populate_file_list()
            self.load_first_image()
            
    def open_labels_folder(self):
        """Open and set the labels folder."""
        folder_path = QFileDialog.getExistingDirectory(self.main_window, "Open Labels Folder")
        if folder_path:
            self.main_window.dataset.set_labels_folder(folder_path)
            self.populate_file_list()
            
    def check_labels_folder(self):
        """Create labels folder if it doesn't exist."""
        images_dir = self.main_window.dataset.images_folder
        if images_dir:
            labels_dir = os.path.join(os.path.dirname(images_dir), 'labels')
            if not os.path.exists(labels_dir):
                os.makedirs(labels_dir)
                self.main_window.dataset.set_labels_folder(labels_dir)
                
    def export_annotations(self):
        """Export annotations in various formats."""
        dialog = ExportDialog(self.main_window)
        if dialog.exec_():
            format_type = dialog.get_selected_format()
            export_dir = dialog.get_export_directory()
            
            if export_dir:
                exporter = AnnotationExporter()
                labels_dir = os.path.join(export_dir, f"labels-{format_type}")
                
                if not os.path.exists(labels_dir):
                    os.makedirs(labels_dir)
                
                # Export annotations to the selected format
                exporter.export_annotations(self.main_window.dataset, format_type, labels_dir)
                
                # Save classes.txt to the export directory if we have classes
                if self.main_window.dataset.classes:
                    classes_path = os.path.join(labels_dir, "classes.txt") 
                    self.main_window.dataset.save_classes_txt(classes_path)
                
                QMessageBox.information(self.main_window, "Export Complete", 
                                     f"Annotations exported to {labels_dir} in {format_type} format.")
                                     
    def create_config_yaml(self):
        """Create config.yaml file with class definitions."""
        file_path, _ = QFileDialog.getSaveFileName(
            self.main_window, "Save config.yaml", 
            os.path.join(self.main_window.dataset.labels_folder, "config.yaml"), 
            "YAML Files (*.yaml)")
        if file_path:
            self.main_window.dataset.create_config_yaml(file_path)
            QMessageBox.information(self.main_window, "Config Created", 
                                 f"Configuration file created at {file_path}")
                                 
    def load_first_image(self):
        """Load the first image in the dataset."""
        if self.main_window.dataset.get_image_count() > 0:
            self.main_window.current_image_index = 0
            self.main_window.load_current_image()
            
    def file_list_clicked(self, index):
        """Handle file list click to load specific image."""
        if index.isValid():
            row = index.row()
            self.main_window.current_image_index = row
            self.main_window.load_current_image()
            
    def populate_file_list(self):
        """Populate file list with images and corresponding labels."""
        model = self.main_window.files_model
        model.clear()
        model.setHorizontalHeaderLabels(["Image", "Label", "Verified"])
        
        for i in range(self.main_window.dataset.get_image_count()):
            img_name = os.path.basename(self.main_window.dataset.get_image_path_by_index(i))
            label_name = self.main_window.dataset.get_label_name_by_index(i) or "Not labeled"
            is_verified = self.main_window.dataset.is_image_verified(i)
            
            # Create items for each column
            img_item = QStandardItem(img_name)
            label_item = QStandardItem(label_name)
            verified_item = QStandardItem("✓" if is_verified else "✗")
            
            # Set colors based on verification status
            self._set_item_colors([img_item, label_item, verified_item], is_verified)
            
            model.appendRow([img_item, label_item, verified_item])
        
    def _set_item_colors(self, items, is_verified):
        """Set colors for file list items based on verification status."""
        if is_verified:
            # Green background for verified images
            color = QColor(200, 255, 200)
            text_color = QColor(0, 128, 0)  # Dark green text for verified column
        else:
            # Light red background for unverified images
            color = QColor(255, 220, 220)
            text_color = QColor(200, 0, 0)  # Red text for verified column
            
        for i, item in enumerate(items):
            item.setBackground(QBrush(color))
            if i == 2:  # Verified column
                item.setForeground(QBrush(text_color))
                
    def update_file_list_item(self, index):
        """Update a specific item in the file list."""
        model = self.main_window.files_model
        if 0 <= index < model.rowCount():
            is_verified = self.main_window.dataset.is_image_verified(index)
            
            # Update verification status display
            verified_item = model.item(index, 2)
            if verified_item:
                verified_item.setText("✓" if is_verified else "✗")
            
            # Update colors for all columns of this row
            items = []
            for col in range(3):  # 3 columns: image, label, verified
                item = model.item(index, col)
                if item:
                    items.append(item)
                    
            if items:
                self._set_item_colors(items, is_verified)
