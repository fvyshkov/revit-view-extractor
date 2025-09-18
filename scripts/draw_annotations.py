#!/usr/bin/env python3
"""
Draw annotation boxes with labels on exported view image.
Uses bbox2D coordinates from annotations JSON to draw thick blue rectangles
with annotation text labels.
"""

import argparse
import json
import os
import sys
from typing import Dict, Any, Tuple, Optional

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("ERROR: Pillow (PIL) is not installed. Install with: python3 -m pip install pillow", file=sys.stderr)
    sys.exit(1)


def load_json(path: str) -> Dict[str, Any]:
    """Load JSON with UTF-8-BOM support"""
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def find_image_path(json_data: Dict[str, Any], folder: str) -> Optional[str]:
    """Find the corresponding PNG image file"""
    # Try to get image path from JSON
    json_image_path = json_data.get("imagePath", "")
    if json_image_path:
        # Convert Windows path to posix if needed
        candidate = json_image_path
        if os.name != "nt":
            candidate = candidate.replace("C:\\Mac\\Home", os.path.expanduser("~")).replace("\\", "/")
        if os.path.isfile(candidate):
            return candidate
    
    # Search for PNG files in the folder
    view_name = json_data.get("viewName", "")
    pngs = [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith(".png")]
    
    if not pngs:
        return None
    
    # Prefer files that include the view name
    if view_name:
        lowered = view_name.lower()
        candidates = [p for p in pngs if lowered in os.path.basename(p).lower()]
        if candidates:
            # Avoid selecting already annotated images
            non_annotated = [p for p in candidates if ".annotated." not in os.path.basename(p).lower()]
            return (non_annotated or candidates)[0]
    
    # Fallback: first PNG that is not already annotated
    non_annotated = [p for p in pngs if ".annotated." not in os.path.basename(p).lower()]
    return (non_annotated or pngs)[0]


def get_font(size: int = 12):
    """Get a font for text rendering"""
    try:
        # Try to use a system font
        if os.name == "nt":  # Windows
            return ImageFont.truetype("arial.ttf", size)
        elif os.name == "posix":  # macOS/Linux
            # Try common font paths
            font_paths = [
                "/System/Library/Fonts/Arial.ttf",  # macOS
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
                "/usr/share/fonts/TTF/arial.ttf",  # Some Linux
            ]
            for font_path in font_paths:
                if os.path.exists(font_path):
                    return ImageFont.truetype(font_path, size)
    except:
        pass
    
    # Fallback to default font
    return ImageFont.load_default()


