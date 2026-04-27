from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QLabel, QHeaderView
)
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QFont

class ShortcutsInfoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Keyboard Shortcuts")
        self.setMinimumSize(400, 500)
        
        # Make the dialog movable but without a title bar
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        
        # Store the position where the mouse is pressed
        self.drag_position = None
        
        self._init_ui()
        
    def _init_ui(self):
        layout = QVBoxLayout()
        
        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("Keyboard Shortcuts")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        close_button = QPushButton("✕")  # X symbol
        close_button.setMaximumSize(30, 30)
        close_button.clicked.connect(self.close)
        header_layout.addWidget(close_button)
        
        layout.addLayout(header_layout)
        
        # Shortcuts table
        shortcuts_table = QTableWidget()
        shortcuts_table.setColumnCount(2)
        shortcuts_table.setHorizontalHeaderLabels(["Shortcut", "Description"])
        shortcuts_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        
        # Add shortcuts data
        shortcuts = [
            ("s", "Save annotations for current image"),
            ("Space", "Verify image (toggle)"),
            ("w", "Start/stop drawing box"),
            ("d", "Next image"),
            ("a", "Previous image"),
            ("z", "Zoom in at mouse position"),
            ("x", "Zoom out at mouse position"),
            ("q", "Delete selected box(es)"),
            ("e", "Set class for selected box (opens class selector)"),
            ("Shift", "Select all boxes"),
            ("c (hold)", "Hover selection: move mouse over boxes to select them"),
            ("v (hold)", "Hover deselection: move mouse over selected boxes to deselect"),
            ("r", "Run detection on current image"),
            ("Ctrl+z", "Undo last action"),
            ("Ctrl+Shift+d", "Delete current image (with confirmation)"),
            ("ESC", "Show/hide shortcuts info")
        ]
        
        # Populate table
        shortcuts_table.setRowCount(len(shortcuts))
        
        for i, (shortcut, description) in enumerate(shortcuts):
            shortcut_item = QTableWidgetItem(shortcut)
            description_item = QTableWidgetItem(description)
            
            shortcuts_table.setItem(i, 0, shortcut_item)
            shortcuts_table.setItem(i, 1, description_item)
            
        layout.addWidget(shortcuts_table)
        
        self.setLayout(layout)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.drag_position:
            self.move(event.globalPos() - self.drag_position)
            
    def mouseReleaseEvent(self, event):
        self.drag_position = None 