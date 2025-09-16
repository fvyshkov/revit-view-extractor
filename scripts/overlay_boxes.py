#!/usr/bin/env python3
"""
Overlay thick blue bounding boxes onto an exported view image using
annotations JSON produced by the Revit add-in.

Coordinates are mapped from model space to pixel space using the view's
crop box, following the same logic as in the C# exporter:
  u = (x - crop.min.x) / (crop.max.x - crop.min.x)
  v = (y - crop.min.y) / (crop.max.y - crop.min.y)
  px = round(u * imgW)
  py = imgH - round(v * imgH)
"""

import argparse
import json
import os
import sys
from typing import Dict, Any, Tuple, Optional

try:
    from PIL import Image, ImageDraw
except ImportError:
    print("ERROR: Pillow (PIL) is not installed. Install with: python3 -m pip install pillow", file=sys.stderr)
    sys.exit(1)


def find_image_path(preferred_path: Optional[str], folder: str, view_name: Optional[str]) -> Optional[str]:
    # If preferred path exists, use it.
    if preferred_path and os.path.isfile(preferred_path):
        return preferred_path

    # Otherwise, search for a likely PNG in the folder.
    pngs = [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith(".png")]
    if not pngs:
        return None

    # Prefer files that include the view name if provided.
    if view_name:
        lowered = view_name.lower()
        candidates = [p for p in pngs if lowered in os.path.basename(p).lower()]
        if candidates:
            # Avoid selecting an already-boxed image by preferring names without .boxes.
            non_boxed = [p for p in candidates if ".boxes." not in os.path.basename(p).lower()]
            return (non_boxed or candidates)[0]

    # Fallback: first PNG that is not already a .boxes.png
    non_boxed = [p for p in pngs if ".boxes." not in os.path.basename(p).lower()]
    return (non_boxed or pngs)[0]


def load_json(path: str) -> Dict[str, Any]:
    # Use utf-8-sig to gracefully handle BOM if present
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def map_to_pixels(x: float, y: float, crop_min: Tuple[float, float], crop_max: Tuple[float, float], img_w: int, img_h: int) -> Tuple[int, int]:
    # Guard against zero-size crop
    dx = max(1e-9, (crop_max[0] - crop_min[0]))
    dy = max(1e-9, (crop_max[1] - crop_min[1]))
    u = (x - crop_min[0]) / dx
    v = (y - crop_min[1]) / dy
    px = int(round(u * img_w))
    py = img_h - int(round(v * img_h))
    return px, py


def clamp_box(px1: int, py1: int, px2: int, py2: int, img_w: int, img_h: int) -> Tuple[int, int, int, int]:
    x1, x2 = sorted((px1, px2))
    y1, y2 = sorted((py1, py2))
    x1 = max(0, min(img_w - 1, x1))
    x2 = max(0, min(img_w - 1, x2))
    y1 = max(0, min(img_h - 1, y1))
    y2 = max(0, min(img_h - 1, y2))
    return x1, y1, x2, y2


def overlay_boxes(json_path: str, image_path: Optional[str], out_path: Optional[str], line_width: int = 8) -> str:
    data = load_json(json_path)

    folder = os.path.dirname(json_path)
    view_name = data.get("viewName")
    json_image_path = data.get("imagePath")

    # Resolve image path
    resolved_image = image_path
    if not resolved_image:
        # Convert Windows path to posix if needed
        if isinstance(json_image_path, str):
            candidate = json_image_path
            if os.name != "nt":
                # Try to map known prefix "C:\\Mac\\Home" to current $HOME
                candidate = candidate.replace("C:\\Mac\\Home", os.path.expanduser("~")).replace("\\", "/")
            if os.path.isfile(candidate):
                resolved_image = candidate
        if not resolved_image:
            resolved_image = find_image_path(None, folder, view_name)

    if not resolved_image or not os.path.isfile(resolved_image):
        raise FileNotFoundError(f"Image file not found. Resolved: {resolved_image}")

    # Output path
    if not out_path:
        base, ext = os.path.splitext(resolved_image)
        out_path = f"{base}.boxes{ext}"

    # Load image
    img = Image.open(resolved_image).convert("RGBA")
    img_w, img_h = img.size

    # Crop box from JSON
    crop = data.get("cropBox") or {}
    crop_min = crop.get("min") or {}
    crop_max = crop.get("max") or {}
    if not all(k in crop_min for k in ("x", "y")) or not all(k in crop_max for k in ("x", "y")):
        raise ValueError("cropBox with min/max x,y is required in the annotations JSON")

    cmin = (float(crop_min["x"]), float(crop_min["y"]))
    cmax = (float(crop_max["x"]), float(crop_max["y"]))

    draw = ImageDraw.Draw(img)
    ann = data.get("annotations", [])
    for a in ann:
        bbox = a.get("bbox") or {}
        bmin = bbox.get("min") or {}
        bmax = bbox.get("max") or {}
        if not all(k in bmin for k in ("x", "y")) or not all(k in bmax for k in ("x", "y")):
            continue

        x1, y1 = float(bmin["x"]), float(bmin["y"])
        x2, y2 = float(bmax["x"]), float(bmax["y"])

        px1, py1 = map_to_pixels(x1, y1, cmin, cmax, img_w, img_h)
        px2, py2 = map_to_pixels(x2, y2, cmin, cmax, img_w, img_h)

        x1c, y1c, x2c, y2c = clamp_box(px1, py1, px2, py2, img_w, img_h)

        # Draw thick blue rectangle (RGBA: a vivid blue)
        draw.rectangle([(x1c, y1c), (x2c, y2c)], outline=(0, 102, 255, 255), width=line_width)

    # Save output
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.save(out_path)
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Overlay thick blue boxes onto an exported view image using annotations JSON.")
    parser.add_argument("--input-json", required=True, help="Path to *.annotations.json")
    parser.add_argument("--image", required=False, default=None, help="Path to the source PNG (optional)")
    parser.add_argument("--out", required=False, default=None, help="Path to save the output image (optional)")
    parser.add_argument("--line-width", type=int, default=8, help="Rectangle outline thickness in pixels")
    args = parser.parse_args()

    out_path = overlay_boxes(args.input_json, args.image, args.out, line_width=args.line_width)
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    main()