def draw_annotations_on_image(json_path: str, output_path: Optional[str] = None, 
                            line_width: int = 4, font_size: int = 12,
                            corners_only: bool = False) -> str:
    """Draw annotation boxes and labels on the image"""
    
    # Load JSON data
    data = load_json(json_path)
    folder = os.path.dirname(json_path)
    
    # Find the source image
    image_path = find_image_path(data, folder)
    if not image_path or not os.path.isfile(image_path):
        raise FileNotFoundError(f"Source image not found. Searched in: {folder}")
    
    # Generate output path if not provided
    if not output_path:
        base, ext = os.path.splitext(image_path)
        output_path = f"{base}.annotated{ext}"
    
    print(f"Source image: {image_path}")
    print(f"Output image: {output_path}")
    
    # Load and prepare image
    img = Image.open(image_path).convert("RGBA")
    img_w, img_h = img.size
    print(f"Image size: {img_w}x{img_h}")
    
    # Create drawing context
    draw = ImageDraw.Draw(img)
    font = get_font(font_size)
    
    # Get crop box for coordinate transformation
    crop = data.get("cropBox", {})
    crop_min = crop.get("min", {})
    crop_max = crop.get("max", {})

    # Debug: draw viewport corner markers if available
    vp = data.get("viewportCorners", {})
    if vp and all(k in vp for k in ("TopLeft", "TopRight", "BottomLeft", "BottomRight")):
        tl, tr, bl, br = vp["TopLeft"], vp["TopRight"], vp["BottomLeft"], vp["BottomRight"]
        # Map corner XYZ -> image pixels using (X,Z)
        tlx, tlz = float(tl["x"]), float(tl["z"])  # top z
        trx, trz = float(tr["x"]), float(tr["z"])  # equals tlz
        blx, blz = float(bl["x"]), float(bl["z"])  # bottom z
        brx, brz = float(br["x"]), float(br["z"])  # equals blz

        def to_px(x, z):
            # u from X; v from Z relative to viewport vertical range
            u = (x - tlx) / (trx - tlx) if (trx - tlx) != 0 else 0.0
            v = (z - blz) / (tlz - blz) if (tlz - blz) != 0 else 0.0
            u = max(0.0, min(1.0, u))
            v = max(0.0, min(1.0, v))
            return int(u * img_w), int((1.0 - v) * img_h)

        corners_px = {
            "TopLeft": to_px(tlx, tlz),
            "TopRight": to_px(trx, trz),
            "BottomLeft": to_px(blx, blz),
            "BottomRight": to_px(brx, brz),
        }

        # Draw small red squares at each corner
        marker_size = 14
        red = (255, 0, 0, 255)
        for name, (cx, cy) in corners_px.items():
            x1, y1 = max(0, cx - marker_size//2), max(0, cy - marker_size//2)
            x2, y2 = min(img_w - 1, cx + marker_size//2), min(img_h - 1, cy + marker_size//2)
            draw.rectangle([(x1, y1), (x2, y2)], outline=red, width=3)
            # label
            try:
                draw.text((x1, max(0, y1 - font_size - 2)), name, fill=red, font=font)
            except:
                draw.text((x1, y1), name, fill=red, font=font)
        print("Viewport corner markers (px):", corners_px)
    
    # Process annotations (unless corners_only)
    annotations = data.get("annotations", [])
    if corners_only:
        print("Corners-only mode: skipping annotation boxes.")
    else:
        print(f"Processing {len(annotations)} annotations...")
    
    drawn_count = 0
    for i, ann in enumerate(annotations if not corners_only else []):
        # Try different coordinate sources in order of preference
        bbox = None
        coord_source = ""
        
        # 1. If viewportCorners + bbox2D exist, use viewport mapping from bbox2D (most robust)
        if not bbox and "bbox2D" in ann and data.get("viewportCorners"):
            vp = data.get("viewportCorners", {})
            tl, tr, bl = vp.get("TopLeft"), vp.get("TopRight"), vp.get("BottomLeft")
            if tl and tr and bl:
                tlx, tlz = float(tl["x"]), float(tl["z"])  # top z
                trx = float(tr["x"])                         # right x
                blz = float(bl["z"])                         # bottom z
                b2d = ann["bbox2D"]; mn=b2d["min"]; mx=b2d["max"]
                x1 = float(mn["x"]); y1m = float(mn["y"])  # model
                x2 = float(mx["x"]); y2m = float(mx["y"])  # model

                def map_with(z_from_y_sign: float):
                    z1 = z_from_y_sign * y1m; z2 = z_from_y_sign * y2m
                    u1 = (x1 - tlx) / (trx - tlx) if (trx - tlx) != 0 else 0.0
                    u2 = (x2 - tlx) / (trx - tlx) if (trx - tlx) != 0 else 1.0
                    v1 = (z1 - blz) / (tlz - blz) if (tlz - blz) != 0 else 0.0
                    v2 = (z2 - blz) / (tlz - blz) if (tlz - blz) != 0 else 1.0
                    # keep unclamped for score
                    u1c=max(0,min(1,u1)); u2c=max(0,min(1,u2))
                    v1c=max(0,min(1,v1)); v2c=max(0,min(1,v2))
                    px1=int(u1c*img_w); px2=int(u2c*img_w)
                    # Invert Y mapping for boxes (observed image axis)
                    py1=int(min(v1c,v2c)*img_h); py2=int(max(v1c,v2c)*img_h)
                    spread_in = abs((min(1,max(0,v2))-min(1,max(0,v1))))
                    return (px1,py1,px2,py2), spread_in

                cand_pos, score_pos = map_with(+1.0)
                cand_neg, score_neg = map_with(-1.0)
                bbox = cand_neg if score_neg >= score_pos else cand_pos
                coord_source = "bbox2D(vp-fit)"

        # 3. Try pixelViewport (if present)
        if not bbox and "pixelViewport" in ann:
            pv = ann["pixelViewport"]
            if "min" in pv and "max" in pv:
                mn, mx = pv["min"], pv["max"]
                if all(k in mn for k in ("x","y")) and all(k in mx for k in ("x","y")):
                    x1 = int(mn["x"]); y1 = int(mn["y"])
                    x2 = int(mx["x"]); y2 = int(mx["y"])
                    bbox = (x1,y1,x2,y2)
                    coord_source = "pixelViewport"

        # 4. Try bbox2D (legacy) - lowest priority
        if not bbox and "bbox2D" in ann:
            bbox2d = ann["bbox2D"]
            if "min" in bbox2d and "max" in bbox2d:
                b2d_min = bbox2d["min"]
                b2d_max = bbox2d["max"]
                if "x" in b2d_min and "y" in b2d_min and "x" in b2d_max and "y" in b2d_max:
                    # viewport-based mapping (deterministic)
                    vp = data.get("viewportCorners", {})
                    tl, tr = vp.get("TopLeft"), vp.get("TopRight")
                    bl = vp.get("BottomLeft")
                    if tl and tr and bl:
                        tlx, tlz = float(tl["x"]), float(tl["z"])  # z is vertical
                        trx, trz = float(tr["x"]), float(tr["z"])  # same z
                        blx, blz = float(bl["x"]), float(bl["z"])  # bottom z
                        
                        model_x1 = float(b2d_min["x"])
                        model_y1 = float(b2d_min["y"])  # plugin stores +Y; vertical should be Z
                        model_x2 = float(b2d_max["x"])
                        model_y2 = float(b2d_max["y"])  # plugin stores +Y
                        
                        # For elevations, treat vertical as Z = -Y (per export_log signs)
                        model_z1 = -model_y1
                        model_z2 = -model_y2
                        
                        # Normalize using viewport extents
                        u1 = (model_x1 - tlx) / (trx - tlx)
                        u2 = (model_x2 - tlx) / (trx - tlx)
                        v1 = (model_z1 - blz) / (tlz - blz)  # bottom->top
                        v2 = (model_z2 - blz) / (tlz - blz)
                        
                        # Clamp
                        u1 = max(0.0, min(1.0, u1))
                        u2 = max(0.0, min(1.0, u2))
                        v1 = max(0.0, min(1.0, v1))
                        v2 = max(0.0, min(1.0, v2))
                        
                        # Convert to pixels
                        x1 = int(u1 * img_w)
                        x2 = int(u2 * img_w)
                        y1 = int((1.0 - v2) * img_h)
                        y2 = int((1.0 - v1) * img_h)
                        
                        # Bounds
                        x1 = max(0, min(img_w - 1, x1))
                        x2 = max(0, min(img_w - 1, x2))
                        y1 = max(0, min(img_h - 1, y1))
                        y2 = max(0, min(img_h - 1, y2))
                        
                        bbox = (x1, y1, x2, y2)
                        coord_source = "bbox2D(viewport)"
                    else:
                        # Fallback to previous heuristic if viewport not present
                        model_x1 = float(b2d_min["x"])
                        model_y1 = float(b2d_min["y"])  # elevation Z
                        model_x2 = float(b2d_max["x"])
                        model_y2 = float(b2d_max["y"])  # elevation Z
                        tag_x_min, tag_x_max = -140.0, 136.0
                        tag_y_min, tag_y_max = -23.0, 105.0
                        u1 = (model_x1 - tag_x_min) / (tag_x_max - tag_x_min)
                        u2 = (model_x2 - tag_x_min) / (tag_x_max - tag_x_min)
                        v1 = (model_y1 - tag_y_min) / (tag_y_max - tag_y_min)
                        v2 = (model_y2 - tag_y_min) / (tag_y_max - tag_y_min)
                        u1 = max(0.0, min(1.0, u1)); u2 = max(0.0, min(1.0, u2))
                        v1 = max(0.0, min(1.0, v1)); v2 = max(0.0, min(1.0, v2))
                        x1 = int(u1 * img_w); x2 = int(u2 * img_w)
                        y1 = int((1.0 - v2) * img_h); y2 = int((1.0 - v1) * img_h)
                        x1 = max(0, min(img_w - 1, x1)); x2 = max(0, min(img_w - 1, x2))
                        y1 = max(0, min(img_h - 1, y1)); y2 = max(0, min(img_h - 1, y2))
                        bbox = (x1, y1, x2, y2)
                        coord_source = "bbox2D(heuristic)"
        
        # 3. Try uvBBox (normalized coordinates) as fallback
        if not bbox and "uvBBox" in ann:
            uv_bbox = ann["uvBBox"]
            if "min" in uv_bbox and "max" in uv_bbox:
                uv_min = uv_bbox["min"]
                uv_max = uv_bbox["max"]
                if "u" in uv_min and "v" in uv_min and "u" in uv_max and "v" in uv_max:
                    u1 = float(uv_min["u"])
                    v1 = float(uv_min["v"])
                    u2 = float(uv_max["u"])
                    v2 = float(uv_max["v"])
                    
                    # Use uvBBox even if v coordinates are negative (tags outside crop)
                    # Just clamp them to reasonable bounds
                    if -2 <= u1 <= 3 and -2 <= u2 <= 3 and -2 <= v1 <= 3 and -2 <= v2 <= 3:
                        # Handle negative coordinates by extending the image conceptually
                        x1 = max(0, min(img_w - 1, int(u1 * img_w)))
                        y1 = max(0, min(img_h - 1, int(v1 * img_h)))
                        x2 = max(0, min(img_w - 1, int(u2 * img_w)))
                        y2 = max(0, min(img_h - 1, int(v2 * img_h)))
                        
                        # If coordinates are negative, place at edge
                        if v1 < 0 or v2 < 0:
                            # Tags are above the image, place them at the top
                            y1 = max(0, int(abs(v1) * 50))  # Scale negative coords
                            y2 = max(0, int(abs(v2) * 50))
                            if y1 > y2:
                                y1, y2 = y2, y1
                        
                        bbox = (x1, y1, x2, y2)
                        coord_source = "uvBBox"

        
        
        if not bbox:
            print(f"  Annotation {i+1}: No usable coordinates found")
            continue
        
        # Ensure bbox is valid
        x1, y1, x2, y2 = bbox
        x1, x2 = sorted([x1, x2])
        y1, y2 = sorted([y1, y2])
        
        # Clamp to image bounds
        x1 = max(0, min(img_w - 1, x1))
        x2 = max(0, min(img_w - 1, x2))
        y1 = max(0, min(img_h - 1, y1))
        y2 = max(0, min(img_h - 1, y2))
        
        # Ensure minimum box size for visibility
        min_size = 8  # minimum pixels
        if (x2 - x1) < min_size:
            center_x = (x1 + x2) // 2
            x1 = center_x - min_size // 2
            x2 = center_x + min_size // 2
        
        if (y2 - y1) < min_size:
            center_y = (y1 + y2) // 2
            y1 = center_y - min_size // 2
            y2 = center_y + min_size // 2
        
        # Re-clamp after size adjustment
        x1 = max(0, min(img_w - 1, x1))
        x2 = max(0, min(img_w - 1, x2))
        y1 = max(0, min(img_h - 1, y1))
        y2 = max(0, min(img_h - 1, y2))
        
        # Final check - skip if still too small
        if (x2 - x1) < 2 or (y2 - y1) < 2:
            print(f"  Annotation {i+1}: Box still too small ({x2-x1}x{y2-y1}) using {coord_source}")
            continue
        
        # Draw thick blue rectangle
        blue_color = (0, 102, 255, 255)  # Vivid blue RGBA
        draw.rectangle([(x1, y1), (x2, y2)], outline=blue_color, width=line_width)
        
        # Get annotation text
        text = ann.get("text", "").strip()
        if not text:
            text = ann.get("type", "Tag")
        
        # Draw text label
        if text:
            # Position text above the box, or inside if there's room
            text_x = x1 + 2
            text_y = max(0, y1 - font_size - 2)
            
            # If text would be outside image, put it inside the box
            if text_y < 0:
                text_y = y1 + 2
            
            # Draw text with background for better visibility
            try:
                # Get text size
                bbox_text = draw.textbbox((text_x, text_y), text, font=font)
                text_w = bbox_text[2] - bbox_text[0]
                text_h = bbox_text[3] - bbox_text[1]
                
                # Draw background rectangle
                bg_color = (255, 255, 255, 200)  # Semi-transparent white
                draw.rectangle([(text_x-1, text_y-1), (text_x+text_w+1, text_y+text_h+1)], 
                             fill=bg_color)
                
                # Draw text
                text_color = (0, 0, 0, 255)  # Black
                draw.text((text_x, text_y), text, fill=text_color, font=font)
            except:
                # Fallback if textbbox is not available
                draw.text((text_x, text_y), text, fill=(0, 0, 0, 255), font=font)
        
        drawn_count += 1
        print(f"  Annotation {i+1}: Drew box ({x1},{y1})-({x2},{y2}) with text '{text}' using {coord_source}")
        
        # Debug: show original coordinates
        if coord_source == "bbox2D(viewport)":
            bbox2d = ann["bbox2D"]
            print(f"    Original bbox2D: min({bbox2d['min']['x']:.2f},{bbox2d['min']['y']:.2f}) max({bbox2d['max']['x']:.2f},{bbox2d['max']['y']:.2f})")
            print(f"    Crop Z range: {crop_min.get('z', 0):.2f} to {crop_max.get('z', 0):.2f}")
            # Calculate v coordinates for debugging
            v1 = (bbox2d['min']['y'] - crop_min.get("z", 0)) / (crop_max.get("z", 0) - crop_min.get("z", 0))
            v2 = (bbox2d['max']['y'] - crop_min.get("z", 0)) / (crop_max.get("z", 0) - crop_min.get("z", 0))
            print(f"    Calculated v1={v1:.3f}, v2={v2:.3f}")
    
    # Save the result
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path)
    
    print(f"\nSuccess! Drew {drawn_count} annotations on image.")
    print(f"Saved: {output_path}")
    
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Draw annotation boxes and labels on exported view image")
    parser.add_argument("json_file", help="Path to *.annotations.json file")
    parser.add_argument("-o", "--output", help="Output image path (optional)")
    parser.add_argument("-w", "--line-width", type=int, default=4, help="Rectangle line width (default: 4)")
    parser.add_argument("-s", "--font-size", type=int, default=12, help="Font size for labels (default: 12)")
    parser.add_argument("-c", "--corners-only", action="store_true", help="Render only viewport corner markers, no boxes")
    
    args = parser.parse_args()
    
    try:
        output_path = draw_annotations_on_image(
            args.json_file, 
            args.output, 
            args.line_width, 
            args.font_size,
            args.corners_only
        )
        print(f"\n✓ Complete: {output_path}")
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
