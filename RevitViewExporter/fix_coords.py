import os
import sys
import json

def main():
    """Fix pixelBBox coordinates in JSON annotations"""
    # Check arguments
    if len(sys.argv) < 2:
        print("Usage: python fix_coords.py <json_path>")
        return 1
    
    json_path = sys.argv[1]
    
    # Check if file exists
    if not os.path.exists(json_path):
        print(f"Error: JSON file not found: {json_path}")
        return 1
    
    try:
        # Load JSON
        with open(json_path, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
        
        # Get image dimensions
        img_width = data.get('imageWidth', 0)
        img_height = data.get('imageHeight', 0)
        
        if img_width == 0 or img_height == 0:
            print("Warning: Image dimensions not found in JSON. Using default 2000x886")
            img_width = 2000
            img_height = 886
            data['imageWidth'] = img_width
            data['imageHeight'] = img_height
        
        print(f"Image dimensions: {img_width}x{img_height}")
        
        # Fix annotations
        annotations = data.get('annotations', [])
        fixed_count = 0
        
        for ann in annotations:
            # Check if pixelBBox exists
            pixel_bbox = ann.get('pixelBBox')
            if not pixel_bbox:
                # Create pixelBBox from model coordinates
                bbox = ann.get('bbox')
                if not bbox or not data.get('cropBox'):
                    continue
                
                # Use X and Z coordinates for elevation views
                x_min = bbox['min']['x']
                x_max = bbox['max']['x']
                z_min = bbox['min']['z']
                z_max = bbox['max']['z']
                
                crop = data['cropBox']
                cx_min = crop['min']['x']
                cx_max = crop['max']['x']
                cz_min = crop['min']['z']
                cz_max = crop['max']['z']
                
                # Map to image coordinates
                px1 = int((x_min - cx_min) / (cx_max - cx_min) * img_width)
                px2 = int((x_max - cx_min) / (cx_max - cx_min) * img_width)
                py1 = img_height - int((z_min - cz_min) / (cz_max - cz_min) * img_height)
                py2 = img_height - int((z_max - cz_min) / (cz_max - cz_min) * img_height)
                
                # Create pixelBBox
                ann['pixelBBox'] = {
                    'min': {'x': px1, 'y': py1},
                    'max': {'x': px2, 'y': py2}
                }
                fixed_count += 1
            else:
                # Fix existing pixelBBox
                x1 = pixel_bbox['min']['x']
                y1 = pixel_bbox['min']['y']
                x2 = pixel_bbox['max']['x']
                y2 = pixel_bbox['max']['y']
                
                # Ensure coordinates are within image bounds
                x1 = max(0, min(img_width - 1, x1))
                x2 = max(0, min(img_width - 1, x2))
                y1 = max(0, min(img_height - 1, y1))
                y2 = max(0, min(img_height - 1, y2))
                
                # Update pixelBBox
                pixel_bbox['min']['x'] = x1
                pixel_bbox['min']['y'] = y1
                pixel_bbox['max']['x'] = x2
                pixel_bbox['max']['y'] = y2
                fixed_count += 1
        
        print(f"Fixed {fixed_count} annotations")
        
        # Save updated JSON
        output_path = os.path.splitext(json_path)[0] + '.fixed.json'
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        print(f"Saved fixed JSON to {output_path}")
        return 0
    
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
