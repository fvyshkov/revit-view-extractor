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

def draw_debug_boxes(image_path, json_data):
    """Draw debug boxes and reference points on the image"""
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
        
        # Draw reference points (viewport corners)
        point_size = 10
        for name, point in corners.items():
            x = float(point.get("x", 0))
            z = float(point.get("z", 0))
            img_x, img_y = map_to_image(x, z)
            
            # Draw point
            if name == "Center":
                color = "yellow"
            elif "Top" in name:
                color = "red"
            elif "Bottom" in name:
                color = "blue"
            elif "Left" in name:
                color = "green"
            elif "Right" in name:
                color = "purple"
            else:
                color = "white"
                
            draw.ellipse((img_x-point_size, img_y-point_size, 
                         img_x+point_size, img_y+point_size), 
                         fill=color)
            
            # Draw label
            draw.text((img_x+point_size, img_y+point_size), 
                     name, fill="white")
            
            print(f"{name}: Model({x}, {z}) -> Image({img_x}, {img_y})")
        
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
            
            # Get text
            text = annotation.get("text", f"Tag {i}")
            
            # Map to image coordinates
            img_min_x, img_min_y = map_to_image(min_x, min_z)
            img_max_x, img_max_y = map_to_image(max_x, max_z)
            
            # Draw bounding box - ensure y1 <= y2
            x1, y1 = min(img_min_x, img_max_x), min(img_min_y, img_max_y)
            x2, y2 = max(img_min_x, img_max_x), max(img_min_y, img_max_y)
            
            # Check if box is outside image
            is_outside = (x2 < 0 or x1 > width or y2 < 0 or y1 > height)
            
            # Use different color if outside
            box_color = "red" if is_outside else "blue"
            
            # Clamp coordinates to image bounds for drawing
            x1 = max(0, min(width, x1))
            y1 = max(0, min(height, y1))
            x2 = max(0, min(width, x2))
            y2 = max(0, min(height, y2))
            
            # Draw box if at least partially visible
            if x1 < width and y1 < height and x2 > 0 and y2 > 0:
                draw.rectangle((x1, y1, x2, y2), outline=box_color, width=3)
                
            # Draw position indicator at tag position
            tag_x, tag_y = map_to_image((min_x + max_x)/2, (min_z + max_z)/2)
            if 0 <= tag_x < width and 0 <= tag_y < height:
                draw.ellipse((tag_x-5, tag_y-5, tag_x+5, tag_y+5), fill="green")
                
            # Add debug info to image
            debug_text = f"Tag: {text}\nModel: ({min_x:.1f},{min_z:.1f})-({max_x:.1f},{max_z:.1f})\nImage: ({img_min_x},{img_min_y})-({img_max_x},{img_max_y})"
            draw.text((20, 20 + i*60), debug_text, fill="white")
            
            # Draw text near the box if visible
            if 0 <= tag_x < width and 0 <= tag_y < height:
                draw.text((tag_x+10, tag_y-10), text, fill=box_color)
            
            print(f"Annotation {i} ({text}): Model({min_x}, {min_z}) to ({max_x}, {max_z}) -> Image({img_min_x}, {img_min_y}) to ({img_max_x}, {img_max_y})")
        
        # Save output image
        output_path = os.path.splitext(image_path)[0] + ".boxes.png"
        img.save(output_path)
        print(f"Debug visualization saved to: {output_path}")
        return output_path
    
    except Exception as e:
        print(f"Error drawing debug boxes: {e}")
        return None

def main():
    if len(sys.argv) < 3:
        print("Usage: python draw_debug_boxes.py <json_path> <image_path>")
        return
    
    json_path = sys.argv[1]
    image_path = sys.argv[2]
    
    json_data = load_json(json_path)
    if json_data:
        output_path = draw_debug_boxes(image_path, json_data)
        if output_path:
            print(f"Success! Output saved to: {output_path}")

if __name__ == "__main__":
    main()
