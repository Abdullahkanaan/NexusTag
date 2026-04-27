"""
AI Detection Controller
Handles all AI model operations and detection functionality.
"""

import os
from PyQt5.QtWidgets import QMessageBox, QProgressDialog, QInputDialog, QLineEdit, QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap

from utils.ai_detector import AIDetector
from models.shape import Shape


class AIController:
    """Controller for AI detection operations."""
    
    def __init__(self, main_window):
        """Initialize the AI controller."""
        self.main_window = main_window
        self.ai_detector = AIDetector()
        
    def update_model_family(self):
        """Update available models based on selected family."""
        selected_family = self.main_window.ui.comboBox_AIModeGroupBox_ModelFamily.currentText()
        
        # Update AI detector's model family
        self.ai_detector.set_model_family(selected_family)
        
        # Enable model upload button
        self.main_window.ui.pushButton_AIModeGroupBox_UploadModel.setEnabled(True)
        
        # Update UI to show model family is selected
        self.main_window.statusBar().showMessage(f"Selected model family: {selected_family}", 3000)
        
    def upload_model(self):
        """Upload custom model file."""
        file_filter = ""
        selected_family = self.main_window.ui.comboBox_AIModeGroupBox_ModelFamily.currentText()
        
        # Set file filter based on model family
        if selected_family == "YOLO":
            file_filter = "YOLO Models (*.pt *.pth *.weights);;All Files (*)"
        elif selected_family == "TensorFlow":
            file_filter = "TensorFlow Models (*.pb *.tflite *.h5);;All Files (*)"
        elif selected_family == "PyTorch":
            file_filter = "PyTorch Models (*.pt *.pth);;All Files (*)"
        else:
            file_filter = "All Files (*)"
            
        from PyQt5.QtWidgets import QFileDialog
        model_path, _ = QFileDialog.getOpenFileName(
            self.main_window, "Open AI Model", "", file_filter)
            
        if model_path and os.path.exists(model_path):
            # Set the model in the detector
            success = self.ai_detector.load_model(model_path)
            
            if success:
                self._on_model_loaded(model_path)
            else:
                QMessageBox.warning(self.main_window, "Model Loading Error", 
                                  f"Failed to load model from {model_path}.")
                
    def _on_model_loaded(self, model_path):
        """Handle successful model loading."""
        model_name = os.path.basename(model_path)
        self.main_window.statusBar().showMessage(f"Model loaded: {model_name}", 3000)
        
        # Enable the YAML upload button
        self.main_window.ui.pushButton_AIModeGroupBox_UploadModelYaml.setEnabled(True)
        
        # Enable detection controls
        self._enable_detection_controls()
        
    def _enable_detection_controls(self):
        """Enable detection-related UI controls."""
        controls = [
            'comboBox_AIModeGroupBox_ChooseObject',
            'comboBox_AIModeGroupBox_AssignToClass',
            'comboBox_AIModeGroupBox_AllSingleFrame',
            'commandLinkButton_AIModeGroupBox_RunDetection'
        ]
        
        for control_name in controls:
            if hasattr(self.main_window.ui, control_name):
                getattr(self.main_window.ui, control_name).setEnabled(True)
                
    def upload_model_yaml(self):
        """Upload model YAML configuration and extract classes."""
        from PyQt5.QtWidgets import QFileDialog
        yaml_path, _ = QFileDialog.getOpenFileName(
            self.main_window, "Open Model YAML", "", "YAML Files (*.yaml *.yml);;All Files (*)")
            
        if yaml_path and os.path.exists(yaml_path):
            # Load classes from YAML using the AI detector
            classes = self.ai_detector.load_classes_from_yaml(yaml_path)
            
            if classes and len(classes) > 0:
                self._update_ui_with_classes(classes)
                self.main_window.statusBar().showMessage(f"Loaded {len(classes)} classes from YAML", 3000)
            else:
                QMessageBox.warning(self.main_window, "YAML Loading Error", 
                                  "Failed to load classes from YAML file.")
                
    def _update_ui_with_classes(self, classes):
        """Update UI elements with loaded classes."""
        # Update the "Choose Object" combobox with model classes
        if hasattr(self.main_window.ui, 'comboBox_AIModeGroupBox_ChooseObject'):
            combo = self.main_window.ui.comboBox_AIModeGroupBox_ChooseObject
            combo.clear()
            combo.addItem("All Classes")
            
            for i, cls in enumerate(classes):
                if cls:  # Skip None values
                    combo.addItem(f"{i}: {cls}")
        
        # Update the dataset classes for compatibility
        if not self.main_window.dataset.classes:
            self.main_window.dataset.classes = classes
            self.main_window.update_classes_list(classes)
            
    def run_ai_detection(self):
        """Run detection based on configured options."""
        # Check if model is loaded
        if not self.ai_detector.model_loaded():
            QMessageBox.warning(self.main_window, "AI Detection", "No AI model loaded for detection.")
            return
        
        # Get detection parameters
        detect_class_idx = self._get_detection_class()
        target_class = self._get_target_class()
        
        if not target_class:
            self.main_window.statusBar().showMessage("Detection cancelled - no target class specified", 3000)
            return
        
        # Set detection parameters
        self.ai_detector.set_detection_class(detect_class_idx)
        self.ai_detector.set_target_class(target_class)
        
        # Check processing scope
        process_all = self._should_process_all_images()
        
        # Run detection
        if process_all:
            self.run_detection_on_all()
        else:
            self.run_detection_on_current()
            
    def _get_detection_class(self):
        """Get the class index to detect."""
        detect_class_idx = None
        if hasattr(self.main_window.ui, 'comboBox_AIModeGroupBox_ChooseObject'):
            selected_class = self.main_window.ui.comboBox_AIModeGroupBox_ChooseObject.currentText()
            
            # Parse class index if not "All Classes"
            if selected_class != "All Classes" and ":" in selected_class:
                try:
                    detect_class_idx = int(selected_class.split(":", 1)[0].strip())
                except (ValueError, IndexError):
                    detect_class_idx = None
        return detect_class_idx
        
    def _get_target_class(self):
        """Get the target class for labeling detections."""
        target_class = None
        if hasattr(self.main_window.ui, 'comboBox_AIModeGroupBox_AssignToClass'):
            selected_target = self.main_window.ui.comboBox_AIModeGroupBox_AssignToClass.currentText()
            
            # If the target class contains ":", extract just the name portion
            if ":" in selected_target:
                target_class = selected_target.split(":", 1)[1].strip()
            else:
                target_class = selected_target
        
        # If no target class is selected, ask the user
        if not target_class:
            target_class, ok = QInputDialog.getText(self.main_window, "Target Class", 
                                                 "Enter the class name for detected objects:",
                                                 QLineEdit.Normal, "")
            if not ok or not target_class:
                return None
                
        return target_class
        
    def _should_process_all_images(self):
        """Check if we should process all images or just the current one."""
        process_all = False
        if hasattr(self.main_window.ui, 'comboBox_AIModeGroupBox_AllSingleFrame'):
            selected_scope = self.main_window.ui.comboBox_AIModeGroupBox_AllSingleFrame.currentText()
            process_all = "All" in selected_scope
        return process_all
        
    def run_detection_on_current(self):
        """Run detection on current image."""
        if self.main_window.current_image_index < 0:
            QMessageBox.warning(self.main_window, "AI Detection", "No image loaded.")
            return
            
        # Get the current image path and verify it exists
        img_path = self.main_window.dataset.get_image_path_by_index(self.main_window.current_image_index)
        if not os.path.exists(img_path):
            QMessageBox.warning(self.main_window, "AI Detection", f"Image file not found: {img_path}")
            return
        
        # Show progress dialog
        progress = QProgressDialog("Running AI detection...", "Cancel", 0, 100, self.main_window)
        progress.setWindowModality(Qt.WindowModal)
        progress.setValue(10)
        QApplication.processEvents()
        
        try:
            if self.main_window.canvas.pixmap.isNull():
                QMessageBox.warning(self.main_window, "AI Detection", "No image loaded in canvas.")
                progress.setValue(100)
                return

            import cv2
            original_img = cv2.imread(img_path)
            if original_img is None:
                QMessageBox.warning(self.main_window, "AI Detection", "Could not load image file.")
                progress.setValue(100)
                return

            original_height, original_width = original_img.shape[:2]
            self.ai_detector.confidence_threshold = 0.5
            
            progress.setValue(30)
            QApplication.processEvents()
            
            # Clear existing shapes before detection
            old_shapes = self.main_window.canvas.shapes.copy()
            self.main_window.canvas.shapes = []
                
            # Run detection
            detection_results = self.ai_detector.detect_objects(img_path)
            progress.setValue(70)
            QApplication.processEvents()
            
            # Check if detection was cancelled
            if progress.wasCanceled():
                self.main_window.canvas.shapes = old_shapes
                self.main_window.canvas.update()
                progress.setValue(100)
                return
            
            # Process results using original image dimensions (not canvas dimensions)
            shapes = self._process_detection_results(detection_results, original_width, original_height)
            
            if shapes:
                self.main_window.canvas.shapes.extend(shapes)
                self.main_window.canvas.update()
                self.main_window.canvas.setModified(True)
                
                progress.setValue(100)
                QMessageBox.information(self.main_window, "AI Detection", 
                                     f"Detection complete. Found {len(shapes)} objects.")
            else:
                progress.setValue(100)
                QMessageBox.information(self.main_window, "AI Detection", "No objects detected.")
                
        except Exception as e:
            progress.setValue(100)
            error_msg = f"Error during detection: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self.main_window, "Detection Error", error_msg)
            
    def _process_detection_results(self, detection_results, image_width, image_height):
        """Process detection results and create shapes."""
        if not detection_results or 'boxes' not in detection_results or not detection_results['boxes']:
            return []

        boxes = detection_results['boxes']
        classes = detection_results.get('classes', [])
        shapes = []

        for i, box in enumerate(boxes):
            class_label = classes[i] if i < len(classes) else (self.ai_detector.get_target_class() or "unknown")
            shape = Shape(label=class_label)
            shape.paint_label = True
            shape.from_normalized_rect(box, image_width, image_height)
            shapes.append(shape)

        return shapes
        
    def run_detection_on_all(self):
        """Run detection on all images in the dataset."""
        # Check if we have images loaded
        total_images = self.main_window.dataset.get_image_count()
        if total_images == 0:
            QMessageBox.information(self.main_window, "AI Detection", "No images to process.")
            return
            
        # Show progress dialog
        progress = QProgressDialog("Running AI detection on all images...", "Cancel", 0, total_images, self.main_window)
        progress.setWindowModality(Qt.WindowModal)
        
        detected_objects = 0
        processed_images = 0
        
        for i in range(total_images):
            if progress.wasCanceled():
                break
                
            img_path = self.main_window.dataset.get_image_path_by_index(i)
            progress.setLabelText(f"Processing image {i+1}/{total_images}: {os.path.basename(img_path)}")
            QApplication.processEvents()
            
            try:
                # Run detection
                detection_results = self.ai_detector.detect_objects(img_path)
                
                if detection_results and 'boxes' in detection_results:
                    detected_objects += self._save_detection_results(i, img_path, detection_results)
                    processed_images += 1
                    
            except Exception as e:
                print(f"Error processing image {img_path}: {str(e)}")
                
            progress.setValue(i + 1)
            
        # If current image was processed, reload to show updated annotations
        if processed_images > 0 and self.main_window.current_image_index >= 0:
            self.main_window.load_current_image()
            
        QMessageBox.information(self.main_window, "AI Detection", 
                             f"Detection complete. Processed {processed_images} images, found {detected_objects} objects.")
                             
    def _save_detection_results(self, image_index, img_path, detection_results):
        """Save detection results for a specific image."""
        # Get image dimensions using OpenCV (same as YOLO processing)
        import cv2
        original_img = cv2.imread(img_path)
        if original_img is None:
            return 0

        img_height, img_width = original_img.shape[:2]
        
        # Get current annotations for this image
        annotations = self.main_window.dataset.get_annotations_for_image(image_index) or {'boxes': [], 'classes': []}
        
        # Get the target class for detections
        target_class = self.ai_detector.get_target_class()
        
        objects_added = 0
        # Add new detections to annotations
        for j, box in enumerate(detection_results['boxes']):
            # Add the normalized box coordinates
            annotations['boxes'].append(box)
            
            # Add the class label
            if 'classes' in detection_results and j < len(detection_results['classes']):
                class_label = detection_results['classes'][j]
            else:
                class_label = target_class or "unknown"
                
            annotations['classes'].append(class_label)
            objects_added += 1
        
        # Save updated annotations
        self.main_window.dataset.save_annotations_for_image(image_index, annotations)
        return objects_added
        
    def assign_class_to_selected(self):
        """Handle class assignment to selected shapes."""
        if not self.main_window.canvas.selected_shapes:
            self.main_window.statusBar().showMessage("No boxes selected. Select a box first.", 3000)
            return
        
        selected_text = self.main_window.ui.comboBox_AIModeGroupBox_AssignToClass.currentText()
        if selected_text:
            try:
                # Parse the class ID from format like "0: apple"
                parts = selected_text.split(':', 1)
                if len(parts) > 1:
                    class_name = parts[1].strip()
                else:
                    class_name = selected_text
                    
                # Set the class for selected shapes
                for shape in self.main_window.canvas.selected_shapes:
                    shape.label = class_name
                    
                # Update the display
                self.main_window.canvas.update()
                
                # Show confirmation message
                count = len(self.main_window.canvas.selected_shapes)
                self.main_window.statusBar().showMessage(f"Class set to '{class_name}' for {count} box(es)", 2000)
                
                # Update classes view if needed
                self.main_window.update_classes_for_current_image()
            except Exception as e:
                self.main_window.statusBar().showMessage(f"Error assigning class: {str(e)}", 3000)
