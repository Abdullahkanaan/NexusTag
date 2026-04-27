import os
import json
from xml.etree import ElementTree as ET
from PIL import Image as PILImage

class AnnotationExporter:
    def __init__(self):
        self.formats = {
            'YOLO': self.export_as_yolo,
            'CreateML': self.export_as_createml,
            'Pascal/VOC': self.export_as_pascal_voc
        }
        
    def export_annotations(self, dataset, format_type, output_dir):
        """Export all annotations to the specified format."""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        if format_type not in self.formats:
            return False
            
        export_func = self.formats[format_type]
        image_count = dataset.get_image_count()
        
        for i in range(image_count):
            img_path = dataset.get_image_path_by_index(i)
            annotations = dataset.get_annotations_for_image(i)
            
            if img_path and annotations:
                img_name = os.path.splitext(os.path.basename(img_path))[0]
                export_func(img_name, img_path, annotations, output_dir)
                
        return True
        
    def export_as_yolo(self, img_name, img_path, annotations, output_dir):
        """Export annotations in YOLO format."""
        boxes = annotations.get('boxes', [])
        classes = annotations.get('classes', [])
        
        if not boxes or not classes:
            return
            
        output_path = os.path.join(output_dir, f"{img_name}.txt")
        
        with open(output_path, 'w') as f:
            for box, class_idx in zip(boxes, classes):
                # Convert our format (x, y, width, height) to YOLO format (x_center, y_center, width, height)
                x_center = box[0] + box[2]/2
                y_center = box[1] + box[3]/2
                width = box[2]
                height = box[3]
                
                f.write(f"{class_idx} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")
                
    def export_as_createml(self, img_name, img_path, annotations, output_dir):
        """Export annotations in CreateML format."""
        boxes = annotations.get('boxes', [])
        classes = annotations.get('classes', [])
        
        if not boxes or not classes:
            return
            
        output_path = os.path.join(output_dir, f"{img_name}.json")
        
        createml_annotations = []
        
        for box, class_idx in zip(boxes, classes):
            # Convert our format (x, y, width, height) to CreateML format (x_center, y_center, width, height) as % of image
            x_center = (box[0] + box[2]/2) * 100
            y_center = (box[1] + box[3]/2) * 100
            width = box[2] * 100
            height = box[3] * 100
            
            createml_annotations.append({
                'label': class_idx,
                'coordinates': {
                    'x': x_center,
                    'y': y_center,
                    'width': width,
                    'height': height
                }
            })
            
        createml_data = {
            'annotations': [{
                'image': img_name,
                'annotations': createml_annotations
            }]
        }
        
        with open(output_path, 'w') as f:
            json.dump(createml_data, f, indent=4)
            
    def export_as_pascal_voc(self, img_name, img_path, annotations, output_dir):
        """Export annotations in Pascal VOC format."""
        boxes = annotations.get('boxes', [])
        classes = annotations.get('classes', [])
        
        if not boxes or not classes:
            return
            
        output_path = os.path.join(output_dir, f"{img_name}.xml")
        
        # Create XML structure
        annotation = ET.Element("annotation")
        
        # Add image info
        folder = ET.SubElement(annotation, "folder")
        folder.text = os.path.basename(os.path.dirname(img_path))
        
        filename = ET.SubElement(annotation, "filename")
        filename.text = os.path.basename(img_path)
        
        path = ET.SubElement(annotation, "path")
        path.text = img_path
        
        # Read actual image dimensions
        try:
            with PILImage.open(img_path) as img:
                img_w, img_h = img.size
        except Exception:
            img_w, img_h = 1000, 1000

        size = ET.SubElement(annotation, "size")
        width_el = ET.SubElement(size, "width")
        width_el.text = str(img_w)
        height_el = ET.SubElement(size, "height")
        height_el.text = str(img_h)
        depth = ET.SubElement(size, "depth")
        depth.text = "3"

        # Add object annotations
        for box, class_idx in zip(boxes, classes):
            obj = ET.SubElement(annotation, "object")

            name = ET.SubElement(obj, "name")
            name.text = str(class_idx)

            pose = ET.SubElement(obj, "pose")
            pose.text = "Unspecified"

            truncated = ET.SubElement(obj, "truncated")
            truncated.text = "0"

            difficult = ET.SubElement(obj, "difficult")
            difficult.text = "0"

            bndbox = ET.SubElement(obj, "bndbox")

            xmin = ET.SubElement(bndbox, "xmin")
            xmin.text = str(int(box[0] * img_w))

            ymin = ET.SubElement(bndbox, "ymin")
            ymin.text = str(int(box[1] * img_h))

            xmax = ET.SubElement(bndbox, "xmax")
            xmax.text = str(int((box[0] + box[2]) * img_w))

            ymax = ET.SubElement(bndbox, "ymax")
            ymax.text = str(int((box[1] + box[3]) * img_h))
            
        # Write XML to file
        tree = ET.ElementTree(annotation)
        tree.write(output_path) 