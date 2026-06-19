import argparse
import cv2
import numpy as np
from skimage.morphology import skeletonize  # Optional: pip install scikit-image
import warnings
warnings.filterwarnings("ignore")

def load_image(image_path):
    """Load image and convert to necessary formats."""
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not load image: {image_path}")
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return img, hsv, gray

def extract_by_color(hsv, lower_color, upper_color, img_shape):
    """Extract line by HSV color range."""
    mask = cv2.inRange(hsv, lower_color, upper_color)
    # Morphological ops to clean up
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    # Skeletonize
    mask_bin = mask > 0
    skeleton = skeletonize(mask_bin).astype(np.uint8) * 255
    return skeleton

def extract_by_width(gray, min_width, max_width):
    """Extract lines by thickness (width in pixels)."""
    # Edge detection
    edges = cv2.Canny(gray, 50, 150)
    # Dilate to approximate width
    kernel_size = int(max_width)
    kernel = np.ones((kernel_size, kernel_size), np.uint8)
    dilated = cv2.dilate(edges, kernel, iterations=1)
    # Erode back and filter by area (proxy for width)
    eroded = cv2.erode(dilated, kernel, iterations=1)
    # Threshold to keep only thick enough regions
    contours, _ = cv2.findContours(eroded, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    width_mask = np.zeros_like(gray)
    for cnt in contours:
        area = cv2.contourArea(cnt)
        perimeter = cv2.arcLength(cnt, True)
        if perimeter > 0:
            avg_width = area / perimeter  # Rough width estimate
            if min_width <= avg_width <= max_width:
                cv2.drawContours(width_mask, [cnt], -1, 255, -1)
    # Skeletonize
    mask_bin = width_mask > 0
    skeleton = skeletonize(mask_bin).astype(np.uint8) * 255
    return skeleton

def extract_by_points(img_shape, points, tolerance=5):
    """Extract line by fitting to provided points (list of (x,y) tuples)."""
    if len(points) < 2:
        raise ValueError("At least 2 points required.")
    pts = np.array(points, dtype=np.float32)
    # Fit line: vx, vy, x0, y0 (direction and point)
    [vx, vy, x0, y0] = cv2.fitLine(pts, cv2.DIST_L2, 0, 0.01, 0.01)
    # Create mask: pixels within tolerance distance to line
    mask = np.zeros(img_shape[:2], np.uint8)
    y1 = int((-x0 * vy / vx) + y0) if vx != 0 else 0
    x1 = int((-y0 * vx / vy) + x0) if vy != 0 else 0
    # Extend line across image bounds
    x2 = int((img_shape[1] - x0) * vy / vx + y0) if vx != 0 else img_shape[1]
    y2 = int((img_shape[0] - y0) * vx / vy + x0) if vy != 0 else img_shape[0]
    # Distance-based rasterization (simple perpendicular distance)
    for y in range(img_shape[0]):
        for x in range(img_shape[1]):
            dist = abs((vy * (x - x0) - vx * (y - y0)) / np.sqrt(vx**2 + vy**2))
            if dist <= tolerance:
                mask[y, x] = 255
    # Skeletonize (already thin)
    return mask

def save_output(extracted_mask, output_path):
    """Save the extracted line as a white-on-black image."""
    cv2.imwrite(output_path, extracted_mask)
    print(f"Extracted line saved to: {output_path}")
    # Optional: Print polyline coords (simplified contour)
    contours, _ = cv2.findContours(extracted_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        main_contour = max(contours, key=cv2.contourArea)
        coords = main_contour.reshape(-1, 2).tolist()
        print("Approximate polyline coordinates (x,y):")
        for pt in coords[:20]:  # First 20 points for brevity
            print(pt)

def main():
    parser = argparse.ArgumentParser(description="Extract a specific line from a map image.")
    parser.add_argument("image_path", help="Path to input image (e.g., map.jpg)")
    parser.add_argument("mode", choices=["color", "width", "points"], help="Extraction mode")
    parser.add_argument("output_path", help="Path for output image (e.g., extracted_line.png)")
    
    # Color mode args
    parser.add_argument("--lower-hsv", nargs=3, type=int, metavar=("H", "S", "V"),
                        help="Lower HSV bounds (e.g., 100 50 50 for green)")
    parser.add_argument("--upper-hsv", nargs=3, type=int, metavar=("H", "S", "V"),
                        help="Upper HSV bounds (e.g., 130 255 255 for green)")
    
    # Width mode args
    parser.add_argument("--min-width", type=int, default=1, help="Min line thickness (pixels)")
    parser.add_argument("--max-width", type=int, default=10, help="Max line thickness (pixels)")
    
    # Points mode args
    parser.add_argument("--points", nargs="+", type=int, help="Points as x1 y1 x2 y2 ... (flattened)")
    
    args = parser.parse_args()
    
    img, hsv, gray = load_image(args.image_path)
    extracted = None
    
    if args.mode == "color":
        if not args.lower_hsv or not args.upper_hsv:
            raise ValueError("Provide --lower-hsv and --upper-hsv for color mode")
        lower = np.array(args.lower_hsv)
        upper = np.array(args.upper_hsv)
        extracted = extract_by_color(hsv, lower, upper, img.shape)
    elif args.mode == "width":
        extracted = extract_by_width(gray, args.min_width, args.max_width)
    elif args.mode == "points":
        if not args.points or len(args.points) < 4:
            raise ValueError("Provide at least 2 points (--points x1 y1 x2 y2 ...)")
        points = [(args.points[i], args.points[i+1]) for i in range(0, len(args.points), 2)]
        extracted = extract_by_points(img.shape, points)
    
    if extracted is not None:
        save_output(extracted, args.output_path)
    else:
        print("Extraction failed.")

if __name__ == "__main__":
    main()