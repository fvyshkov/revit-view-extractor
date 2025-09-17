import json
import sys
import os
from PIL import Image, ImageDraw, ImageFont

def draw_rect_with_text(draw, x1, y1, x2, y2, text, color, font):
    """Helper function to draw rectangle with text label"""
    # Draw rectangle
    draw.rectangle([x1, y1, x2, y2], outline=color, width=2)
    
    # Add label if text exists
    if text:
        # Background for text
        text_width = len(text) * 10
        draw.rectangle([x1, y1-20, x1+text_width, y1], fill=(0, 0, 0, 128))
        draw.text((x1+2, y1-18), text, fill=(255, 255, 255), font=font)

def main():
    # Check if a file path is provided
    if len(sys.argv) < 2:
        print("Usage: python fix_annotations.py <json_file> [output_image_name]")
        return
    
    # Load JSON data
    json_path = sys.argv[1]
    output_name = sys.argv[2] if len(sys.argv) > 2 else "annotated_image.png"
    
    try:
        with open(json_path, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading JSON file: {e}")
        return
    
    # Extract image path and dimensions
    image_path = data.get('imagePath')
    if not image_path:
        print("Error: No image path found in JSON")
        return
    
    # For macOS, convert Windows path if needed
    if image_path.startswith("C:\\"):
        parts = image_path.split("\\")
        if "Mac" in parts and "Home" in parts:
            # Find the index after "Home"
            home_index = parts.index("Home")
            if home_index < len(parts) - 1:
                image_path = "/Users/" + "/".join(parts[home_index+1:])
        else:
            # Just use the filename
            image_path = parts[-1]
            print(f"Using just the filename: {image_path}")
            # Check in current directory and addin-results
            if os.path.exists(image_path):
                pass
            elif os.path.exists(f"addin-results/{image_path}"):
                image_path = f"addin-results/{image_path}"
            else:
                print(f"Warning: Could not find image file at {image_path}")
    
    try:
        img = Image.open(image_path)
        print(f"Loaded image: {image_path}, size: {img.size[0]}x{img.size[1]}")
    except Exception as e:
        print(f"Error loading image: {e}")
        print("Creating a blank image for testing...")
        # Create a blank image with the dimensions from JSON
        img = Image.new('RGB', (data.get('imageWidth', 2000), data.get('imageHeight', 886)), color=(255, 255, 255))
    
    # Get image dimensions
    img_width, img_height = img.size
    
    # Check if dimensions in JSON match actual image
    json_width = data.get('imageWidth', 0)
    json_height = data.get('imageHeight', 0)
    
    if json_width != img_width or json_height != img_height:
        print(f"Warning: JSON dimensions ({json_width}x{json_height}) don't match image dimensions ({img_width}x{img_height})")
        print("Using actual image dimensions for scaling")
    
    # Create a copy of the image for drawing
    annotated_img = img.copy()
    draw = ImageDraw.Draw(annotated_img)
    
    # Try to load a font, use default if not available
    try:
        font = ImageFont.truetype("Arial", 16)
    except:
        font = ImageFont.load_default()
    
    # Get crop box
    crop_box = data.get('cropBox', {})
    if not crop_box:
        print("Warning: No crop box found in JSON")
        return
    
    # Extract crop box coordinates
    x_min = crop_box.get('min', {}).get('x', 0)
    x_max = crop_box.get('max', {}).get('x', 0)
    z_min = crop_box.get('min', {}).get('z', 0)
    z_max = crop_box.get('max', {}).get('z', 0)
    
    # Calculate ranges
    x_range = x_max - x_min
    z_range = z_max - z_min
    
    if x_range == 0 or z_range == 0:
        print("Error: Invalid crop box dimensions")
        return
    
    # Process annotations
    annotations = data.get('annotations', [])
    if not annotations:
        print("No annotations found in JSON")
        return
    
    print(f"Processing {len(annotations)} annotations")
    
    # Count of annotations with pixelBBox
    pixel_bbox_count = sum(1 for ann in annotations if 'pixelBBox' in ann)
    print(f"Found {pixel_bbox_count} annotations with pixelBBox")
    
    # Create multiple versions of the image with different mapping approaches
    # Original image with pixelBBox if available
    annotated_img = img.copy()
    draw = ImageDraw.Draw(annotated_img)
    
    # Try different coordinate mappings
    img_xy = img.copy()
    draw_xy = ImageDraw.Draw(img_xy)
    
    img_xz = img.copy()
    draw_xz = ImageDraw.Draw(img_xz)
    
    # Draw annotations
    count = 0
    count_xy = 0
    count_xz = 0
    
    for ann in annotations:
        # Check if pixelBBox is available
        if 'pixelBBox' in ann:
            # Use pixelBBox directly
            pixel_bbox = ann['pixelBBox']
            x1 = pixel_bbox['min']['x']
            y1 = pixel_bbox['min']['y']
            x2 = pixel_bbox['max']['x']
            y2 = pixel_bbox['max']['y']
            
            # Draw on main image
            draw_rect_with_text(draw, x1, y1, x2, y2, ann.get('text', ''), (255, 0, 0), font)
            count += 1
        
        # Always calculate alternative mappings from 3D coordinates
        bbox = ann.get('bbox')
        if not bbox:
            continue
        
        # Get all 3D coordinates
        x1_3d = bbox['min']['x']
        y1_3d = bbox['min']['y']
        z1_3d = bbox['min']['z']
        x2_3d = bbox['max']['x']
        y2_3d = bbox['max']['y']
        z2_3d = bbox['max']['z']
        
        # XY mapping (plan view style)
        x1_xy = int((x1_3d - x_min) / x_range * img_width)
        x2_xy = int((x2_3d - x_min) / x_range * img_width)
        y1_xy = int((y1_3d - crop_box['min']['y']) / (crop_box['max']['y'] - crop_box['min']['y']) * img_height)
        y2_xy = int((y2_3d - crop_box['min']['y']) / (crop_box['max']['y'] - crop_box['min']['y']) * img_height)
        
        # Ensure coordinates are within bounds
        x1_xy = max(0, min(img_width-1, x1_xy))
        x2_xy = max(0, min(img_width-1, x2_xy))
        y1_xy = max(0, min(img_height-1, y1_xy))
        y2_xy = max(0, min(img_height-1, y2_xy))
        
        # For XY mapping, always draw regardless of size
        draw_rect_with_text(draw_xy, x1_xy, y1_xy, x2_xy, y2_xy, ann.get('text', ''), (0, 255, 0), font)
        count_xy += 1
        
        # XZ mapping (elevation view style)
        x1_xz = int((x1_3d - x_min) / x_range * img_width)
        x2_xz = int((x2_3d - x_min) / x_range * img_width)
        y1_xz = int(img_height - (z1_3d - z_min) / z_range * img_height)
        y2_xz = int(img_height - (z2_3d - z_min) / z_range * img_height)
        
        # Ensure coordinates are within bounds
        x1_xz = max(0, min(img_width-1, x1_xz))
        x2_xz = max(0, min(img_width-1, x2_xz))
        y1_xz = max(0, min(img_height-1, y1_xz))
        y2_xz = max(0, min(img_height-1, y2_xz))
        
        # For XZ mapping, always draw regardless of size
        draw_rect_with_text(draw_xz, x1_xz, y1_xz, x2_xz, y2_xz, ann.get('text', ''), (0, 0, 255), font)
        count_xz += 1
    
    # Save all versions
    base_name, ext = os.path.splitext(output_name)
    
    # Save original with pixelBBox
    annotated_img.save(output_name)
    print(f"Saved annotated image with {count} pixelBBox boxes to {output_name}")
    
    # Save XY mapping
    xy_path = f"{base_name}-XY{ext}"
    img_xy.save(xy_path)
    print(f"Saved XY mapping with {count_xy} boxes to {xy_path}")
    
    # Save XZ mapping
    xz_path = f"{base_name}-XZ{ext}"
    img_xz.save(xz_path)
    print(f"Saved XZ mapping with {count_xz} boxes to {xz_path}")
    
    # Try a fourth approach - using view direction
    # For South elevation, we're looking along Y axis, so use X and Z
    img_dir = img.copy()
    draw_dir = ImageDraw.Draw(img_dir)
    count_dir = 0
    
    # Try to determine view direction from view name
    view_name = data.get('viewName', '').lower()
    
    # Default to XZ mapping for elevations
    for ann in annotations:
        bbox = ann.get('bbox')
        if not bbox:
            continue
            
        # Get 3D coordinates
        x1_3d = bbox['min']['x']
        y1_3d = bbox['min']['y']
        z1_3d = bbox['min']['z']
        x2_3d = bbox['max']['x']
        y2_3d = bbox['max']['y']
        z2_3d = bbox['max']['z']
        
        # Map X to horizontal (always)
        x1_dir = int((x1_3d - x_min) / x_range * img_width)
        x2_dir = int((x2_3d - x_min) / x_range * img_width)
        
        # Map Z to vertical (for elevations)
        y1_dir = int(img_height - (z1_3d - z_min) / z_range * img_height)
        y2_dir = int(img_height - (z2_3d - z_min) / z_range * img_height)
        
        # Ensure coordinates are within bounds
        x1_dir = max(0, min(img_width-1, x1_dir))
        x2_dir = max(0, min(img_width-1, x2_dir))
        y1_dir = max(0, min(img_height-1, y1_dir))
        y2_dir = max(0, min(img_height-1, y2_dir))
        
        # For direction mapping, always draw regardless of size
        draw_rect_with_text(draw_dir, x1_dir, y1_dir, x2_dir, y2_dir, ann.get('text', ''), (255, 0, 255), font)
        count_dir += 1
    
    # Save direction-based mapping
    dir_path = f"{base_name}-Direction{ext}"
    img_dir.save(dir_path)
    print(f"Saved direction-based mapping with {count_dir} boxes to {dir_path}")
    
    print("\nSummary:")
    print(f"- Original with pixelBBox: {count} boxes")
    print(f"- XY mapping: {count_xy} boxes")
    print(f"- XZ mapping: {count_xz} boxes")
    print(f"- Direction mapping: {count_dir} boxes")

if __name__ == "__main__":
    main()