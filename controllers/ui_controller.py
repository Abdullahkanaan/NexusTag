"""
UI Controller
Handles UI interactions, zoom, navigation, and visual settings.
"""

import os
from PyQt5.QtWidgets import QColorDialog, QMessageBox, QInputDialog, QLineEdit
from PyQt5.QtGui import QColor, QStandardItem, QPixmap
from PyQt5.QtCore import Qt

from models.shape import Shape


class UIController:
    """Controller for UI operations and visual settings."""
    
    def __init__(self, main_window):
        """Initialize the UI controller."""
        self.main_window = main_window
        
    def next_image(self):
        """Move to the next image in the dataset."""
        if self.main_window.current_image_index < self.main_window.dataset.get_image_count() - 1:
            if self.main_window.auto_save_enabled:
                self.main_window.save_current_annotations()
                
            self.main_window.current_image_index += 1
            self.main_window.load_current_image()
            self.main_window.is_verified = False
            self.update_verification_ui()
        else:
            QMessageBox.information(self.main_window, "End of Dataset", "You've reached the end of the dataset")
            
    def previous_image(self):
        """Move to the previous image in the dataset."""
        if self.main_window.current_image_index > 0:
            if self.main_window.auto_save_enabled:
                self.main_window.save_current_annotations()
                
            self.main_window.current_image_index -= 1
            self.main_window.load_current_image()
            self.main_window.is_verified = False
            self.update_verification_ui()
            
    def verify_image(self):
        """Toggle verification status of the current image."""
        self.main_window.is_verified = self.main_window.ui.commandLinkButton_BottomWidget_VerifyFrame.isChecked()
        self.main_window.dataset.set_image_verified(self.main_window.current_image_index, self.main_window.is_verified)
        self.update_verification_ui()
        
        # Update the file list to reflect verification status
        if hasattr(self.main_window, 'files_model'):
            self.main_window.file_controller.update_file_list_item(self.main_window.current_image_index)
        
        # Show status message
        status = "verified" if self.main_window.is_verified else "unverified"
        self.main_window.statusBar().showMessage(f"Image {status}", 3000)
        
    def update_verification_ui(self):
        """Update UI based on verification status."""
        self.main_window.ui.commandLinkButton_BottomWidget_VerifyFrame.setChecked(self.main_window.is_verified)
        
        if self.main_window.is_verified:
            # Change background color to light green when verified
            self.main_window.ui.widget_RightPanel_Bottom.setStyleSheet("background-color: #D4EDDA;")
        else:
            # Reset background color
            self.main_window.ui.widget_RightPanel_Bottom.setStyleSheet("")
            
    def toggle_auto_save(self):
        """Toggle auto-save mode."""
        self.main_window.auto_save_enabled = self.main_window.ui.checkBox_BottomWidget_AutoSaveMode.isChecked()
        
    def change_box_color(self):
        """Change the color of bounding boxes."""
        color = QColorDialog.getColor(self.main_window.box_color, self.main_window, "Select Box Color")
        if color.isValid():
            self.main_window.box_color = color
            
            # Update the drawing color for the canvas
            self.main_window.canvas.set_drawing_color(color)
            
            # Also update the default color for all shapes
            Shape.line_color = color
            
            # Create a matching fill color with more transparency
            fill_color = QColor(color)
            fill_color.setAlpha(30)  # Make it transparent
            Shape.fill_color = fill_color
            
            # Repaint
            self.main_window.canvas.update()
            
    def change_border_width(self):
        """Change the border width of bounding boxes."""
        width = self.main_window.ui.spinBox_BottomWidget_ChangeBorderWidth.value()
        self.main_window.border_width = width
        
        # Store the line width in the Shape class
        Shape.line_width = width
        
        # Adjust point size to be proportional but not as extreme
        Shape.point_size = width * 2
        
        # Repaint
        self.main_window.canvas.update()
        
    def toggle_hide_labels(self):
        """Toggle visibility of labels and boxes."""
        self.main_window.hide_labels = self.main_window.ui.commandLinkButton_BottomWidget_HideLabels.isChecked()
        
        if self.main_window.hide_labels:
            # Hide labels and boxes
            self.main_window.canvas.set_visible_shapes(False)
        else:
            # Show labels and boxes
            self.main_window.canvas.set_visible_shapes(True)
            self.main_window.canvas.set_painting_labels(True)
            
    def zoom_in(self, pos=None):
        """Zoom in at the cursor position."""
        cursor_pos = self.main_window.canvas.mapFromGlobal(self.main_window.cursor().pos()) if pos is None else pos
        self.main_window.canvas.zoom_in(cursor_pos)
        self.update_zoom_level(self.main_window.canvas.zoom_level)
        
    def zoom_out(self, pos=None):
        """Zoom out at the cursor position."""
        cursor_pos = self.main_window.canvas.mapFromGlobal(self.main_window.cursor().pos()) if pos is None else pos
        self.main_window.canvas.zoom_out(cursor_pos)
        self.update_zoom_level(self.main_window.canvas.zoom_level)
        
    def update_zoom_level(self, zoom_level):
        """Update the zoom level display based on canvas events."""
        self.main_window.zoom_level = zoom_level
        self.main_window.ui.label_BottomWidget_Zoom.setText(f"{zoom_level}%")
        
    def center_image(self):
        """Reset zoom to 100% and center the image in the view."""
        if self.main_window.canvas.pixmap and not self.main_window.canvas.pixmap.isNull():
            # Reset zoom level to 100%
            img_width = self.main_window.canvas.pixmap.width()
            img_height = self.main_window.canvas.pixmap.height()
            canvas_width = self.main_window.canvas.width()
            canvas_height = self.main_window.canvas.height()
            
            if img_width > canvas_width or img_height > canvas_height:
                self.main_window.statusBar().showMessage("Image centered and fit to view", 2000)
            else:
                self.main_window.zoom_level = 100
                self.main_window.canvas.zoom_level = 100
                self.main_window.canvas.scale = 1.0
                self.main_window.ui.label_BottomWidget_Zoom.setText(f"{self.main_window.zoom_level}%")
                self.main_window.statusBar().showMessage("Image centered at 100% zoom", 2000)
            
            # Center the image in the view
            self.main_window.canvas.center_pixmap()
            self.main_window.canvas.update()
            
    def delete_current_image(self):
        """Delete the current image with confirmation."""
        if self.main_window.current_image_index >= 0:
            if not self.main_window.confirmed_delete:
                reply = QMessageBox.question(self.main_window, 'Delete Image', 
                                           "Are you sure you want to delete this image?",
                                           QMessageBox.Yes | QMessageBox.No)
                
                if reply == QMessageBox.Yes:
                    self.main_window.confirmed_delete = True
                    self._perform_image_deletion()
            else:
                self._perform_image_deletion()
                
    def _perform_image_deletion(self):
        """Perform the actual image deletion."""
        self.main_window.dataset.delete_image(self.main_window.current_image_index)
        
        # Update current index if needed
        if self.main_window.current_image_index >= self.main_window.dataset.get_image_count():
            self.main_window.current_image_index = self.main_window.dataset.get_image_count() - 1
            
        if self.main_window.current_image_index >= 0:
            self.main_window.load_current_image()
        else:
            # No more images
            self.main_window.canvas.reset_state()
            
    def update_status_bar(self, pos, width=None, height=None):
        """Update status bar with coordinates and dimensions."""
        if width is not None and height is not None:
            status = f"X: {int(pos.x())}, Y: {int(pos.y())}, Width: {int(width)}, Height: {int(height)}"
        else:
            status = f"X: {int(pos.x())}, Y: {int(pos.y())}"
        
        self.main_window.statusBar().showMessage(status)
