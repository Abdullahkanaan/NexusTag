from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QGraphicsPixmapItem, QInputDialog, QDialog, QVBoxLayout, 
    QHBoxLayout, QComboBox, QLineEdit, QPushButton, QLabel
)

class ShortcutsHandler:
    def __init__(self, main_window):
        self.main_window = main_window
        
        # Define shortcut mappings
        self.shortcuts = {
            Qt.Key_S: self.save_current_annotations,
            Qt.Key_Space: self.verify_image,
            Qt.Key_W: self.start_drawing,
            Qt.Key_D: self.next_image,
            Qt.Key_A: self.previous_image,
            Qt.Key_Z: self.zoom_in,
            Qt.Key_X: self.zoom_out,
            Qt.Key_Q: self.delete_selected_box,
            Qt.Key_E: self.set_class_for_selected,
            Qt.Key_R: self.run_detection_on_current,
            Qt.Key_C: self.select_box_mode,
            Qt.Key_V: self.deselect_box_mode,
            Qt.Key_Escape: self.toggle_shortcuts_info,
        }
        
        # Define shortcuts with modifiers
        self.ctrl_shortcuts = {
            Qt.Key_Z: self.undo_last_action,
        }
        
        self.ctrl_shift_shortcuts = {
            Qt.Key_D: self.delete_current_image,
        }
        
        self.shift_shortcuts = {
            0: self.select_all_boxes,  # Using 0 instead of Qt.Key_None which doesn't exist
        }
        
        # State variables
        self.is_c_pressed = False
        self.is_v_pressed = False
        self.is_shift_pressed = False
        
    def handle_key_press(self, event):
        """Handle key press events."""
        key = event.key()
        modifiers = event.modifiers()
        
        # For C and V keys, we need to explicitly track the state
        if key == Qt.Key_C:
            self.is_c_pressed = True
            self.select_box_mode()
            return

        if key == Qt.Key_V:
            self.is_v_pressed = True
            self.deselect_box_mode()
            return
            
        # Handle Shift key state
        if key == Qt.Key_Shift:
            self.is_shift_pressed = True
            self.select_all_boxes()
            return
            
        # Handle Ctrl+Z
        if modifiers & Qt.ControlModifier and key == Qt.Key_Z:
            self.undo_last_action()
            return
            
        # Handle Ctrl+Shift+D
        if modifiers & Qt.ControlModifier and modifiers & Qt.ShiftModifier and key == Qt.Key_D:
            self.delete_current_image()
            return
            
        # Handle other shortcuts
        if key in self.shortcuts:
            self.shortcuts[key]()
            
    def handle_key_release(self, event):
        """Handle key release events."""
        key = event.key()
        
        if key == Qt.Key_C:
            self.is_c_pressed = False
            self.main_window.select_mode = False

        if key == Qt.Key_V:
            self.is_v_pressed = False
            self.main_window.deselect_mode = False
            
        if key == Qt.Key_Shift:
            self.is_shift_pressed = False
            
    # Shortcut methods
    def save_current_annotations(self):
        """Save current annotations (key: s)"""
        self.main_window.save_current_annotations()
        
    def verify_image(self):
        """Toggle image verification (key: Space)"""
        button = self.main_window.ui.commandLinkButton_BottomWidget_VerifyFrame
        button.setChecked(not button.isChecked())
        self.main_window.verify_image()
        
    def start_drawing(self):
        """Enter drawing mode (key: w)"""
        # Only work when an image is loaded
        if self.main_window.current_image_index >= 0:
            if not self.main_window.is_drawing:
                self.main_window.canvas.set_editing(False)
                self.main_window.is_drawing = True
            else:
                if self.main_window.canvas.current:
                    self.main_window.canvas.finalise()
                self.main_window.canvas.set_editing(True)
                self.main_window.is_drawing = False
        
    def next_image(self):
        """Go to next image (key: d)"""
        self.main_window.next_image()
        
    def previous_image(self):
        """Go to previous image (key: a)"""
        self.main_window.previous_image()
        
    def zoom_in(self):
        """Zoom in at mouse position (key: z)"""
        self.main_window.zoom_in()
        
    def zoom_out(self):
        """Zoom out at mouse position (key: x)"""
        self.main_window.zoom_out()
        
    def delete_selected_box(self):
        """Delete selected boxes (key: q)"""
        if self.main_window.canvas.selected_shapes:
            deleted = self.main_window.canvas.delete_selected()
            count = len(deleted) if deleted else 0
            self.main_window.statusBar().showMessage(f"{count} box(es) deleted", 3000)
        else:
            self.main_window.statusBar().showMessage("No boxes selected to delete", 3000)
        
    def set_class_for_selected(self):
        """Set class for selected boxes (key: e)"""
        if self.main_window.canvas.selected_shapes:
            # Check if "Use default class" checkbox is checked
            if hasattr(self.main_window.ui, 'checkBox_Classes_UseDefaultClass') and self.main_window.ui.checkBox_Classes_UseDefaultClass.isChecked():
                # Use the selected default class directly
                selected_class = self.main_window.ui.comboBox_Classes_UseDefaultClass.currentText()
                
                # Ensure we're using the class name, not the index
                if ":" in selected_class:
                    # Handle the case where the text might be in format "0: class_name"
                    selected_class = selected_class.split(":", 1)[1].strip()
                
                if selected_class:
                    # Set the class for all selected shapes
                    for shape in self.main_window.canvas.selected_shapes:
                        shape.label = selected_class
                    
                    self.main_window.canvas.update()
                    # Update the class list display if needed
                    if hasattr(self.main_window, 'update_classes_for_current_image'):
                        self.main_window.update_classes_for_current_image()
                    # Show confirmation message in status bar
                    count = len(self.main_window.canvas.selected_shapes)
                    self.main_window.statusBar().showMessage(f"Class set to {selected_class} for {count} box(es)", 2000)
            else:
                # Create a custom dialog to allow both selecting existing classes or adding a new one
                dialog = QDialog(self.main_window)
                dialog.setWindowTitle("Set Class")
                dialog.setMinimumWidth(300)
                layout = QVBoxLayout()

                # Add combobox for existing classes
                layout.addWidget(QLabel("Select an existing class:"))
                combobox = QComboBox()
                combobox.addItems(self.main_window.dataset.classes)
                layout.addWidget(combobox)

                # Add section for adding a new class
                layout.addWidget(QLabel("Or add a new class:"))
                new_class_input = QLineEdit()
                layout.addWidget(new_class_input)

                # Add buttons
                button_layout = QHBoxLayout()
                ok_button = QPushButton("OK")
                cancel_button = QPushButton("Cancel")
                button_layout.addWidget(ok_button)
                button_layout.addWidget(cancel_button)
                layout.addLayout(button_layout)

                dialog.setLayout(layout)

                # Connect signals
                ok_button.clicked.connect(dialog.accept)
                cancel_button.clicked.connect(dialog.reject)

                # Execute dialog
                result = dialog.exec_()
                
                if result == QDialog.Accepted:
                    selected_class = None
                    new_class = new_class_input.text().strip()
                    
                    if new_class:
                        # User entered a new class
                        selected_class = new_class
                        
                        # Add the new class to dataset
                        if selected_class not in self.main_window.dataset.classes:
                            self.main_window.dataset.add_class(selected_class)
                            
                            # Save to classes.txt
                            if self.main_window.dataset.save_classes_txt():
                                # Update combo boxes and class list
                                self.main_window.update_classes_list(self.main_window.dataset.classes)
                                self.main_window.statusBar().showMessage(f"Added new class: {selected_class}", 2000)
                            else:
                                self.main_window.statusBar().showMessage("Failed to save new class to classes.txt", 3000)
                    else:
                        # User selected from existing classes
                        selected_class = combobox.currentText()
                        if ":" in selected_class:
                            # Handle the case where the text might be in format "0: class_name"
                            selected_class = selected_class.split(":", 1)[1].strip()
                    
                    if selected_class:
                        # Set the class for all selected shapes
                        for shape in self.main_window.canvas.selected_shapes:
                            shape.label = selected_class
                        
                        self.main_window.canvas.update()
                        # Update the class list display if needed
                        if hasattr(self.main_window, 'update_classes_for_current_image'):
                            self.main_window.update_classes_for_current_image()
                        # Show confirmation message in status bar
                        count = len(self.main_window.canvas.selected_shapes)
                        self.main_window.statusBar().showMessage(f"Class set to {selected_class} for {count} box(es)", 2000)
        else:
            # Show message if no shapes are selected
            self.main_window.statusBar().showMessage("No shapes selected. Select a shape first, then press E to set class.", 3000)
        
    def run_detection_on_current(self):
        """Run detection on current image (key: r)"""
        self.main_window.run_detection_on_current()
        
    def select_box_mode(self):
        """Enter select box mode (key: c)"""
        # In the new Canvas implementation, we always have selection capability when in edit mode
        self.main_window.canvas.set_editing(True)
        self.main_window.is_drawing = False
        
        # Still maintain old state variables for compatibility
        self.main_window.select_mode = True
        self.main_window.deselect_mode = False
        
        # Show status message for hover selection
        self.main_window.statusBar().showMessage("Hover selection mode: Move mouse over boxes while holding C to select multiple boxes", 3000)
        
    def deselect_box_mode(self):
        """Enter deselect box mode (key: v)"""
        # In the new Canvas implementation, we don't have a specific deselect mode,
        # but we can just deselect any currently selected shape
        if not self.main_window.canvas.selected_shapes:
            self.main_window.statusBar().showMessage("No boxes selected to deselect", 3000)
        
        # Still maintain old state variables for compatibility
        self.main_window.select_mode = False
        self.main_window.deselect_mode = True
        
        # Show status message for hover deselection
        self.main_window.statusBar().showMessage("Hover deselection mode: Move mouse over selected boxes while holding V to deselect them", 3000)
        
    def toggle_shortcuts_info(self):
        """Show or hide shortcuts info dialog (key: Escape)"""
        self.main_window.show_shortcuts()
        
    def undo_last_action(self):
        """Undo last action (key: Ctrl+Z)"""
        if self.main_window.canvas.undo():
            self.main_window.statusBar().showMessage("Undo successful", 2000)
        else:
            self.main_window.statusBar().showMessage("Nothing to undo", 2000)
        
    def delete_current_image(self):
        """Delete current image (key: Ctrl+Shift+D)"""
        self.main_window.delete_current_image()
        
    def select_all_boxes(self):
        """Select all boxes (key: Shift)"""
        if self.main_window.canvas.shapes:
            self.main_window.canvas.select_all_shapes()
            count = len(self.main_window.canvas.shapes)
            self.main_window.statusBar().showMessage(f"All {count} boxes selected", 2000)
        else:
            self.main_window.statusBar().showMessage("No boxes to select", 2000) 