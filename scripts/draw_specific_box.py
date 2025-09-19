#!/usr/bin/env python3
import json
import os
import sys
from PIL import Image, ImageDraw, ImageFont

def draw_box_at_coordinates(image_path, output_path=None):
    """Draw a box at specific coordinates"""
    try:
        # Load image
        img = Image.open(image_path)
        draw = ImageDraw.Draw(img)
        width, height = img.size
        
        print(f"Image dimensions: {width}x{height}")
        
        # Viewport corners coordinates
        viewport_corners = {
            "TopLeft": {"x": -133.11322030184525, "y": -21.580671151432, "z": -7.105427357601002E-15},
            "TopRight": {"x": 124.88934707710165, "y": -21.580671151432, "z": -7.105427357601002E-15},
            "BottomLeft": {"x": -133.11322030184525, "y": -21.580671151432, "z": -161.8339800805128},
            "BottomRight": {"x": 124.88934707710165, "y": -21.580671151432, "z": -161.8339800805128}
        }
        
        # Extract viewport dimensions
        viewport_width = viewport_corners["TopRight"]["x"] - viewport_corners["TopLeft"]["x"]
        viewport_height = viewport_corners["BottomLeft"]["z"] - viewport_corners["TopLeft"]["z"]
        
        print(f"Viewport dimensions: {viewport_width} x {viewport_height}")
        
        # Specific point coordinates
        point_x = -24.447916666666885
        point_y = -28.90479103488828
        
        # Create a 10x10 box around the point
        box_half_size = 1.0
        box_min_x = point_x - box_half_size
        box_min_z = point_y - box_half_size  # Using Y as Z as mentioned
        box_max_x = point_x + box_half_size
        box_max_z = point_y + box_half_size  # Using Y as Z as mentioned
        
        print(f"Box coordinates: ({box_min_x}, {box_min_z}) to ({box_max_x}, {box_max_z})")
        
        # Function to map model coordinates to image coordinates
        def map_to_image(x, z):
            # Linear mapping from model space to image space
            img_x = int((x - viewport_corners["TopLeft"]["x"]) / viewport_width * width)
            # Z axis is inverted (negative is up in model, down in image)
            # Using absolute values for z coordinates since they're negative
            z_range = abs(viewport_corners["BottomLeft"]["z"] - viewport_corners["TopLeft"]["z"])
            z_pos = abs(z - viewport_corners["TopLeft"]["z"])
            img_y = int(z_pos / z_range * height)
            return img_x, img_y
        
        # Map box coordinates to image
        img_min_x, img_min_y = map_to_image(box_min_x, box_min_z)
        img_max_x, img_max_y = map_to_image(box_max_x, box_max_z)
        
        print(f"Image box coordinates: ({img_min_x}, {img_min_y}) to ({img_max_x}, {img_max_y})")
        
        # Draw reference points for viewport corners
        point_size = 5
        for corner, coords in viewport_corners.items():
            x, y = map_to_image(coords["x"], coords["z"])
            draw.ellipse((x-point_size, y-point_size, x+point_size, y+point_size), 
                        fill=(255, 0, 0), outline=(0, 0, 0))
            draw.text((x+point_size+2, y), corner, fill=(255, 0, 0))
        
        # Ensure coordinates are in the right order (min <= max)
        x1, y1 = min(img_min_x, img_max_x), min(img_min_y, img_max_y)
        x2, y2 = max(img_min_x, img_max_x), max(img_min_y, img_max_y)
        
        # Draw the box with thick blue line
        line_width = 8
        blue_color = (0, 0, 255)  # RGB for blue
        draw.rectangle((x1, y1, x2, y2), outline=blue_color, width=line_width)
        
        # Draw text with coordinates
        text = f"({point_x}, {point_y})"
        draw.text((x1, y1-20), text, fill=blue_color)
        
        # Save output image
        if output_path is None:
            output_path = os.path.splitext(image_path)[0] + ".specific_box.png"
        img.save(output_path)
        print(f"Image with specific box saved to: {output_path}")
        return output_path
    
    except Exception as e:
        print(f"Error drawing specific box: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python draw_specific_box.py <image_path> [output_path]")
        return
    
    image_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    output_path = draw_box_at_coordinates(image_path, output_path)
    if output_path:
        print(f"Success! Output saved to: {output_path}")

if __name__ == "__main__":
    main()
