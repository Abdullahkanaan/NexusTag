import os
import yaml
from PIL import Image

# Try to import OpenCV, but provide a fallback if it fails
try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False

class AIDetector:
    """Class for AI-based object detection."""
    
    def __init__(self):
        """Initialize the detector."""
        self.model = None
        self.model_path = None
        self.model_family = None
        self.model_classes = []
        self.detection_class = None  # Index of class to detect, None means all classes
        self.target_class = None     # Target class name for labeling detected objects
        self.confidence_threshold = 0.4  # Confidence threshold for detections
        
    def set_model_family(self, family):
        """Set the model family (YOLO, TensorFlow, etc.)."""
        self.model_family = family
        
    def load_model(self, model_path):
        """Load a model from the specified path."""
        # Save the model path
        self.model_path = model_path
        
        if self.model_family == "YOLO":
            try:
                # Try to import ultralytics YOLO
                try:
                    from ultralytics import YOLO
                    YOLO_AVAILABLE = True
                except ImportError:
                    print("Ultralytics not available, using mock detection")
                    YOLO_AVAILABLE = False
                
                # Check if file exists
                if not os.path.exists(model_path):
                    print(f"Model file not found: {model_path}")
                    return False
                
                # Load the YOLO model
                print(f"Loading YOLO model from {model_path}")
                
                if YOLO_AVAILABLE:
                    self.model = YOLO(model_path)
                    if hasattr(self.model, 'names'):
                        self.model_classes = list(self.model.names.values())
                else:
                    self.model = "mock_model"
                    self.model_classes = ["person", "bicycle", "car", "motorcycle", "airplane"]
                
                return True
            except Exception as e:
                print(f"Error loading YOLO model: {str(e)}")
                self.model = "mock_model"
                self.model_classes = ["person", "bicycle", "car", "motorcycle", "airplane"]
                return True
        else:
            self.model = "mock_model"
            self.model_classes = ["person", "bicycle", "car", "motorcycle", "airplane"]
            return True
        
    def model_loaded(self):
        """Check if a model is loaded."""
        return self.model is not None
        
    def is_configured(self):
        """Check if detector is configured (for backward compatibility)."""
        return self.model_loaded()
        
    def load_classes_from_yaml(self, yaml_path):
        """Load class names from a YAML file."""
        try:
            with open(yaml_path, 'r') as file:
                data = yaml.safe_load(file)
                
                # YOLO format: 'names' key with list or dict of class names
                if 'names' in data:
                    names = data['names']
                    if isinstance(names, list):
                        self.model_classes = names
                    elif isinstance(names, dict):
                        max_idx = max(int(idx) if isinstance(idx, str) else idx for idx in names.keys())
                        self.model_classes = [None] * (max_idx + 1)
                        for idx, name in names.items():
                            idx_int = int(idx) if isinstance(idx, str) else idx
                            self.model_classes[idx_int] = name
                    return self.model_classes
                elif 'classes' in data:
                    self.model_classes = data['classes']
                    return self.model_classes

            return []
        except Exception as e:
            print(f"Error loading classes from YAML: {str(e)}")
            return []
            
    def set_detection_class(self, class_index):
        """Set which class to detect. None means detect all classes."""
        self.detection_class = class_index

    def set_target_class(self, class_name):
        """Set the target class name for labeling detected objects."""
        self.target_class = class_name
        
    def get_target_class(self):
        """Get the target class name."""
        return self.target_class
        
    def detect_objects(self, image_path):
        """Detect objects in the image."""
        if not self.model:
            return {'boxes': [], 'classes': []}

        if not os.path.exists(image_path):
            return {'boxes': [], 'classes': []}

        if isinstance(self.model, str) and self.model == "mock_model":
            return self._detect_mock(image_path)
        elif self.model_family == "YOLO" and OPENCV_AVAILABLE:
            return self._detect_with_ultralytics(image_path)
        else:
            return self._detect_mock(image_path)
            
    def _detect_with_ultralytics(self, image_path):
        """Use the ultralytics YOLO model for detection."""
        try:
            frame = cv2.imread(image_path)
            if frame is None:
                return {'boxes': [], 'classes': []}

            img_height, img_width = frame.shape[:2]
            results = self.model(frame)[0]

            detections = []
            classes = []

            for result in results.boxes.data.tolist():
                x1, y1, x2, y2, score, class_id = result

                if score < self.confidence_threshold:
                    continue

                if self.detection_class is not None and int(class_id) != self.detection_class:
                    continue

                x = x1 / img_width
                y = y1 / img_height
                width = (x2 - x1) / img_width
                height = (y2 - y1) / img_height

                detections.append([x, y, width, height])

                if self.target_class:
                    class_name = self.target_class
                else:
                    class_idx = int(class_id)
                    if hasattr(self.model, 'names') and class_idx in self.model.names:
                        class_name = self.model.names[class_idx]
                    else:
                        class_name = str(class_idx)

                classes.append(class_name)

            return {'boxes': detections, 'classes': classes}

        except Exception as e:
            print(f"Error in YOLO detection: {str(e)}")
            return {'boxes': [], 'classes': []}
            
    def _detect_mock(self, image_path):
        """Mock detection used when no real model is loaded."""
        import random

        if random.random() < 0.5:
            return {'boxes': [], 'classes': []}

        num_detections = random.randint(1, 3)
        boxes = []
        classes = []
        class_list = self.model_classes if self.model_classes else ["person", "bicycle", "car"]

        for _ in range(num_detections):
            x = random.uniform(0.1, 0.6)
            y = random.uniform(0.1, 0.6)
            width = random.uniform(0.15, 0.35)
            height = random.uniform(0.15, 0.35)
            width = min(width, 1.0 - x)
            height = min(height, 1.0 - y)
            boxes.append([x, y, width, height])
            classes.append(self.target_class if self.target_class else random.choice(class_list))

        return {'boxes': boxes, 'classes': classes}
    
    def detect(self, image_path):
        """Detect objects in the image (for backward compatibility)."""
        return self.detect_objects(image_path) 