import os
import sys
import json
from PIL import Image, ImageDraw, ImageFont

def main():
    # Check arguments
    if len(sys.argv) < 3:
        print("Usage: python extract_coords.py <image_path> <json_path>")
        return 1
    
    image_path = sys.argv[1]
    json_path = sys.argv[2]
    
    # Check if files exist
    if not os.path.exists(image_path):
        print(f"Error: Image file not found: {image_path}")
        return 1
    
    if not os.path.exists(json_path):
        print(f"Error: JSON file not found: {json_path}")
        return 1
    
    # Load image and JSON
    try:
        img = Image.open(image_path)
        width, height = img.size
        print(f"Image dimensions: {width}x{height}")
        
        # Create a copy for drawing
        img_with_boxes = img.copy()
        draw = ImageDraw.Draw(img_with_boxes)
        
        # Load JSON
        with open(json_path, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
        
        # Get crop box
        crop = data.get('cropBox', {})
        if not crop:
            print("Warning: No crop box found in JSON")
        
        # Get annotations
        annotations = data.get('annotations', [])
        print(f"Found {len(annotations)} annotations")
        
        # Try different coordinate mappings
        results = {}
        
        # 1. Try XZ mapping (for elevations)
        xz_img = img.copy()
        xz_draw = ImageDraw.Draw(xz_img)
        xz_count = map_annotations_xz(xz_draw, annotations, crop, width, height)
        results["XZ"] = (xz_img, xz_count)
        
        # 2. Try XY mapping (for plans)
        xy_img = img.copy()
        xy_draw = ImageDraw.Draw(xy_img)
        xy_count = map_annotations_xy(xy_draw, annotations, crop, width, height)
        results["XY"] = (xy_img, xy_count)
        
        # Save results
        output_dir = os.path.dirname(image_path)
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        
        for name, (img, count) in results.items():
            out_path = os.path.join(output_dir, f"{base_name}.{name}.png")
            img.save(out_path)
            print(f"Saved {count} boxes using {name} mapping to {out_path}")
        
        return 0
    
    except Exception as e:
        print(f"Error: {e}")
        return 1

def map_annotations_xz(draw, annotations, crop, width, height):
    """Map annotations using X and Z coordinates (for elevations)"""
    count = 0
    
    # Get crop box bounds
    if not crop or 'min' not in crop or 'max' not in crop:
        return 0
    
    cx_min = crop['min']['x']
    cx_max = crop['max']['x']
    cz_min = crop['min']['z']
    cz_max = crop['max']['z']
    
    # Calculate ranges
    cx_range = cx_max - cx_min
    cz_range = cz_max - cz_min
    
    if cx_range <= 0 or cz_range <= 0:
        print("Warning: Invalid crop box ranges")
        return 0
    
    for ann in annotations:
        bbox = ann.get('bbox')
        if not bbox:
            continue
        
        # Get annotation bounds
        try:
            x_min = bbox['min']['x']
            x_max = bbox['max']['x']
            z_min = bbox['min']['z']
            z_max = bbox['max']['z']
            
            # Map to image coordinates
            px1 = int((x_min - cx_min) / cx_range * width)
            px2 = int((x_max - cx_min) / cx_range * width)
            
            # Flip Y because image coordinates start from top
            py1 = height - int((z_min - cz_min) / cz_range * height)
            py2 = height - int((z_max - cz_min) / cz_range * height)
            
            # Ensure coordinates are within image bounds
            px1 = max(0, min(width-1, px1))
            px2 = max(0, min(width-1, px2))
            py1 = max(0, min(height-1, py1))
            py2 = max(0, min(height-1, py2))
            
            # Skip if box is too small
            if abs(px2 - px1) < 2 or abs(py2 - py1) < 2:
                continue
            
            # Draw rectangle
            draw.rectangle([px1, py1, px2, py2], outline=(255, 0, 0), width=2)
            
            # Add label
            text = ann.get('text', '')
            if text:
                draw.rectangle([px1, py1-20, px1+len(text)*8, py1], fill=(0, 0, 0, 128))
                draw.text((px1+2, py1-18), text, fill=(255, 255, 255))
            
            count += 1
        except Exception as e:
            print(f"Error processing annotation: {e}")
    
    return count

def map_annotations_xy(draw, annotations, crop, width, height):
    """Map annotations using X and Y coordinates (for plans)"""
    count = 0
    
    # Get crop box bounds
    if not crop or 'min' not in crop or 'max' not in crop:
        return 0
    
    cx_min = crop['min']['x']
    cx_max = crop['max']['x']
    cy_min = crop['min']['y']
    cy_max = crop['max']['y']
    
    # Calculate ranges
    cx_range = cx_max - cx_min
    cy_range = cy_max - cy_min
    
    if cx_range <= 0 or cy_range <= 0:
        print("Warning: Invalid crop box ranges")
        return 0
    
    for ann in annotations:
        bbox = ann.get('bbox')
        if not bbox:
            continue
        
        # Get annotation bounds
        try:
            x_min = bbox['min']['x']
            x_max = bbox['max']['x']
            y_min = bbox['min']['y']
            y_max = bbox['max']['y']
            
            # Map to image coordinates
            px1 = int((x_min - cx_min) / cx_range * width)
            px2 = int((x_max - cx_min) / cx_range * width)
            
            # Flip Y because image coordinates start from top
            py1 = height - int((y_min - cy_min) / cy_range * height)
            py2 = height - int((y_max - cy_min) / cy_range * height)
            
            # Ensure coordinates are within image bounds
            px1 = max(0, min(width-1, px1))
            px2 = max(0, min(width-1, px2))
            py1 = max(0, min(height-1, py1))
            py2 = max(0, min(height-1, py2))
            
            # Skip if box is too small
            if abs(px2 - px1) < 2 or abs(py2 - py1) < 2:
                continue
            
            # Draw rectangle
            draw.rectangle([px1, py1, px2, py2], outline=(0, 0, 255), width=2)
            
            # Add label
            text = ann.get('text', '')
            if text:
                draw.rectangle([px1, py1-20, px1+len(text)*8, py1], fill=(0, 0, 0, 128))
                draw.text((px1+2, py1-18), text, fill=(255, 255, 255))
            
            count += 1
        except Exception as e:
            print(f"Error processing annotation: {e}")
    
    return count

if __name__ == "__main__":
    sys.exit(main())
