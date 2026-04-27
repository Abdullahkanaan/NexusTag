from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, 
    QRadioButton, QPushButton, QFileDialog, QLabel
)
from PyQt5.QtCore import Qt

class ExportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Export Annotations")
        self.setMinimumWidth(400)
        
        self.format_type = "YOLO"  # Default format
        self.export_directory = ""
        
        self._init_ui()
        
    def _init_ui(self):
        layout = QVBoxLayout()
        
        # Format selection group
        format_group = QGroupBox("Export Format (select one):")
        format_layout = QVBoxLayout()
        
        # Format radio buttons
        self.yolo_radio = QRadioButton("YOLO")
        self.yolo_radio.setChecked(True)  # Default selection
        self.yolo_radio.toggled.connect(lambda: self._format_selected("YOLO"))
        
        self.createml_radio = QRadioButton("CreateML")
        self.createml_radio.toggled.connect(lambda: self._format_selected("CreateML"))
        
        self.pascal_radio = QRadioButton("Pascal/VOC")
        self.pascal_radio.toggled.connect(lambda: self._format_selected("Pascal/VOC"))
        
        # Add radio buttons to layout
        format_layout.addWidget(self.yolo_radio)
        format_layout.addWidget(self.createml_radio)
        format_layout.addWidget(self.pascal_radio)
        
        format_group.setLayout(format_layout)
        layout.addWidget(format_group)
        
        # Directory selection
        dir_layout = QHBoxLayout()
        self.dir_label = QLabel("Export Directory:")
        self.dir_path_label = QLabel("Not selected")
        self.dir_path_label.setStyleSheet("color: gray;")
        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self._browse_directory)
        
        dir_layout.addWidget(self.dir_label)
        dir_layout.addWidget(self.dir_path_label, 1)  # Stretch factor 1
        dir_layout.addWidget(self.browse_button)
        
        layout.addLayout(dir_layout)
        
        # Dialog buttons
        button_layout = QHBoxLayout()
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        self.export_button = QPushButton("Export")
        self.export_button.clicked.connect(self.accept)
        self.export_button.setDefault(True)
        self.export_button.setEnabled(False)  # Disabled until directory is selected
        
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.export_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def _format_selected(self, format_type):
        self.format_type = format_type
        
    def _browse_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Export Directory")
        if directory:
            self.export_directory = directory
            # Show ellipsis in the middle if the path is too long
            if len(directory) > 30:
                display_path = directory[:14] + "..." + directory[-14:]
            else:
                display_path = directory
                
            self.dir_path_label.setText(display_path)
            self.dir_path_label.setStyleSheet("color: black;")
            self.export_button.setEnabled(True)
            
    def get_selected_format(self):
        return self.format_type
        
    def get_export_directory(self):
        return self.export_directory 