import cv2
import numpy as np
from pdf2image import convert_from_path

# --------------------------------------------------
# PARAMETERS
# --------------------------------------------------
FRAME_WIDTH  = 6670
FRAME_HEIGHT = 6650

OUTER_PAD = 70
INNER_PAD = 0

TILT_THRESHOLD_DEG = 0.5

pdf_path = "MH_80.pdf"
output_path = "outside_cropped_MH80.png"

# --------------------------------------------------
# 1. Convert PDF to image
# --------------------------------------------------
page = convert_from_path(pdf_path, dpi=300)[0]
img = cv2.cvtColor(np.array(page), cv2.COLOR_RGB2BGR)

# --------------------------------------------------
# 2. Detect brown dashed border
# --------------------------------------------------
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

lower_brown = np.array([5, 50, 50])
upper_brown = np.array([25, 255, 200])

mask = cv2.inRange(hsv, lower_brown, upper_brown)

# Clean gaps in dashed line
kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)

# --------------------------------------------------
# 3. Detect tilt angle using Hough
# --------------------------------------------------
# edges = cv2.Canny(mask, 50, 150, apertureSize=3)

# lines = cv2.HoughLines(edges, 1, np.pi / 180, 250)

# angles = []
# if lines is not None:
#     for line in lines[:20]:
#         rho, theta = line[0]
#         angle = (theta - np.pi / 2) * 180 / np.pi
#         angles.append(angle)

# tilt_deg = np.median(angles) if angles else 0.0
# print(f"Tilt detected: {tilt_deg:.3f} degrees")

# --------------------------------------------------
# 3. Detect tilt angle (IGNORE vertical lines)
# --------------------------------------------------
edges = cv2.Canny(mask, 50, 150, apertureSize=3)
lines = cv2.HoughLines(edges, 1, np.pi / 180, 250)

angles = []

if lines is not None:
    for line in lines:
        rho, theta = line[0]

        # Convert to line angle (not normal angle)
        line_angle = (theta - np.pi / 2) * 180 / np.pi

        # KEEP ONLY near-horizontal lines (true skew range)
        if -10 <= line_angle <= 10:
            angles.append(line_angle)

# Robust tilt
tilt_deg = np.median(angles) if angles else 0.0
print(f"Tilt detected: {tilt_deg:.3f} degrees")

# --------------------------------------------------
# 4. Deskew ONLY if needed
# --------------------------------------------------
if abs(tilt_deg) >= TILT_THRESHOLD_DEG:
    print("Deskewing image...")
    h, w = img.shape[:2]
    center = (w // 2, h // 2)

    M = cv2.getRotationMatrix2D(center, tilt_deg, 1.0)
    img = cv2.warpAffine(
        img, M, (w, h),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_REPLICATE
    )
else:
    print("Image is straight. Skipping deskew.")

# --------------------------------------------------
# 5. OLD LOGIC: find top-left of frame
# --------------------------------------------------
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
mask = cv2.inRange(hsv, lower_brown, upper_brown)

ys, xs = np.where(mask > 0)

if len(xs) == 0:
    raise RuntimeError("Frame not detected")

tl_x = xs.min()
tl_y = ys.min()

# --------------------------------------------------
# 6. Fixed-size crop (unchanged logic)
# --------------------------------------------------
h_img, w_img = img.shape[:2]

x_start = max(0, tl_x - OUTER_PAD)
y_start = max(0, tl_y - OUTER_PAD)

x_end = min(w_img, tl_x + FRAME_WIDTH  + OUTER_PAD)
y_end = min(h_img, tl_y + FRAME_HEIGHT + OUTER_PAD)

cropped = img[
    y_start + INNER_PAD : y_end - INNER_PAD,
    x_start + INNER_PAD : x_end - INNER_PAD
]

# --------------------------------------------------
# 7. Save result
# --------------------------------------------------
cv2.imwrite(output_path, cropped)
print("Frame cropped and saved as:", output_path)
