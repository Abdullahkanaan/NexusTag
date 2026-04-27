import os
import json
import yaml
from glob import glob
from collections import defaultdict
from xml.etree import ElementTree as ET

class Dataset:
    def __init__(self):
        self.images_folder = None
        self.labels_folder = None
        self.image_paths = []
        self.label_paths = []
        self.verified_images = set()
        self.classes = []
        self.annotations = {}
        self.unsaved_changes = set()
        self.classes_file_path = None
        
    def load_images(self, folder_path):
        """Load all images from a folder."""
        self.images_folder = folder_path
        
        # Get supported image extensions
        extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.gif']
        image_paths = []
        
        for ext in extensions:
            image_paths.extend(glob(os.path.join(folder_path, ext)))
            
        # Sort paths by filename
        self.image_paths = sorted(image_paths, key=lambda x: os.path.basename(x))
        
        # Initialize annotations dictionary
        self.annotations = {}
        self.unsaved_changes = set()
        self.verified_images = set()
        
    def set_labels_folder(self, folder_path):
        """Set the folder for label files."""
        self.labels_folder = folder_path
        self.load_existing_labels()
        
    def load_existing_labels(self):
        """Load existing label files from the labels folder."""
        if not self.labels_folder or not os.path.exists(self.labels_folder):
            return
            
        # Clear existing label paths
        self.label_paths = []
        
        # Get all label files (.txt for YOLO, .xml for Pascal VOC, .json for CreateML)
        label_files = []
        for ext in ['*.txt', '*.xml', '*.json']:
            label_files.extend(glob(os.path.join(self.labels_folder, ext)))
            
        # Match label files with images
        for i, img_path in enumerate(self.image_paths):
            img_name = os.path.splitext(os.path.basename(img_path))[0]
            
            # Find matching label file
            label_path = None
            for lbl_file in label_files:
                lbl_name = os.path.splitext(os.path.basename(lbl_file))[0]
                if lbl_name == img_name:
                    label_path = lbl_file
                    break
                    
            if label_path:
                self.label_paths.append(label_path)
                # Load the annotation data
                self.load_annotation(i, label_path)
            else:
                self.label_paths.append(None)
                
    def load_annotation(self, img_index, label_path):
        """Load annotation data from a label file."""
        if not label_path or not os.path.exists(label_path):
            return
            
        ext = os.path.splitext(label_path)[1].lower()
        
        try:
            if ext == '.txt':  # YOLO format
                self.load_yolo_annotation(img_index, label_path)
            elif ext == '.xml':  # Pascal VOC format
                self.load_pascal_annotation(img_index, label_path)
            elif ext == '.json':  # CreateML format
                self.load_createml_annotation(img_index, label_path)
        except Exception as e:
            print(f"Error loading annotation from {label_path}: {str(e)}")
            
    def load_yolo_annotation(self, img_index, label_path):
        """Load annotation in YOLO format."""
        boxes = []
        classes = []
        
        with open(label_path, 'r') as f:
            lines = f.readlines()
            
        for line in lines:
            line = line.strip()
            if line:
                parts = line.split()
                if len(parts) >= 5:
                    class_idx = parts[0]
                    x_center = float(parts[1])
                    y_center = float(parts[2])
                    width = float(parts[3])
                    height = float(parts[4])
                    
                    # Convert YOLO format (x_center, y_center, width, height) to our format (x, y, width, height)
                    x = x_center - width/2
                    y = y_center - height/2
                    
                    boxes.append([x, y, width, height])
                    classes.append(class_idx)
                    
        self.annotations[img_index] = {'boxes': boxes, 'classes': classes}
        
    def load_pascal_annotation(self, img_index, label_path):
        """Load annotation in Pascal VOC format."""
        boxes = []
        classes = []

        try:
            tree = ET.parse(label_path)
            root = tree.getroot()

            size = root.find('size')
            if size is not None:
                img_w = int(size.find('width').text)
                img_h = int(size.find('height').text)
            else:
                img_w, img_h = 1, 1

            for obj in root.findall('object'):
                class_name = obj.find('name').text
                bndbox = obj.find('bndbox')
                xmin = float(bndbox.find('xmin').text) / img_w
                ymin = float(bndbox.find('ymin').text) / img_h
                xmax = float(bndbox.find('xmax').text) / img_w
                ymax = float(bndbox.find('ymax').text) / img_h
                boxes.append([xmin, ymin, xmax - xmin, ymax - ymin])
                classes.append(class_name)
        except Exception as e:
            print(f"Error parsing Pascal VOC annotation {label_path}: {str(e)}")

        self.annotations[img_index] = {'boxes': boxes, 'classes': classes}
        
    def load_createml_annotation(self, img_index, label_path):
        """Load annotation in CreateML format."""
        with open(label_path, 'r') as f:
            data = json.load(f)
            
        boxes = []
        classes = []
        
        # Extract annotations from CreateML format
        img_data = data.get('annotations', [{}])[0]
        for ann in img_data.get('annotations', []):
            label = ann.get('label', '0')
            coords = ann.get('coordinates', {})
            x = coords.get('x', 0) / 100  # Normalize to 0-1 range
            y = coords.get('y', 0) / 100
            width = coords.get('width', 0) / 100
            height = coords.get('height', 0) / 100
            
            boxes.append([x - width/2, y - height/2, width, height])
            classes.append(label)
            
        self.annotations[img_index] = {'boxes': boxes, 'classes': classes}
        
    def get_image_count(self):
        """Get the number of images in the dataset."""
        return len(self.image_paths)
        
    def get_image_path_by_index(self, index):
        """Get the path of an image by its index."""
        if 0 <= index < len(self.image_paths):
            return self.image_paths[index]
        return None
        
    def get_current_image_path(self, index):
        """Get the path of the current image."""
        return self.get_image_path_by_index(index)
        
    def get_label_name_by_index(self, index):
        """Get the label filename for an image index."""
        if 0 <= index < len(self.label_paths) and self.label_paths[index]:
            return os.path.basename(self.label_paths[index])
        return None
        
    def get_annotations_for_image(self, index):
        """Get annotations for an image by index."""
        return self.annotations.get(index, {'boxes': [], 'classes': []})
        
    def save_annotations_for_image(self, index, annotations):
        """Save annotations for a specific image."""
        self.annotations[index] = annotations
        
        # Mark as changed
        self.unsaved_changes.add(index)
        
        # If label folder exists, save to file
        if self.labels_folder:
            self.save_annotation_to_file(index)
            
    def save_annotation_to_file(self, index):
        """Save annotation to a file based on the current format preference."""
        if not self.labels_folder or not os.path.exists(self.labels_folder):
            return False
            
        if index not in self.annotations:
            return False
            
        img_path = self.image_paths[index]
        img_name = os.path.splitext(os.path.basename(img_path))[0]
        
        # Default to YOLO format
        label_path = os.path.join(self.labels_folder, f"{img_name}.txt")
        
        # Save in YOLO format by default
        self.save_as_yolo(index, label_path)
        
        # Update label paths
        if index < len(self.label_paths):
            self.label_paths[index] = label_path
        else:
            self.label_paths.append(label_path)
            
        # Remove from unsaved changes
        if index in self.unsaved_changes:
            self.unsaved_changes.remove(index)
            
        return True
        
    def save_as_yolo(self, index, output_path):
        """Save annotation in YOLO format."""
        annotation = self.annotations.get(index, {})
        boxes = annotation.get('boxes', [])
        classes = annotation.get('classes', [])
        
        with open(output_path, 'w') as f:
            for i, (box, class_idx) in enumerate(zip(boxes, classes)):
                # Convert our format (x, y, width, height) to YOLO format (x_center, y_center, width, height)
                x_center = box[0] + box[2]/2
                y_center = box[1] + box[3]/2
                width = box[2]
                height = box[3]
                
                f.write(f"{class_idx} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")
                
    def save_all_annotations(self):
        """Save all annotations to files."""
        for index in list(self.unsaved_changes):
            self.save_annotation_to_file(index)
            
    def add_detections_for_image(self, index, detections):
        """Add AI detections for a specific image."""
        if index not in self.annotations:
            self.annotations[index] = {'boxes': [], 'classes': []}
            
        current = self.annotations[index]
        
        # Add new detections
        if detections:
            current['boxes'].extend(detections.get('boxes', []))
            current['classes'].extend(detections.get('classes', []))
            
        # Mark as changed
        self.unsaved_changes.add(index)
        
    def is_image_verified(self, index):
        """Check if an image is verified."""
        return index in self.verified_images
        
    def set_image_verified(self, index, verified):
        """Set verification status for an image."""
        if verified:
            self.verified_images.add(index)
        elif index in self.verified_images:
            self.verified_images.remove(index)
            
    def delete_image(self, index):
        """Delete an image and its annotation."""
        if 0 <= index < len(self.image_paths):
            # Remove the image file
            img_path = self.image_paths[index]
            label_path = self.label_paths[index] if index < len(self.label_paths) else None
            
            try:
                if os.path.exists(img_path):
                    os.remove(img_path)
                    
                if label_path and os.path.exists(label_path):
                    os.remove(label_path)
            except Exception as e:
                print(f"Error deleting files: {str(e)}")
                
            # Remove from data structures
            self.image_paths.pop(index)
            
            if index < len(self.label_paths):
                self.label_paths.pop(index)
                
            if index in self.annotations:
                del self.annotations[index]
                
            if index in self.unsaved_changes:
                self.unsaved_changes.remove(index)
                
            if index in self.verified_images:
                self.verified_images.remove(index)
                
            # Reindex the data structures
            self._reindex_after_delete(index)
            
            return True
        return False
        
    def _reindex_after_delete(self, deleted_index):
        """Reindex data structures after deletion."""
        # Create new annotations dictionary with updated indices
        new_annotations = {}
        new_unsaved = set()
        new_verified = set()
        
        for old_idx, data in self.annotations.items():
            if old_idx < deleted_index:
                new_annotations[old_idx] = data
            elif old_idx > deleted_index:
                new_annotations[old_idx - 1] = data
                
        for old_idx in self.unsaved_changes:
            if old_idx < deleted_index:
                new_unsaved.add(old_idx)
            elif old_idx > deleted_index:
                new_unsaved.add(old_idx - 1)
                
        for old_idx in self.verified_images:
            if old_idx < deleted_index:
                new_verified.add(old_idx)
            elif old_idx > deleted_index:
                new_verified.add(old_idx - 1)
                
        self.annotations = new_annotations
        self.unsaved_changes = new_unsaved
        self.verified_images = new_verified
        
    def load_config_yaml(self, yaml_path):
        """Load classes from a YAML file."""
        if os.path.exists(yaml_path):
            with open(yaml_path, 'r') as f:
                data = yaml.safe_load(f)
                
            if 'names' in data:
                if isinstance(data['names'], list):
                    self.classes = data['names']
                elif isinstance(data['names'], dict):
                    # Convert dict to list if needed
                    self.classes = [class_name for _, class_name in sorted(data['names'].items())]
                return self.classes
                
        return []
        
    def load_classes_txt(self, txt_path=None):
        """Load classes from a text file (one class per line)."""
        # If no path provided, check if there's one in the labels folder
        if txt_path is None and self.labels_folder:
            txt_path = os.path.join(self.labels_folder, "classes.txt")
        
        # Store the classes file path for later use
        self.classes_file_path = txt_path if os.path.exists(txt_path) else None
        
        # If the file exists, load the classes
        if self.classes_file_path:
            self.classes = []
            try:
                with open(self.classes_file_path, 'r') as f:
                    for line in f:
                        class_name = line.strip()
                        if class_name:  # Skip empty lines
                            self.classes.append(class_name)
                return True
            except Exception as e:
                print(f"Error loading classes.txt: {str(e)}")
        
        return False
        
    def save_classes_txt(self, output_path=None):
        """Save classes to a text file (one class per line)."""
        # If no path provided, use the stored path or create one in the labels folder
        if output_path is None:
            output_path = self.classes_file_path
            if output_path is None and self.labels_folder:
                output_path = os.path.join(self.labels_folder, "classes.txt")
        
        # Ensure we have a valid path
        if not output_path:
            return False
        
        try:
            with open(output_path, 'w') as f:
                for class_name in self.classes:
                    f.write(f"{class_name}\n")
            
            # Update the stored file path
            self.classes_file_path = output_path
            return True
        except Exception as e:
            print(f"Error saving classes.txt: {str(e)}")
            return False
        
    def get_classes_for_image(self, index):
        """Get unique class names used in the current image."""
        image_classes = []
        class_ids_used = []
        
        if index in self.annotations:
            annotation = self.annotations[index]
            class_ids_used = annotation.get('classes', [])
        
        # Convert class IDs to names if possible
        for class_id in class_ids_used:
            try:
                # If class_id is a number (or string numeric), use it as index
                idx = int(class_id)
                if 0 <= idx < len(self.classes):
                    image_classes.append(self.classes[idx])
                else:
                    image_classes.append(str(class_id))
            except (ValueError, TypeError):
                # If class_id is not a number, use it as is (class name)
                image_classes.append(str(class_id))
        
        # Return unique class names
        return list(set(image_classes))
        
    def add_class(self, class_name):
        """Add a new class if it doesn't already exist."""
        if class_name not in self.classes:
            self.classes.append(class_name)
            
    def get_classes(self):
        """Get all classes in the dataset."""
        return self.classes
        
    def create_config_yaml(self, output_path):
        """Create a config YAML file with class definitions."""
        data = {
            'names': self.classes,
            'nc': len(self.classes)
        }
        
        with open(output_path, 'w') as f:
            yaml.dump(data, f)
            
    def get_unsaved_count(self):
        """Get the number of unsaved annotations."""
        return len(self.unsaved_changes) 