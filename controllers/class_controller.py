"""
Class Management Controller
Handles class definitions, loading, and management operations.
"""

import os
from PyQt5.QtWidgets import QMessageBox, QInputDialog, QLineEdit
from PyQt5.QtGui import QStandardItem


class ClassController:
    """Controller for class management operations."""
    
    def __init__(self, main_window):
        """Initialize the class controller."""
        self.main_window = main_window
        
    def open_classes_txt(self):
        """Open classes.txt file from labels folder or create/choose new one."""
        # Check if we have a labels folder
        if not self.main_window.dataset.labels_folder:
            QMessageBox.warning(self.main_window, "No Labels Folder", 
                              "Please open a labels folder first or load images to create one automatically.")
            return
        
        # Try to find existing classes.txt in the labels folder
        existing_path = os.path.join(self.main_window.dataset.labels_folder, "classes.txt")
        
        if os.path.exists(existing_path):
            self._load_existing_classes(existing_path)
        else:
            self._handle_missing_classes_file(existing_path)
            
    def _load_existing_classes(self, existing_path):
        """Load existing classes.txt file."""
        if self.main_window.dataset.load_classes_txt(existing_path):
            self.update_classes_list(self.main_window.dataset.get_classes())
            self.update_classes_for_current_image()
            self.main_window.statusBar().showMessage(f"Loaded classes from {existing_path}", 3000)
        else:
            QMessageBox.warning(self.main_window, "Error", f"Failed to load classes from {existing_path}")
            
    def _handle_missing_classes_file(self, existing_path):
        """Handle the case when classes.txt doesn't exist."""
        reply = QMessageBox.question(self.main_window, 'Create Classes File', 
                                  "No classes.txt found. Would you like to create one?",
                                  QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        
        if reply == QMessageBox.Yes:
            self.edit_classes_txt(existing_path)
        else:
            self._choose_existing_classes_file()
            
    def _choose_existing_classes_file(self):
        """Let user choose an existing classes file."""
        from PyQt5.QtWidgets import QFileDialog
        classes_path, _ = QFileDialog.getOpenFileName(
            self.main_window, "Open Classes File", "", "Text Files (*.txt)")
        
        if classes_path and os.path.exists(classes_path):
            if self.main_window.dataset.load_classes_txt(classes_path):
                self.update_classes_list(self.main_window.dataset.get_classes())
                self.update_classes_for_current_image()
                self.main_window.statusBar().showMessage(f"Loaded classes from {classes_path}", 3000)
            else:
                QMessageBox.warning(self.main_window, "Error", f"Failed to load classes from {classes_path}")
                
    def edit_classes_txt(self, path):
        """Open a dialog to edit classes.txt file."""
        dialog = QInputDialog(self.main_window)
        dialog.setInputMode(QInputDialog.TextInput)
        dialog.setLabelText("Enter class names (one per line):")
        dialog.resize(400, 300)
        
        # If we have existing classes, pre-populate the dialog
        if self.main_window.dataset.classes:
            dialog.setTextValue("\n".join(self.main_window.dataset.classes))
        
        if dialog.exec_():
            classes_text = dialog.textValue()
            classes = [c.strip() for c in classes_text.split("\n") if c.strip()]
            
            # Update dataset classes
            self.main_window.dataset.classes = classes
            
            # Save to file
            if self.main_window.dataset.save_classes_txt(path):
                self.update_classes_list(self.main_window.dataset.classes)
                self.update_classes_for_current_image()
                self.main_window.statusBar().showMessage(f"Saved classes to {path}", 3000)
            else:
                QMessageBox.warning(self.main_window, "Error", f"Failed to save classes to {path}")
                
    def update_classes_list(self, classes):
        """Update classes ListView and ComboBoxes."""
        model = self.main_window.classes_model
        model.clear()
        model.setHorizontalHeaderLabels(["ID", "Class Name"])
        
        # Update the class list view
        for i, cls in enumerate(classes):
            id_item = QStandardItem(str(i))
            name_item = QStandardItem(cls)
            model.appendRow([id_item, name_item])
        
        # Update UI comboboxes
        self._update_class_comboboxes(classes)
        
    def _update_class_comboboxes(self, classes):
        """Update all class-related comboboxes."""
        # Update the "Use Default Class" combo box
        if hasattr(self.main_window.ui, 'comboBox_Classes_UseDefaultClass'):
            combo = self.main_window.ui.comboBox_Classes_UseDefaultClass
            combo.clear()
            for cls in classes:
                combo.addItem(cls)
            
            # Make sure the combo box is enabled if checkbox is checked
            use_default = self.main_window.ui.checkBox_Classes_UseDefaultClass.isChecked()
            combo.setEnabled(use_default)
            
        # Update the "Assign to Class" combo box in the AI Mode section
        if hasattr(self.main_window.ui, 'comboBox_AIModeGroupBox_AssignToClass'):
            combo = self.main_window.ui.comboBox_AIModeGroupBox_AssignToClass
            combo.clear()
            for i, cls in enumerate(classes):
                combo.addItem(f"{i}: {cls}")
                
    def update_classes_for_current_image(self):
        """Update the classes list with classes used in the current image."""
        model = self.main_window.classes_model
        model.clear()
        model.setHorizontalHeaderLabels(["ID", "Class Name"])
        
        if self.main_window.current_image_index >= 0:
            # Get the current image's class IDs
            annotations = self.main_window.dataset.get_annotations_for_image(self.main_window.current_image_index)
            class_ids = annotations.get('classes', [])
            
            # Convert class IDs to class names where possible
            for i, class_id in enumerate(class_ids):
                name = self._get_class_name_from_id(class_id)
                id_item = QStandardItem(str(class_id))
                name_item = QStandardItem(name)
                model.appendRow([id_item, name_item])
                
    def _get_class_name_from_id(self, class_id):
        """Convert class ID to class name."""
        try:
            idx = int(class_id)
            if 0 <= idx < len(self.main_window.dataset.classes):
                return self.main_window.dataset.classes[idx]
            else:
                return str(class_id) + " (unknown)"
        except (ValueError, TypeError):
            return str(class_id)
            
    def toggle_default_class(self):
        """Toggle default class for new annotations."""
        use_default = self.main_window.ui.checkBox_Classes_UseDefaultClass.isChecked()
        
        if hasattr(self.main_window.ui, 'comboBox_Classes_UseDefaultClass'):
            self.main_window.ui.comboBox_Classes_UseDefaultClass.setEnabled(use_default)
            
            if use_default:
                default_class = self.main_window.ui.comboBox_Classes_UseDefaultClass.currentText()
                if default_class:
                    self.main_window.annotation.set_default_class(default_class)
            else:
                self.main_window.annotation.set_default_class(None)
                
    def add_class_to_dataset(self):
        """Add a new class to the dataset and classes.txt file."""
        # Check if we have a dataset with classes
        if not self.main_window.dataset.classes_file_path:
            if not self._prepare_classes_file():
                return
        
        # Ask for the new class name
        class_name, ok = QInputDialog.getText(self.main_window, "Add New Class", 
                                           "Enter the name for the new class:",
                                           QLineEdit.Normal, "")
                                           
        if ok and class_name.strip():
            class_name = class_name.strip()
            
            # Check for duplicates
            if class_name in self.main_window.dataset.classes:
                QMessageBox.information(self.main_window, "Duplicate Class", 
                                     f"Class '{class_name}' already exists.")
                return
            
            # Add the class
            self.main_window.dataset.add_class(class_name)
            
            # Save to file
            if self.main_window.dataset.save_classes_txt():
                self._on_class_added(class_name)
            else:
                QMessageBox.warning(self.main_window, "Error", "Failed to save classes to file.")
                
    def _prepare_classes_file(self):
        """Prepare classes file if it doesn't exist."""
        if not self.main_window.dataset.labels_folder:
            QMessageBox.warning(self.main_window, "No Labels Folder", 
                              "Please open a labels folder first.")
            return False
        
        # Create path for a new classes.txt file
        classes_path = os.path.join(self.main_window.dataset.labels_folder, "classes.txt")
        
        reply = QMessageBox.question(self.main_window, 'Create Classes File', 
                                  f"No classes.txt found. Would you like to create one at {classes_path}?",
                                  QMessageBox.Yes | QMessageBox.No)
                              
        return reply == QMessageBox.Yes
        
    def _on_class_added(self, class_name):
        """Handle successful class addition."""
        # Update UI
        self.update_classes_list(self.main_window.dataset.classes)
        
        # Set newly added class as selected in default combobox
        if hasattr(self.main_window.ui, 'comboBox_Classes_UseDefaultClass'):
            index = self.main_window.ui.comboBox_Classes_UseDefaultClass.findText(class_name)
            if index >= 0:
                self.main_window.ui.comboBox_Classes_UseDefaultClass.setCurrentIndex(index)
                
        # Show confirmation
        self.main_window.statusBar().showMessage(f"Added new class: {class_name}", 3000)
