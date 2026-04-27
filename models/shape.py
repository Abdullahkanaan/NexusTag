#!/usr/bin/python
# -*- coding: utf-8 -*-

from PyQt5.QtGui import QColor, QPainterPath
from PyQt5.QtCore import QPointF

# Default colors for shapes
DEFAULT_LINE_COLOR = QColor(0, 0, 255, 128)  # Blue with transparency
DEFAULT_FILL_COLOR = QColor(0, 0, 255, 30)   # Light blue with high transparency
DEFAULT_SELECT_LINE_COLOR = QColor(255, 255, 255)  # White
DEFAULT_SELECT_FILL_COLOR = QColor(0, 128, 255, 155)  # Light blue
DEFAULT_VERTEX_FILL_COLOR = QColor(0, 255, 0, 255)  # Green
DEFAULT_HVERTEX_FILL_COLOR = QColor(255, 0, 0)  # Red

def distance(p1, p2):
    """Calculate the distance between two points."""
    return ((p1.x() - p2.x()) ** 2 + (p1.y() - p2.y()) ** 2) ** 0.5

class Shape:
    """Shape class represents a bounding box with label and other attributes."""
    
    P_SQUARE, P_ROUND = range(2)  # Vertex shape style
    MOVE_VERTEX, NEAR_VERTEX = range(2)  # Vertex highlight mode
    
    # Class-level style variables (affect all instances)
    line_color = DEFAULT_LINE_COLOR
    fill_color = DEFAULT_FILL_COLOR
    select_line_color = DEFAULT_SELECT_LINE_COLOR
    select_fill_color = DEFAULT_SELECT_FILL_COLOR
    vertex_fill_color = DEFAULT_VERTEX_FILL_COLOR
    h_vertex_fill_color = DEFAULT_HVERTEX_FILL_COLOR
    point_type = P_ROUND
    point_size = 8
    line_width = 2  # Default line width
    scale = 1.0
    label_font_size = 8

    def __init__(self, label=None, line_color=None, difficult=False, paint_label=True):
        self.label = label
        self.points = []  # List of QPointF
        self.fill = True  # Enable fill by default
        self.selected = False
        self.difficult = difficult
        self.paint_label = paint_label
        self._closed = False
        
        # Highlight state
        self._highlight_index = None
        self._highlight_mode = self.NEAR_VERTEX
        self._highlight_settings = {
            self.NEAR_VERTEX: (4, self.P_ROUND),
            self.MOVE_VERTEX: (1.5, self.P_SQUARE),
        }
        
        # Override the class line_color if specified
        if line_color is not None:
            self.line_color = line_color
            # Also create matching fill color with more transparency
            self.fill_color = QColor(line_color)
            self.fill_color.setAlpha(30)  # Make it more transparent

    def close(self):
        """Close the shape (rectangle is complete)."""
        self._closed = True

    def add_point(self, point):
        """Add a point to the shape."""
        if len(self.points) < 4:  # For rectangle, only need 4 points (or 2 for opposite corners)
            self.points.append(point)

    def pop_point(self):
        """Remove and return the last point."""
        if self.points:
            return self.points.pop()
        return None

    def is_closed(self):
        """Check if the shape is closed."""
        return self._closed

    def set_open(self):
        """Set the shape as open (not yet complete)."""
        self._closed = False
        
    def reach_max_points(self):
        """Check if shape has reached maximum number of points."""
        if len(self.points) >= 4:
            return True
        return False

    def paint(self, painter):
        """Paint the shape on the canvas."""
        if not self.points:
            return
            
        # Set the color based on selection state
        color = self.select_line_color if self.selected else self.line_color
        pen = painter.pen()
        pen.setColor(color)
        # Use the class-wide line_width property for consistent border width
        pen.setWidth(max(1, int(round(self.line_width / self.scale))))
        painter.setPen(pen)
        
        # Create paths for lines and vertices
        line_path = QPainterPath()
        vertex_path = QPainterPath()
        
        # For a rectangle, create a proper closed shape even during drawing
        if len(self.points) == 2:
            # When dragging with two points, we create a rectangle
            p1 = self.points[0]
            p2 = self.points[1]
            
            # Create a rectangular path
            line_path.moveTo(p1.x(), p1.y())
            line_path.lineTo(p2.x(), p1.y())
            line_path.lineTo(p2.x(), p2.y())
            line_path.lineTo(p1.x(), p2.y())
            line_path.closeSubpath()
            
            # Draw vertices at the corners
            for i, p in enumerate([
                QPointF(p1.x(), p1.y()),  # top-left
                QPointF(p2.x(), p1.y()),  # top-right
                QPointF(p2.x(), p2.y()),  # bottom-right
                QPointF(p1.x(), p2.y())   # bottom-left
            ]):
                vertex_path.addEllipse(p, self.point_size / self.scale / 2.0, 
                                  self.point_size / self.scale / 2.0)
        else:
            # Normal drawing for other cases (completed shapes)
            # Start drawing from the first point
            if self.points:
                line_path.moveTo(self.points[0])
                
            # Draw each point and connecting lines
            for i, p in enumerate(self.points):
                line_path.lineTo(p)
                self.draw_vertex(vertex_path, i)
                
            # Close the shape if it's marked as closed
            if self.is_closed() and len(self.points) > 2:
                line_path.lineTo(self.points[0])
        
        # Fill the shape whether it's complete or being drawn
        color = self.select_fill_color if self.selected else self.fill_color
        if self.fill:
            painter.fillPath(line_path, color)
            
        # Draw the outline and vertices
        painter.drawPath(line_path)
        painter.drawPath(vertex_path)
        painter.fillPath(vertex_path, self.vertex_fill_color)
        
        # Draw the label text
        if self.paint_label and self.label and len(self.points) >= 2:
            min_x = min(p.x() for p in self.points)
            min_y = min(p.y() for p in self.points)
            font = painter.font()
            font.setPointSize(self.label_font_size)
            font.setBold(True)
            painter.setFont(font)
            
            # Draw label slightly above the top-left corner
            painter.drawText(int(min_x), int(min_y - 5), self.label)

    def draw_vertex(self, path, i):
        """Draw a vertex at the given index."""
        d = self.point_size / self.scale
        shape = self.point_type
        point = self.points[i]
        
        # Adjust size and shape for highlighted vertex
        if i == self._highlight_index:
            size, shape = self._highlight_settings[self._highlight_mode]
            d *= size
            
        # Set color based on highlight state
        if self._highlight_index is not None:
            vertex_fill_color = self.h_vertex_fill_color
        else:
            vertex_fill_color = self.vertex_fill_color
            
        # Draw square or round vertex
        if shape == self.P_SQUARE:
            path.addRect(point.x() - d / 2, point.y() - d / 2, d, d)
        elif shape == self.P_ROUND:
            path.addEllipse(point, d / 2.0, d / 2.0)

    def nearest_vertex(self, point, epsilon):
        """Find the nearest vertex to given point within epsilon distance."""
        min_distance = float('inf')
        vertex_index = None
        
        for i, p in enumerate(self.points):
            dist = distance(p, point)
            if dist <= epsilon and dist < min_distance:
                min_distance = dist
                vertex_index = i
                
        return vertex_index

    def contains_point(self, point):
        """Check if shape contains the given point."""
        return self.make_path().contains(point)

    def make_path(self):
        """Create a painter path from the shape points."""
        if len(self.points) < 2:
            return QPainterPath()
            
        path = QPainterPath(self.points[0])
        for p in self.points[1:]:
            path.lineTo(p)
            
        # Close the path if shape is closed
        if self.is_closed():
            path.closeSubpath()
            
        return path

    def bounding_rect(self):
        """Get the bounding rectangle of the shape."""
        return self.make_path().boundingRect()

    def move_by(self, offset):
        """Move the entire shape by the given offset."""
        self.points = [p + offset for p in self.points]

    def move_vertex_by(self, index, offset):
        """Move a specific vertex by the given offset."""
        if 0 <= index < len(self.points):
            self.points[index] = self.points[index] + offset

    def highlight_vertex(self, index, action):
        """Highlight a vertex with the specified action."""
        self._highlight_index = index
        self._highlight_mode = action

    def highlight_clear(self):
        """Clear vertex highlighting."""
        self._highlight_index = None

    def copy(self):
        """Create a copy of this shape."""
        shape = Shape(self.label)
        shape.points = [QPointF(p) for p in self.points]
        shape.fill = self.fill
        shape.selected = self.selected
        shape._closed = self._closed
        shape.difficult = self.difficult
        shape.paint_label = self.paint_label
        
        # Copy custom colors if set
        if self.line_color != Shape.line_color:
            shape.line_color = QColor(self.line_color)
        if self.fill_color != Shape.fill_color:
            shape.fill_color = QColor(self.fill_color)
            
        return shape
        
    def to_normalized_rect(self, image_width, image_height):
        """Convert shape to normalized rectangle coordinates [x, y, width, height]."""
        if len(self.points) < 4:
            return [0, 0, 0, 0]
            
        # For rectangles, we should just use the min/max coordinates
        min_x = min(p.x() for p in self.points)
        min_y = min(p.y() for p in self.points)
        max_x = max(p.x() for p in self.points)
        max_y = max(p.y() for p in self.points)
        
        # Normalize coordinates
        x = max(0, min_x) / image_width
        y = max(0, min_y) / image_height
        w = min(image_width, max_x - min_x) / image_width
        h = min(image_height, max_y - min_y) / image_height
        
        return [x, y, w, h]
        
    def from_normalized_rect(self, rect, img_width, img_height):
        """Create shape from normalized rectangle coordinates [x, y, width, height]."""
        # Ensure we have valid dimensions to prevent division by zero
        if img_width <= 0 or img_height <= 0:
            print(f"Invalid image dimensions: {img_width}x{img_height}")
            return
            
        if len(rect) != 4:
            print(f"Invalid rectangle format. Expected [x, y, width, height], got {rect}")
            return
            
        # Extract normalized coordinates
        x, y, width, height = rect
        
        # Convert from normalized coordinates to pixel coordinates
        x_pixels = x * img_width
        y_pixels = y * img_height
        width_pixels = width * img_width
        height_pixels = height * img_height
        
        # Ensure values are within image bounds
        x_pixels = max(0, min(x_pixels, img_width - 1))
        y_pixels = max(0, min(y_pixels, img_height - 1))
        width_pixels = min(width_pixels, img_width - x_pixels)
        height_pixels = min(height_pixels, img_height - y_pixels)
        
        # Create points for rectangle corners (in clockwise order)
        self.points = [
            QPointF(x_pixels, y_pixels),                         # Top-left
            QPointF(x_pixels + width_pixels, y_pixels),          # Top-right
            QPointF(x_pixels + width_pixels, y_pixels + height_pixels),  # Bottom-right
            QPointF(x_pixels, y_pixels + height_pixels)          # Bottom-left
        ]
        
        print(f"Created shape with points: {self.points}")
        self.close()
        
    def ensure_rectangle(self):
        """Ensure the shape is a proper rectangle with perpendicular sides."""
        if len(self.points) != 4:
            return
            
        # Find the bounding box
        min_x = min(p.x() for p in self.points)
        min_y = min(p.y() for p in self.points)
        max_x = max(p.x() for p in self.points)
        max_y = max(p.y() for p in self.points)
        
        # Update points to form a rectangle
        self.points[0] = QPointF(min_x, min_y)  # top-left
        self.points[1] = QPointF(max_x, min_y)  # top-right 
        self.points[2] = QPointF(max_x, max_y)  # bottom-right
        self.points[3] = QPointF(min_x, max_y)  # bottom-left

    def __len__(self):
        return len(self.points)
        
    def __getitem__(self, key):
        return self.points[key]
        
    def __setitem__(self, key, value):
        self.points[key] = value 