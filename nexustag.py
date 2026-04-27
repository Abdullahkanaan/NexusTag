"""
Nexus Tag: AI-Assisted Annotation Tool
Main application class using MVC architecture.
"""

import sys
import os

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget
)
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtGui import QColor, QStandardItemModel

# UI and Models
from app_ui import Ui_MainWindow
from models.annotation import Annotation
from models.dataset import Dataset
from models.canvas import Canvas
from models.shape import Shape

# Controllers
from controllers.ai_controller import AIController
from controllers.file_controller import FileController
from controllers.ui_controller import UIController
from controllers.class_controller import ClassController

# Utilities
from utils.shortcuts import ShortcutsHandler
from dialogs.shortcuts_info_dialog import ShortcutsInfoDialog


class NexusTag(QMainWindow):
    """Main application window with controller-based architecture."""
    
    def __init__(self):
        super().__init__()
        self._initialize_ui()
        self._initialize_data_models()
        self._initialize_controllers()
        self._setup_canvas()
        self._connect_signals()
        self._initialize_event_handling()
        
    def _initialize_ui(self):
        """Initialize the main UI."""
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowTitle("Nexus Tag - AI-Assisted Annotation Tool")
        
    def _initialize_data_models(self):
        """Initialize data models and state variables."""
        # Data models
        self.dataset = Dataset()
        self.annotation = Annotation()
        
        # State variables
        self.current_image_index = -1
        self.is_drawing = False
        self.select_mode = False
        self.deselect_mode = False
        self.is_verified = False
        self.auto_save_enabled = False
        self.confirmed_delete = False
        self.box_color = QColor(0, 255, 0)  # Default green
        self.border_width = 2
        self.hide_labels = False
        self.zoom_level = 100
        
        # Key state tracking
        self.key_states = {}
        
        # Initialize UI models
        self._setup_ui_models()
        
    def _setup_ui_models(self):
        """Setup models for UI components."""
        # Files section model
        self.files_model = QStandardItemModel()
        self.files_model.setColumnCount(3)
        self.files_model.setHorizontalHeaderLabels(["Image", "Label", "Verified"])
        
        # Classes section model
        self.classes_model = QStandardItemModel()
        self.classes_model.setColumnCount(2)
        self.classes_model.setHorizontalHeaderLabels(["ID", "Class Name"])
        
        # Connect models to views
        self.ui.listView_OpenedFiles.setModel(self.files_model)
        self.ui.listView_Classes_ViewYamlClasses.setModel(self.classes_model)
        
    def _initialize_controllers(self):
        """Initialize controller objects."""
        self.ai_controller = AIController(self)
        self.file_controller = FileController(self)
        self.ui_controller = UIController(self)
        self.class_controller = ClassController(self)
        
        # Initialize shortcuts handler
        self.shortcuts_handler = ShortcutsHandler(self)
        
    def _setup_canvas(self):
        """Setup the canvas for image annotation."""
        self.canvas_layout = QVBoxLayout()
        self.canvas_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create canvas widget
        self.canvas = Canvas()
        self.canvas.set_drawing_color(self.box_color)
        self.canvas_layout.addWidget(self.canvas)
        
        # Create container and replace graphics view
        self.canvas_container = QWidget()
        self.canvas_container.setLayout(self.canvas_layout)
        
        self._replace_graphics_view_with_canvas()
        self._connect_canvas_signals()
        
    def _replace_graphics_view_with_canvas(self):
        """Replace the QGraphicsView with our canvas container."""
        graphics_view = self.ui.graphicsView_RightPanel
        parent_widget = graphics_view.parent()
        parent_layout = parent_widget.layout()
        
        # Find and replace the graphics view
        for i in range(parent_layout.count()):
            if parent_layout.itemAt(i).widget() == graphics_view:
                graphics_view.setParent(None)
                parent_layout.insertWidget(i, self.canvas_container)
                break
                
    def _connect_canvas_signals(self):
        """Connect canvas signals to handlers."""
        self.canvas.newShape.connect(self.shape_complete)
        self.canvas.selectionChanged.connect(self.shape_selection_changed)
        self.canvas.shapeMoved.connect(self.shape_moved)
        self.canvas.zoomRequest.connect(self.ui_controller.update_zoom_level)
        
    def _connect_signals(self):
        """Connect UI signals to controller methods."""
        # Menu and toolbar connections
        self.ui.actionOpen_Images_Folder.triggered.connect(self.file_controller.open_images_folder)
        self.ui.actionOpen_Annotations_Folder.triggered.connect(self.file_controller.open_labels_folder)
        self.ui.actionExport_Annotations.triggered.connect(self.file_controller.export_annotations)
        self.ui.actionCreate_config_yaml.triggered.connect(self.file_controller.create_config_yaml)
        self.ui.actionshortcuts.triggered.connect(self.show_shortcuts)
        
        # Navigation and control buttons
        self.ui.pushButton_BottomWidget_Save.clicked.connect(self.save_current_annotations)
        self.ui.pushButton_BottomWidget_Next.clicked.connect(self.ui_controller.next_image)
        self.ui.pushButton_BottomWidget_Previos.clicked.connect(self.ui_controller.previous_image)
        self.ui.commandLinkButton_BottomWidget_VerifyFrame.clicked.connect(self.ui_controller.verify_image)
        self.ui.checkBox_BottomWidget_AutoSaveMode.stateChanged.connect(self.ui_controller.toggle_auto_save)
        
        # Visual settings
        self.ui.pushButton_BottomWidget_ChangeBoxColor.clicked.connect(self.ui_controller.change_box_color)
        self.ui.spinBox_BottomWidget_ChangeBorderWidth.valueChanged.connect(self.ui_controller.change_border_width)
        self.ui.commandLinkButton_BottomWidget_HideLabels.clicked.connect(self.ui_controller.toggle_hide_labels)
        
        # AI Mode connections
        self.ui.comboBox_AIModeGroupBox_ModelFamily.currentIndexChanged.connect(self.ai_controller.update_model_family)
        self.ui.pushButton_AIModeGroupBox_UploadModel.clicked.connect(self.ai_controller.upload_model)
        self.ui.pushButton_AIModeGroupBox_UploadModelYaml.clicked.connect(self.ai_controller.upload_model_yaml)
        self.ui.commandLinkButton_AIModeGroupBox_RunDetection.clicked.connect(self.ai_controller.run_ai_detection)
        
        # Classes connections
        self.ui.checkBox_Classes_UseDefaultClass.stateChanged.connect(self.class_controller.toggle_default_class)
        
        # File list interaction
        self.ui.listView_OpenedFiles.clicked.connect(self.file_controller.file_list_clicked)
        
        # Class assignment for selected shapes
        if hasattr(self.ui, 'comboBox_AIModeGroupBox_AssignToClass'):
            self.ui.comboBox_AIModeGroupBox_AssignToClass.currentIndexChanged.connect(self.ai_controller.assign_class_to_selected)
            
        self._setup_additional_ui_elements()
        
    def _setup_additional_ui_elements(self):
        """Setup additional UI elements like center button and class management."""
        # Add Center button
        self.center_button = QtWidgets.QPushButton("Center")
        self.center_button.setToolTip("Reset zoom to 100% and center image")
        self.center_button.clicked.connect(self.ui_controller.center_image)
        self.center_button.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; border-radius: 4px; padding: 4px 8px; } "
            "QPushButton:hover { background-color: #45a049; }"
        )
        
        # Add center button to zoom layout
        zoom_label = self.ui.label_BottomWidget_Zoom
        if zoom_label and zoom_label.parent():
            parent_layout = zoom_label.parent().layout()
            if parent_layout:
                for i in range(parent_layout.count()):
                    if parent_layout.itemAt(i).widget() == zoom_label:
                        parent_layout.insertWidget(i + 1, self.center_button)
                        break
                        
        # Setup class management UI
        self._setup_class_management_ui()
        
    def _setup_class_management_ui(self):
        """Setup class management UI elements."""
        # Change button text and connect to class controller
        self.ui.pushButton_Classes_OpenCurrentDatasetYaml.setText("Open Current Dataset classes.txt")
        self.ui.pushButton_Classes_OpenCurrentDatasetYaml.clicked.connect(self.class_controller.open_classes_txt)
        
        # Create Add Class button
        self.add_class_button = QtWidgets.QPushButton("Add New Class")
        self.add_class_button.setToolTip("Add a new class to the classes.txt file")
        self.add_class_button.clicked.connect(self.class_controller.add_class_to_dataset)
        
        # Add button to classes layout
        classes_view = self.ui.listView_Classes_ViewYamlClasses
        if classes_view and classes_view.parent():
            parent_layout = classes_view.parent().layout()
            if parent_layout:
                list_view_index = parent_layout.indexOf(classes_view)
                if list_view_index >= 0:
                    parent_layout.insertWidget(list_view_index + 1, self.add_class_button)
                    
        # Hide unused UI elements
        self._hide_unused_ui_elements()
        
    def _hide_unused_ui_elements(self):
        """Hide UI elements that are not needed in the refactored version."""
        unused_elements = [
            'pushButton_Classes_AddClass',
            'plainTextEdit_Classes_AddClass',
            'splitter_Classes_AddClass'
        ]
        
        for element_name in unused_elements:
            if hasattr(self.ui, element_name):
                getattr(self.ui, element_name).setVisible(False)
                
    def _initialize_event_handling(self):
        """Initialize event handling."""
        self.installEventFilter(self)
        
    # Event handlers
    def eventFilter(self, obj, event):
        """Event filter to track key states."""
        if event.type() == QEvent.KeyPress:
            self.key_states[event.key()] = True
        elif event.type() == QEvent.KeyRelease:
            self.key_states[event.key()] = False
        
        return super().eventFilter(obj, event)
    
    def is_key_pressed(self, key):
        """Check if a key is currently pressed."""
        return self.key_states.get(key, False)

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts."""
        self.shortcuts_handler.handle_key_press(event)
        
    def keyReleaseEvent(self, event):
        """Handle keyboard shortcut releases."""
        self.shortcuts_handler.handle_key_release(event)
        
    # Canvas event handlers
    def shape_complete(self):
        """Called when a new shape is created."""
        # Set default class if enabled
        selected_class = None
        if self.ui.checkBox_Classes_UseDefaultClass.isChecked() and hasattr(self.ui, 'comboBox_Classes_UseDefaultClass'):
            selected_class = self.ui.comboBox_Classes_UseDefaultClass.currentText()
            if selected_class and ":" in selected_class:
                selected_class = selected_class.split(":", 1)[1].strip()
            
        # Set label for the last created shape
        shapes = self.canvas.shapes
        if shapes and shapes[-1].label is None:
            default_class = selected_class or (self.dataset.classes[0] if self.dataset.classes else "")
            shapes[-1].label = default_class
    
    def shape_selection_changed(self, selected):
        """Handle shape selection change."""
        if selected and self.canvas.selected_shape:
            shape = self.canvas.selected_shape
            if shape and shape.label:
                # Update AI Mode combobox
                if hasattr(self.ui, 'comboBox_AIModeGroupBox_AssignToClass'):
                    index = self.ui.comboBox_AIModeGroupBox_AssignToClass.findText(shape.label, Qt.MatchContains)
                    if index >= 0:
                        self.ui.comboBox_AIModeGroupBox_AssignToClass.setCurrentIndex(index)
                
                # Update current class label
                if hasattr(self.ui, 'label_BottomWidget_CurrentClass'):
                    self.ui.label_BottomWidget_CurrentClass.setText(shape.label)
        elif not selected or not self.canvas.selected_shapes:
            if hasattr(self.ui, 'label_BottomWidget_CurrentClass'):
                self.ui.label_BottomWidget_CurrentClass.setText("")
    
    def shape_moved(self):
        """Handle shape moved event."""
        pass  # Canvas handles the visual updates
        
    def update_status_bar(self, pos, width=None, height=None):
        """Update status bar with coordinates and dimensions."""
        if width is not None and height is not None:
            status = f"X: {int(pos.x())}, Y: {int(pos.y())}, Width: {int(width)}, Height: {int(height)}"
        else:
            status = f"X: {int(pos.x())}, Y: {int(pos.y())}"
        
        self.statusBar().showMessage(status)
        
    # Image loading and navigation
    def load_current_image(self):
        """Load current image and its annotations."""
        if 0 <= self.current_image_index < self.dataset.get_image_count():
            image_path = self.dataset.get_current_image_path(self.current_image_index)
            annotations = self.dataset.get_annotations_for_image(self.current_image_index)
            
            # Update window title
            image_name = os.path.basename(image_path)
            self.setWindowTitle(f"Nexus Tag - {image_name}")
            
            # Load the image
            pixmap = QtGui.QPixmap(image_path)
            if not pixmap.isNull():
                # Reset zoom level for new images
                self.zoom_level = 100
                self.ui.label_BottomWidget_Zoom.setText(f"{self.zoom_level}%")
                self.canvas.zoom_level = 100
                self.canvas.scale = 1.0
                
                # Load pixmap and annotations
                self.canvas.load_pixmap(pixmap)
                
                if annotations and 'boxes' in annotations and 'classes' in annotations:
                    self.load_shapes_from_annotations(annotations)
                    self.class_controller.update_classes_for_current_image()
                
                # Update zoom display
                self.zoom_level = self.canvas.zoom_level
                self.ui.label_BottomWidget_Zoom.setText(f"{self.zoom_level}%")
            
            # Update verification status
            self.is_verified = self.dataset.is_image_verified(self.current_image_index)
            self.ui_controller.update_verification_ui()
            
            # Reset to edit mode
            self.canvas.set_editing(True)
            self.is_drawing = False
            
    def load_shapes_from_annotations(self, annotations):
        """Convert annotations to shapes and load them into the canvas."""
        boxes = annotations.get('boxes', [])
        classes = annotations.get('classes', [])
        img_width = self.canvas.pixmap.width()
        img_height = self.canvas.pixmap.height()
        
        shapes = []
        for box, class_id in zip(boxes, classes):
            # Convert class_id to class name if possible
            try:
                class_idx = int(class_id)
                if 0 <= class_idx < len(self.dataset.classes):
                    class_name = self.dataset.classes[class_idx]
                else:
                    class_name = str(class_id)
            except (ValueError, TypeError):
                class_name = str(class_id)
                
            shape = Shape(label=class_name)
            shape.paint_label = not self.hide_labels
            shape.from_normalized_rect(box, img_width, img_height)
            shapes.append(shape)
            
        self.canvas.load_shapes(shapes)
        
    # Data management
    def save_current_annotations(self):
        """Save the current annotations to the dataset."""
        if self.current_image_index >= 0:
            # Convert shapes to normalized rectangles
            rect_data = self.canvas.shapes_to_normalized_rects()
            
            # Create annotations dict
            annotations = {
                'boxes': [item['rect'] for item in rect_data],
                'classes': [item['label'] for item in rect_data]
            }
            
            # Save to dataset
            self.dataset.save_annotations_for_image(self.current_image_index, annotations)
            
            # Show status message
            self.statusBar().showMessage("Annotations saved successfully", 3000)
            
            # Update file list
            if hasattr(self, 'files_model'):
                self.file_controller.update_file_list_item(self.current_image_index)
                
    # UI helper methods
    def update_classes_list(self, classes):
        """Update classes ListView and ComboBoxes."""
        self.class_controller.update_classes_list(classes)
        
    def update_classes_for_current_image(self):
        """Update the classes list with classes used in the current image."""
        self.class_controller.update_classes_for_current_image()
        
    def populate_file_list(self):
        """Populate file list with images and corresponding labels."""
        self.file_controller.populate_file_list()
        
    # Dialog methods
    def show_shortcuts(self):
        """Show shortcuts info dialog."""
        dialog = ShortcutsInfoDialog(self)
        dialog.exec_()
        
    def closeEvent(self, event):
        """Handle application close event."""
        if self.dataset.get_unsaved_count() > 0:
            reply = QtWidgets.QMessageBox.question(
                self, 'Unsaved Changes', 
                f"You have {self.dataset.get_unsaved_count()} unsaved annotations. Save before closing?",
                QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.Discard | QtWidgets.QMessageBox.Cancel,
                QtWidgets.QMessageBox.Save)
            
            if reply == QtWidgets.QMessageBox.Save:
                self.dataset.save_all_annotations()
                event.accept()
            elif reply == QtWidgets.QMessageBox.Cancel:
                event.ignore()
            else:
                event.accept()
        else:
            event.accept()
            
    # Navigation methods (delegated to UI controller)
    def next_image(self):
        """Go to next image."""
        self.ui_controller.next_image()
        
    def previous_image(self):
        """Go to previous image."""
        self.ui_controller.previous_image()
        
    def zoom_in(self):
        """Zoom in."""
        self.ui_controller.zoom_in()
        
    def zoom_out(self):
        """Zoom out."""
        self.ui_controller.zoom_out()
        
    def verify_image(self):
        """Toggle image verification."""
        self.ui_controller.verify_image()
        
    # AI detection methods (delegated to AI controller)
    def run_detection_on_current(self):
        """Run detection on current image."""
        self.ai_controller.run_detection_on_current()
        
    # File management methods (delegated to ui controller)
    def delete_current_image(self):
        """Delete current image."""
        self.ui_controller.delete_current_image()

    def toggle_draw_mode(self):
        """Toggle between draw and edit modes."""
        if self.is_drawing:
            self.is_drawing = False
            self.canvas.set_editing(True)
        else:
            self.is_drawing = True
            self.canvas.set_editing(False)
