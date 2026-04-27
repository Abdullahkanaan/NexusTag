from PyQt5.QtGui import QImage, QPixmap, QPainter, QColor, QPen
from PyQt5.QtCore import QPointF, QRectF

class Annotation:
    def __init__(self):
        self.image_path = None
        self.image = None
        self.pixmap = None
        self.boxes = []
        self.classes = []
        self.default_class = None
        self.current_box = None
        self.start_point = None
        self.end_point = None
        self.box_color = QColor(0, 255, 0)  # Default green
        self.border_width = 2
        self.hide_labels = False
        self.selected_boxes = set()
        
    def set_image(self, image_path):
        """Set the current image for annotation."""
        self.image_path = image_path
        self.image = QImage(image_path)
        self.pixmap = QPixmap.fromImage(self.image)
        
    def set_annotations(self, annotations):
        """Set existing annotations for the image."""
        if annotations:
            self.boxes = annotations.get('boxes', [])
            self.classes = annotations.get('classes', [])
        else:
            self.boxes = []
            self.classes = []
        
    def get_annotations(self):
        """Get all annotations for the current image."""
        return {
            'boxes': self.boxes,
            'classes': self.classes
        }
        
    def set_default_class(self, class_name):
        """Set default class for new bounding boxes."""
        self.default_class = class_name
        
    def start_box(self, point):
        """Start drawing a new bounding box."""
        self.start_point = point
        self.end_point = point
        self.current_box = True
        print(f"Kutu çizme başladı: {point.x()}, {point.y()}")
        
    def update_box(self, point):
        """Update the current box with new endpoint."""
        if self.current_box:
            self.end_point = point
            print(f"Kutu güncellendi: {self.start_point.x()}, {self.start_point.y()} -> {point.x()}, {point.y()}")
            
    def finalize_box(self, point=None):
        """Complete the box and add it to annotations."""
        if self.current_box and self.start_point:
            # Eğer point parametresi verildiyse, end_point'i güncelle
            if point:
                self.end_point = point
                
            # Ensure start_point is top-left and end_point is bottom-right
            x1 = min(self.start_point.x(), self.end_point.x())
            y1 = min(self.start_point.y(), self.end_point.y())
            x2 = max(self.start_point.x(), self.end_point.x())
            y2 = max(self.start_point.y(), self.end_point.y())
            
            # Ensure box has minimum size
            if x2 - x1 > 5 and y2 - y1 > 5:
                # Normalize coordinates (0-1 range)
                img_width = self.pixmap.width()
                img_height = self.pixmap.height()
                
                norm_box = [
                    x1 / img_width,
                    y1 / img_height,
                    (x2 - x1) / img_width,
                    (y2 - y1) / img_height
                ]
                
                self.boxes.append(norm_box)
                
                # Assign default class if available, otherwise use '0' as default
                class_idx = self.default_class or '0'
                self.classes.append(class_idx)
                
                print(f"Kutu kaydedildi: {norm_box}, sınıf: {class_idx}")
                
            # Reset current box
            self.current_box = False
            self.start_point = None
            self.end_point = None
            
    def add_detections(self, detections):
        """Add AI-detected objects to annotations."""
        if detections:
            new_boxes = detections.get('boxes', [])
            new_classes = detections.get('classes', [])
            
            self.boxes.extend(new_boxes)
            self.classes.extend(new_classes)
            
    def set_box_color(self, color):
        """Set color for bounding boxes."""
        self.box_color = color
        
    def set_border_width(self, width):
        """Set border width for bounding boxes."""
        self.border_width = width
        
    def set_hide_labels(self, hide):
        """Set whether to hide labels."""
        self.hide_labels = hide
        
    def toggle_box_selection(self, index):
        """Toggle selection state for a box."""
        if index in self.selected_boxes:
            self.selected_boxes.remove(index)
        else:
            self.selected_boxes.add(index)
            
    def select_all_boxes(self):
        """Select all boxes."""
        self.selected_boxes = set(range(len(self.boxes)))
        
    def deselect_all_boxes(self):
        """Deselect all boxes."""
        self.selected_boxes = set()
        
    def delete_selected_boxes(self):
        """Delete all selected boxes."""
        if not self.selected_boxes:
            return
            
        # Sort indices in reverse to avoid index shifting during deletion
        indices = sorted(list(self.selected_boxes), reverse=True)
        
        for idx in indices:
            if 0 <= idx < len(self.boxes):
                self.boxes.pop(idx)
                self.classes.pop(idx)
                
        self.selected_boxes = set()
        
    def set_class_for_selected(self, class_idx):
        """Set class for selected boxes."""
        for idx in self.selected_boxes:
            if 0 <= idx < len(self.classes):
                self.classes[idx] = class_idx
                
    def draw_annotations(self, painter, scale_factor=1.0):
        """Draw all bounding boxes and labels."""
        if not self.pixmap:
            return
            
        img_width = self.pixmap.width()
        img_height = self.pixmap.height()
        
        # Draw existing boxes
        for idx, (box, class_idx) in enumerate(zip(self.boxes, self.classes)):
            # Denormalize coordinates to pixel values
            x = box[0] * img_width
            y = box[1] * img_height
            w = box[2] * img_width
            h = box[3] * img_height
            
            # Adjust for zoom level
            x *= scale_factor
            y *= scale_factor
            w *= scale_factor
            h *= scale_factor
            
            # Set pen for selected/unselected boxes
            if idx in self.selected_boxes:
                pen = QPen(QColor(255, 0, 0), self.border_width)  # Red for selected
            else:
                pen = QPen(self.box_color, self.border_width)
                
            painter.setPen(pen)
            painter.drawRect(QRectF(x, y, w, h))
            
            # Draw label if not hidden
            if not self.hide_labels:
                label = f"Class: {class_idx}"
                painter.drawText(QPointF(x, y - 5), label)
                
        # Draw current box being created
        if self.current_box and self.start_point and self.end_point:
            x1 = min(self.start_point.x(), self.end_point.x()) * scale_factor
            y1 = min(self.start_point.y(), self.end_point.y()) * scale_factor
            w = abs(self.end_point.x() - self.start_point.x()) * scale_factor
            h = abs(self.end_point.y() - self.start_point.y()) * scale_factor
            
            painter.setPen(QPen(self.box_color, self.border_width))
            painter.drawRect(QRectF(x1, y1, w, h))
            
    def get_box_at_position(self, pos, scale_factor=1.0):
        """Get index of box at given position."""
        if not self.pixmap:
            return -1
            
        img_width = self.pixmap.width()
        img_height = self.pixmap.height()
        
        # Check each box if it contains the position
        for idx, box in enumerate(self.boxes):
            # Denormalize coordinates to pixel values
            x = box[0] * img_width * scale_factor
            y = box[1] * img_height * scale_factor
            w = box[2] * img_width * scale_factor
            h = box[3] * img_height * scale_factor
            
            rect = QRectF(x, y, w, h)
            
            if rect.contains(pos):
                return idx
                
        return -1
        
    def clear(self):
        """Clear all annotations."""
        self.boxes = []
        self.classes = []
        self.selected_boxes = set() 