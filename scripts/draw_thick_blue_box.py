#!/usr/bin/env python3
import json
import os
import sys
from PIL import Image, ImageDraw, ImageFont

def load_json(json_path):
    """Load JSON file with annotations"""
    try:
        with open(json_path, 'r', encoding='utf-8-sig') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading JSON: {e}")
        return None

def draw_thick_blue_box(image_path, json_data, output_path=None):
    """Draw thick blue box around tag"""
    try:
        # Load image
        img = Image.open(image_path)
        draw = ImageDraw.Draw(img)
        width, height = img.size
        
        print(f"Image dimensions: {width}x{height}")
        
        # Get viewport corners
        corners = json_data.get("viewportCorners", {})
        
        # Get crop box dimensions
        crop_box = json_data.get("cropBox", {})
        crop_min = crop_box.get("min", {})
        crop_max = crop_box.get("max", {})
        
        crop_min_x = float(crop_min.get("x", 0))
        crop_min_z = float(crop_min.get("z", 0))
        crop_max_x = float(crop_max.get("x", 0))
        crop_max_z = float(crop_max.get("z", 0))
        
        crop_width = crop_max_x - crop_min_x
        crop_height = crop_max_z - crop_min_z
        
        print(f"Crop box: X: {crop_min_x} to {crop_max_x}, Z: {crop_min_z} to {crop_max_z}")
        print(f"Crop dimensions: {crop_width} x {crop_height}")
        
        # Function to map model coordinates to image coordinates
        def map_to_image(x, z):
            # Linear mapping from model space to image space
            img_x = int((x - crop_min_x) / crop_width * width)
            # Z axis is inverted (negative is up in model, down in image)
            img_y = int(height - (z - crop_min_z) / crop_height * height)
            return img_x, img_y
        
        # Draw annotations
        annotations = json_data.get("annotations", [])
        for i, annotation in enumerate(annotations):
            # Get 3D bounding box
            bbox3d = annotation.get("bbox3D", {})
            min_point = bbox3d.get("min", {})
            max_point = bbox3d.get("max", {})
            
            min_x = float(min_point.get("x", 0))
            min_z = float(min_point.get("z", 0))
            max_x = float(max_point.get("x", 0))
            max_z = float(max_point.get("z", 0))
            
            # Get tag position (center of bbox)
            tag_x = (min_x + max_x) / 2
            tag_z = (min_z + max_z) / 2
            
            # Create a 10x10 meter box around tag center
            box_half_size = 5.0  # 5 meters in each direction = 10x10 meter box
            box_min_x = tag_x - box_half_size
            box_min_z = tag_z - box_half_size
            box_max_x = tag_x + box_half_size
            box_max_z = tag_z + box_half_size
            
            # Map to image coordinates
            img_min_x, img_min_y = map_to_image(box_min_x, box_min_z)
            img_max_x, img_max_y = map_to_image(box_max_x, box_max_z)
            
            # Draw bounding box with thick blue line (8 pixels)
            line_width = 8
            blue_color = (0, 0, 255)  # RGB for blue
            
            # Ensure coordinates are in the right order (min <= max)
            x1, y1 = min(img_min_x, img_max_x), min(img_min_y, img_max_y)
            x2, y2 = max(img_min_x, img_max_x), max(img_min_y, img_max_y)
            
            # Draw rectangle with thick blue line
            draw.rectangle((x1, y1, x2, y2), 
                         outline=blue_color, width=line_width)
            
            # Draw text
            text = annotation.get("text", f"Tag {i}")
            draw.text((img_min_x, img_min_y-20), text, fill=blue_color)
            
            print(f"Annotation {i} ({text}): Box 10x10m around ({tag_x}, {tag_z})")
            print(f"  Model coordinates: ({box_min_x}, {box_min_z}) to ({box_max_x}, {box_max_z})")
            print(f"  Image coordinates: ({img_min_x}, {img_min_y}) to ({img_max_x}, {img_max_y})")
        
        # Save output image
        if output_path is None:
            output_path = os.path.splitext(image_path)[0] + ".blue_box.png"
        img.save(output_path)
        print(f"Image with thick blue box saved to: {output_path}")
        return output_path
    
    except Exception as e:
        print(f"Error drawing thick blue box: {e}")
        return None

def main():
    if len(sys.argv) < 3:
        print("Usage: python draw_thick_blue_box.py <json_path> <image_path> [output_path]")
        return
    
    json_path = sys.argv[1]
    image_path = sys.argv[2]
    output_path = sys.argv[3] if len(sys.argv) > 3 else None
    
    json_data = load_json(json_path)
    if json_data:
        output_path = draw_thick_blue_box(image_path, json_data, output_path)
        if output_path:
            print(f"Success! Output saved to: {output_path}")

if __name__ == "__main__":
    main()
