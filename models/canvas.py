"""
Canvas Widget - Optimized and cleaned version
Handles image display and shape interaction without duplicated code.
"""

from PyQt5.QtGui import QPainter, QPen, QColor, QPixmap
from PyQt5.QtCore import QPointF, Qt, pyqtSignal, QRectF
from PyQt5.QtWidgets import QWidget, QApplication

from models.shape import Shape, distance

# Cursor types
CURSOR_DEFAULT = Qt.ArrowCursor
CURSOR_POINT = Qt.PointingHandCursor
CURSOR_DRAW = Qt.CrossCursor
CURSOR_MOVE = Qt.ClosedHandCursor
CURSOR_GRAB = Qt.OpenHandCursor


class Canvas(QWidget):
    """Canvas widget for displaying and interacting with the image and shapes."""
    
    # Signals
    zoomRequest = pyqtSignal(int)
    scrollRequest = pyqtSignal(int, int)
    newShape = pyqtSignal()
    selectionChanged = pyqtSignal(bool)
    shapeMoved = pyqtSignal()
    drawingPolygon = pyqtSignal(bool)
    
    # Modes
    CREATE, EDIT = range(2)
    
    # Distance tolerance for selecting points
    epsilon = 24.0
    
    def __init__(self, *args, **kwargs):
        super(Canvas, self).__init__(*args, **kwargs)
        
        # Initialize state variables
        self.mode = self.EDIT
        self.shapes = []
        self.current = None         # Current shape being drawn
        self.selected_shape = None  # Keep for backwards compatibility
        self.selected_shapes = []   # New list to track multiple selections
        self.selected_shape_copy = None
        self.drawing_line_color = QColor(0, 255, 0)  # Default green
        self.drawing_rect_color = QColor(0, 0, 255)
        self.line = Shape(line_color=self.drawing_line_color)
        self.prev_point = QPointF()
        self.offsets = QPointF(), QPointF()
        self.scale = 1.0
        self.pixmap = QPixmap()
        self.visible = {}
        self._hide_background = False
        self.hide_background = False
        self.h_shape = None
        self.h_vertex = None
        self._painter = QPainter()
        self._cursor = CURSOR_DEFAULT
        self.draw_square = False
        self.paint_labels = True    # Whether to paint labels
        self.show_shapes = True     # Add this property to control shapes visibility
        self.modified = False       # Track if canvas has unsaved changes
        self.shape_history = []     # Undo stack: list of shape list snapshots

        # For zooming
        self.zoom_level = 100  # Percentage zoom level
        self.offset_to_center = QPointF()  # Offset to center the pixmap
        self.last_mouse_pos = QPointF()  # Last mouse position for zooming
        
        # Track key states directly in the canvas
        self.key_states = {}

        # Enable mouse tracking for hover effects
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.WheelFocus)
        
    def set_drawing_color(self, qcolor):
        """Set the color used for drawing shapes."""
        self.drawing_line_color = qcolor
        self.drawing_rect_color = qcolor
        
        # Also create matching fill color with more transparency
        fill_color = QColor(qcolor)
        fill_color.setAlpha(30)
        Shape.fill_color = fill_color
        
    # Event handlers
    def enterEvent(self, ev):
        """Handle mouse entering widget."""
        self.override_cursor(self._cursor)
        self.setFocus()
        
    def leaveEvent(self, ev):
        """Handle mouse leaving widget."""
        self.restore_cursor()
        
    def focusOutEvent(self, ev):
        """Handle widget losing focus."""
        self.restore_cursor()
        
    def keyPressEvent(self, ev):
        """Handle key press events directly in the canvas."""
        self.key_states[ev.key()] = True
        if ev.key() == Qt.Key_Shift:
            self.select_all_shapes()
            
        # Pass the event to the parent for handling
        if hasattr(self.parent(), 'keyPressEvent'):
            self.parent().keyPressEvent(ev)
        else:
            super().keyPressEvent(ev)
        
    def keyReleaseEvent(self, ev):
        """Handle key release events directly in the canvas."""
        self.key_states[ev.key()] = False
            
        # Pass the event to the parent for handling
        if hasattr(self.parent(), 'keyReleaseEvent'):
            self.parent().keyReleaseEvent(ev)
        else:
            super().keyReleaseEvent(ev)
            
    def wheelEvent(self, ev):
        """Handle mouse wheel events for zooming."""
        pos = ev.pos()
        self.last_mouse_pos = self.transform_pos(pos)
        
        # Determine zoom direction
        delta = ev.angleDelta()
        if delta.y() > 0:  # Wheel up = zoom in
            self.zoom_in(pos)
        else:  # Wheel down = zoom out
            self.zoom_out(pos)
        
        ev.accept()
        
    def resizeEvent(self, event):
        """Handle resize events to keep the pixmap centered."""
        super().resizeEvent(event)
        self.center_pixmap()
        
    # Mouse event handlers
    def mouseMoveEvent(self, ev):
        """Handle mouse move events."""
        pos = self.transform_pos(ev.pos())
        
        # Update cursor shape and show coordinates
        if hasattr(self.parent(), 'update_status_bar'):
            self.parent().update_status_bar(pos)
        
        # Check key states for hover selection
        is_c_pressed = self.key_states.get(Qt.Key_C, False)
        is_v_pressed = self.key_states.get(Qt.Key_V, False)
            
        # Draw mode - updating current shape while drawing
        if self.drawing():
            self.override_cursor(CURSOR_DRAW)
            if self.current:
                self.current.points[1] = pos
                self.repaint()
                
        # Edit mode - moving shapes or vertices
        elif self.editing():
            if self.selected_vertex():
                self.override_cursor(CURSOR_POINT)
                self.bounded_move_vertex(pos)
                self.shapeMoved.emit()
                self.repaint()
            elif self.selected_shapes and self.prev_point:
                self.override_cursor(CURSOR_GRAB)
                if self.selected_shape:
                    self.bounded_move_shape(self.selected_shape, pos)
                self.shapeMoved.emit()
                self.repaint()
            elif is_c_pressed:
                self._handle_hover_selection(pos)
            elif is_v_pressed:
                self._handle_hover_deselection(pos)
            else:
                self._handle_normal_hover(pos)
                
    def _handle_hover_selection(self, pos):
        """Handle hover selection when C key is pressed."""
        self.override_cursor(CURSOR_GRAB)
        for shape in reversed(self.shapes):
            if shape.contains_point(pos) and shape not in self.selected_shapes:
                self.select_shape(shape, add_to_selection=True)
                break
                
    def _handle_hover_deselection(self, pos):
        """Handle hover deselection when V key is pressed."""
        self.override_cursor(CURSOR_GRAB)
        for shape in self.selected_shapes.copy():
            if shape.contains_point(pos):
                self.de_select_shape(shape)
                break
                
    def _handle_normal_hover(self, pos):
        """Handle normal hover behavior."""
        for shape in reversed(self.shapes):
            if shape.contains_point(pos):
                self.override_cursor(CURSOR_GRAB)
                self.setToolTip("Click to select and drag shape")
                break
        else:
            self.override_cursor(CURSOR_DEFAULT)
            self.setToolTip("Click to select a shape")
        
    def mousePressEvent(self, ev):
        """Handle mouse press events."""
        pos = self.transform_pos(ev.pos())
        
        if ev.button() == Qt.LeftButton:
            if self.drawing():
                self._start_new_shape(pos)
            elif self.editing():
                self.select_shape_point(pos, ev.modifiers() & Qt.ShiftModifier)
                self.prev_point = pos
                self.repaint()
        elif ev.button() == Qt.RightButton and self.editing():
            self._handle_right_click(pos)
            
    def _start_new_shape(self, pos):
        """Start drawing a new shape."""
        if self.current is None:
            self.line = Shape(line_color=self.drawing_line_color)
            self.line.points = [pos, pos]
            self.current = self.line
            self.drawingPolygon.emit(True)
        self.update()
        
    def _handle_right_click(self, pos):
        """Handle right mouse click for deselection."""
        self.select_shape_point(pos, add_to_selection=False)
        if self.selected_shape:
            self.de_select_shape(self.selected_shape)
            self.update()
        
    def mouseReleaseEvent(self, ev):
        """Handle mouse release events."""
        if ev.button() == Qt.LeftButton and self.drawing():
            self._finish_drawing_shape(ev.pos())
        elif ev.button() == Qt.LeftButton and self.editing():
            self._finish_editing_operation()
            
    def _finish_drawing_shape(self, pos):
        """Finish drawing the current shape."""
        pos = self.transform_pos(pos)
        
        # Ensure position is within bounds
        if self.out_of_pixmap(pos):
            size = self.pixmap.size()
            pos = QPointF(
                min(max(0, pos.x()), size.width()),
                min(max(0, pos.y()), size.height())
            )
        
        if self.current and len(self.current.points) == 2:
            self._create_rectangle_from_points(pos)
        
        self.update()
        
    def _create_rectangle_from_points(self, end_pos):
        """Create a rectangle from start and end points."""
        p1 = self.current.points[0]
        p2 = end_pos
        
        # Ensure initial point is within boundaries
        if self.out_of_pixmap(p1):
            size = self.pixmap.size()
            p1 = QPointF(
                min(max(0, p1.x()), size.width()),
                min(max(0, p1.y()), size.height())
            )
            self.current.points[0] = p1
        
        # Calculate rectangle bounds
        x1, y1 = min(p1.x(), p2.x()), min(p1.y(), p2.y())
        x2, y2 = max(p1.x(), p2.x()), max(p1.y(), p2.y())
        
        # Ensure rectangle is within image boundaries
        size = self.pixmap.size()
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(size.width(), x2), min(size.height(), y2)
        
        # Only add if the rectangle has meaningful size
        if x2 - x1 > 1 and y2 - y1 > 1:
            self.current.points = [
                QPointF(x1, y1), QPointF(x2, y1),  # top-left, top-right
                QPointF(x2, y2), QPointF(x1, y2)   # bottom-right, bottom-left
            ]

            self.current.close()
            self.shape_history.append(self.shapes.copy())
            self.shapes.append(self.current)
            self.current = None
            self.newShape.emit()
        else:
            self.current = None
            
    def _finish_editing_operation(self):
        """Finish editing operations."""
        if self.selected_vertex():
            if self.h_shape and len(self.h_shape.points) == 4:
                self._ensure_rectangle(self.h_shape)
                
            self.h_shape.highlight_clear()
            self.h_vertex = None
            self.h_shape = None
            self.prev_point = QPointF()
        elif self.selected_shapes and self.prev_point:
            self.prev_point = QPointF()
            
    # Drawing and editing mode management
    def drawing(self):
        """Check if in drawing mode."""
        return self.mode == self.CREATE
        
    def editing(self):
        """Check if in editing mode."""
        return self.mode == self.EDIT
        
    def set_editing(self, value=True):
        """Set the editing mode."""
        self.mode = self.EDIT if value else self.CREATE
        if not value:  # Create mode - clear selections
            self.un_highlight()
            self.de_select_shape()
        self.prev_point = QPointF()
        self.repaint()
        
    # Shape management
    def select_shape(self, shape, add_to_selection=False):
        """Select a shape, optionally adding to existing selection."""
        if not add_to_selection:
            self.de_select_all_shapes()
        
        if shape not in self.selected_shapes:
            shape.selected = True
            self.selected_shapes.append(shape)
            self.selected_shape = shape
            self.repaint()
        
        self.selectionChanged.emit(len(self.selected_shapes) > 0)
        
    def de_select_shape(self, shape=None):
        """Deselect a shape or all shapes if None."""
        if shape is None and self.selected_shape:
            shape = self.selected_shape
        
        if shape is not None:
            shape.selected = False
            if shape in self.selected_shapes:
                self.selected_shapes.remove(shape)
            
            self.selected_shape = self.selected_shapes[0] if self.selected_shapes else None
            self.update()
            self.selectionChanged.emit(len(self.selected_shapes) > 0)

    def de_select_all_shapes(self):
        """Deselect all selected shapes."""
        if self.selected_shapes:
            for shape in self.selected_shapes:
                shape.selected = False
            self.selected_shapes.clear()
            self.selected_shape = None
            self.update()
            self.selectionChanged.emit(False)

    def select_all_shapes(self):
        """Select all shapes in the canvas."""
        if not self.shapes:
            return
        
        self.de_select_all_shapes()
        
        for shape in self.shapes:
            shape.selected = True
            self.selected_shapes.append(shape)
        
        if self.selected_shapes:
            self.selected_shape = self.selected_shapes[-1]
        
        self.update()
        self.selectionChanged.emit(len(self.selected_shapes) > 0)
        
    def delete_selected(self):
        """Delete all selected shapes."""
        if not self.selected_shapes:
            return None
        
        deleted = self.selected_shapes.copy()
        self.shape_history.append(self.shapes.copy())

        for shape in deleted:
            if shape in self.shapes:
                self.shapes.remove(shape)
        
        self.selected_shapes.clear()
        self.selected_shape = None
        self.update()
        return deleted
        
    # Zoom and view management
    def zoom_in(self, pos=None):
        """Zoom in at the specified position."""
        if self.zoom_level < 500:  # Max zoom: 500%
            self._apply_zoom(10, pos)
            
    def zoom_out(self, pos=None):
        """Zoom out at the specified position."""
        if self.zoom_level > 10:  # Min zoom: 10%
            self._apply_zoom(-10, pos)
            
    def _apply_zoom(self, zoom_delta, pos):
        """Apply zoom change at the specified position."""
        view_point = pos if pos else QPointF(self.width()/2, self.height()/2)
        scene_point = self.transform_pos(view_point)
        
        # Update zoom level and scale
        self.zoom_level += zoom_delta
        self.scale = self.zoom_level / 100.0
        
        # Calculate new position to maintain cursor over same scene point
        new_view_point = scene_point * self.scale + self.offset_to_center
        delta = new_view_point - view_point
        
        # Adjust offset to keep the point under cursor
        self.offset_to_center -= delta
        
        self.update()
        self.zoomRequest.emit(self.zoom_level)
            
    def center_pixmap(self):
        """Center the pixmap in the widget and fit it if larger than the view."""
        if not self.pixmap.isNull():
            w, h = self.width(), self.height()
            pw, ph = self.pixmap.width(), self.pixmap.height()
            
            # Calculate fit scale if image is larger than view
            if pw > w or ph > h:
                scale_x = w / pw if pw > w else 1.0
                scale_y = h / ph if ph > h else 1.0
                fit_scale = min(scale_x, scale_y) * 0.95
                
                if fit_scale < self.scale:
                    self.scale = fit_scale
                    self.zoom_level = int(self.scale * 100)
                    self.zoomRequest.emit(self.zoom_level)
            
            # Calculate center offset
            scaled_pw = pw * self.scale
            scaled_ph = ph * self.scale
            
            self.offset_to_center = QPointF(
                (w - scaled_pw) / 2.0 if w > scaled_pw else 0,
                (h - scaled_ph) / 2.0 if h > scaled_ph else 0
            )
            
    # Utility methods
    def transform_pos(self, point):
        """Convert from widget coordinates to scene coordinates."""
        return (point - self.offset_to_center) / self.scale
        
    def out_of_pixmap(self, p):
        """Check if point is outside the pixmap."""
        w, h = self.pixmap.width(), self.pixmap.height()
        return not (0 <= p.x() < w and 0 <= p.y() < h)
        
    def isVisible(self, shape):
        """Check if a shape is visible."""
        return self.visible.get(shape, True)
        
    def selected_vertex(self):
        """Check if a vertex is selected."""
        return self.h_vertex is not None
        
    def un_highlight(self, shape=None):
        """Remove highlight from shapes."""
        if shape is None or shape == self.h_shape:
            if self.h_shape:
                self.h_shape.highlight_clear()
            self.h_vertex = self.h_shape = None
            
    # Canvas content management
    def load_pixmap(self, pixmap):
        """Load a new pixmap and center it."""
        self.pixmap = pixmap
        self.center_pixmap()
        self.update()
        
    def load_shapes(self, shapes):
        """Load a list of shapes."""
        self.shapes = list(shapes)
        self.shape_history = []
        self.current = None
        self.repaint()
        
    def reset_state(self):
        """Reset the canvas state."""
        self.restore_cursor()
        self.pixmap = QPixmap()
        self.shapes = []
        self.shape_history = []
        self.current = None
        self.selected_shape = None
        self.selected_shapes = []
        self.selected_shape_copy = None
        self.h_shape = None
        self.h_vertex = None
        self.update()
        
    # Painting
    def paintEvent(self, event):
        """Paint the canvas contents."""
        if not self.pixmap:
            return super().paintEvent(event)
            
        p = self._painter
        p.begin(self)
        
        # Setup rendering
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        
        # Apply transformation
        p.translate(self.offset_to_center)
        p.scale(self.scale, self.scale)
        
        # Draw pixmap and shapes
        p.drawPixmap(0, 0, self.pixmap)
        
        Shape.scale = self.scale
        
        for shape in self.shapes:
            if shape in self.selected_shapes:
                shape.selected = True
            if self.isVisible(shape) and self.show_shapes:
                shape.paint(p)
            if shape in self.selected_shapes:
                shape.selected = False
        
        # Draw current shape while creating
        if self.current:
            self.current.paint(p)
        
        p.end()
        
    # Shape operations
    def finalise(self):
        """Finalize the current shape."""
        if not self.current:
            return False
            
        # Ensure proper rectangle form
        if len(self.current.points) == 2:
            self._convert_to_rectangle()
        
        # Only add if the shape has meaningful size
        if len(self.current.points) >= 2:
            rect = self.current.bounding_rect()
            if rect.width() > 1 and rect.height() > 1:
                self.current.close()
                self.shapes.append(self.current)
                self.current = None
                self.set_editing(True)
                self.newShape.emit()
                return True
                
        # Discard shape if too small
        self.current = None
        self.set_editing(True)
        return False
        
    def _convert_to_rectangle(self):
        """Convert 2-point shape to 4-point rectangle."""
        p1, p2 = self.current.points
        
        x1, y1 = min(p1.x(), p2.x()), min(p1.y(), p2.y())
        x2, y2 = max(p1.x(), p2.x()), max(p1.y(), p2.y())
        
        self.current.points = [
            QPointF(x1, y1), QPointF(x2, y1),  # top-left, top-right
            QPointF(x2, y2), QPointF(x1, y2)   # bottom-right, bottom-left
        ]
        
    # Shape selection and manipulation
    def select_shape_point(self, point, add_to_selection=False):
        """Select a shape or vertex at the given point."""
        if not add_to_selection:
            self.de_select_all_shapes()
        
        # Clear existing vertex selection
        if self.selected_vertex():
            self.h_shape.highlight_clear()
            self.h_vertex = None
            self.h_shape = None
            
        # Check for vertices first
        for shape in reversed(self.shapes):
            index = shape.nearest_vertex(point, self.epsilon / self.scale)
            if index is not None:
                self._select_vertex(shape, index, add_to_selection)
                return
                
        # Check for shapes
        for shape in reversed(self.shapes):
            if shape.contains_point(point):
                self.select_shape(shape, add_to_selection)
                self.prev_point = point
                self.override_cursor(CURSOR_MOVE)
                self.setToolTip("Drag to move shape")
                return
                
    def _select_vertex(self, shape, index, add_to_selection):
        """Select a specific vertex of a shape."""
        self.h_vertex = index
        self.h_shape = shape
        self.select_shape(shape, add_to_selection)
        shape.highlight_vertex(index, shape.MOVE_VERTEX)
        self.override_cursor(CURSOR_POINT)
        self.setToolTip("Drag to move vertex")
        
    # Movement operations
    def bounded_move_vertex(self, pos):
        """Move a vertex while keeping it within bounds."""
        if not (self.selected_vertex() and self.h_shape and len(self.h_shape.points) == 4):
            return
            
        index = self.h_vertex
        shape = self.h_shape
        point = shape[index]
        
        # Clip to image boundaries
        if self.out_of_pixmap(pos):
            size = self.pixmap.size()
            pos = QPointF(
                min(max(0, pos.x()), size.width()),
                min(max(0, pos.y()), size.height())
            )
        
        # Move the vertex and maintain rectangle shape
        shape.move_vertex_by(index, pos - point)
        self._maintain_rectangle_constraints(shape, index)
            
    def _maintain_rectangle_constraints(self, shape, moved_index):
        """Maintain rectangle constraints when moving a vertex."""
        points = shape.points
        
        if moved_index == 0:    # Top-left
            points[1].setY(points[0].y())  # Top-right maintains y
            points[3].setX(points[0].x())  # Bottom-left maintains x
        elif moved_index == 1:  # Top-right
            points[0].setY(points[1].y())  # Top-left maintains y
            points[2].setX(points[1].x())  # Bottom-right maintains x
        elif moved_index == 2:  # Bottom-right
            points[1].setX(points[2].x())  # Top-right maintains x
            points[3].setY(points[2].y())  # Bottom-left maintains y
        elif moved_index == 3:  # Bottom-left
            points[0].setX(points[3].x())  # Top-left maintains x
            points[2].setY(points[3].y())  # Bottom-right maintains y
            
    def bounded_move_shape(self, shape, pos):
        """Move a shape while keeping it within bounds."""
        if shape is None:
            return
            
        offset = pos - self.prev_point
        if offset == QPointF(0, 0):
            return
            
        # Calculate bounds and constrain movement
        rect = shape.bounding_rect()
        rect.translate(offset)
        
        size = self.pixmap.size()
        if rect.right() > size.width():
            offset.setX(offset.x() - (rect.right() - size.width()))
        if rect.bottom() > size.height():
            offset.setY(offset.y() - (rect.bottom() - size.height()))
        if rect.left() < 0:
            offset.setX(offset.x() - rect.left())
        if rect.top() < 0:
            offset.setY(offset.y() - rect.top())
            
        shape.move_by(offset)
        self.prev_point = pos
        
    def _ensure_rectangle(self, shape):
        """Ensure the shape is a proper rectangle with straight edges."""
        if len(shape.points) != 4:
            return
            
        # Find bounding box and reset points
        min_x = min(p.x() for p in shape.points)
        min_y = min(p.y() for p in shape.points)
        max_x = max(p.x() for p in shape.points)
        max_y = max(p.y() for p in shape.points)
        
        shape.points[0] = QPointF(min_x, min_y)  # top-left
        shape.points[1] = QPointF(max_x, min_y)  # top-right
        shape.points[2] = QPointF(max_x, max_y)  # bottom-right
        shape.points[3] = QPointF(min_x, max_y)  # bottom-left
        
    # Data conversion methods
    def shapes_to_normalized_rects(self):
        """Convert all shapes to normalized rectangles."""
        if not self.pixmap:
            return []
            
        img_width = self.pixmap.width()
        img_height = self.pixmap.height()
        
        rect_data = []
        for shape in self.shapes:
            rect_data.append({
                'rect': shape.to_normalized_rect(img_width, img_height),
                'label': shape.label
            })
            
        return rect_data
        
    # UI and cursor management
    def override_cursor(self, cursor):
        """Override the current cursor."""
        self.restoreCursor = False
        self._cursor = cursor
        QApplication.setOverrideCursor(cursor)
        
    def restore_cursor(self):
        """Restore the cursor."""
        QApplication.restoreOverrideCursor()
        
    def set_shape_visible(self, shape, value):
        """Set visibility for a shape."""
        self.visible[shape] = value
        self.repaint()
        
    def set_painting_labels(self, value):
        """Set whether to paint labels."""
        self.paint_labels = value
        if self.shapes:
            for shape in self.shapes:
                shape.paint_label = value
            self.update()
            
    def set_visible_shapes(self, visible):
        """Set whether shapes are visible."""
        self.show_shapes = visible
        self.update()
        
    def undo(self):
        """Undo the last shape addition or deletion."""
        if not self.shape_history:
            return False
        self.de_select_all_shapes()
        self.shapes = self.shape_history.pop()
        self.update()
        return True

    def setModified(self, modified=True):
        """Mark the canvas as modified to indicate unsaved changes."""
        self.modified = modified
