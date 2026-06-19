import cv2
import numpy as np

# --------------------------------------------------
# INPUT / OUTPUT
# --------------------------------------------------
input_image  = "outside_cropped_MH80.png"
output_image = "inside_cropped_MH80.png"

# --------------------------------------------------
# PARAMETERS (TUNED FOR DASHED BROWN / PURPLE BORDER)
# --------------------------------------------------
LOWER_BORDER = np.array([5, 40, 40])     # brown + purplish
UPPER_BORDER = np.array([25, 255, 220])

KERNEL_SIZE = 7

# Coarse detection rules
BORDER_PIXEL_RATIO = 0.02    # still considered border
CONSECUTIVE_CLEAR  = 12      # must disappear consistently

# Recursive refinement
REFINE_LEVELS = 3            # 3 levels → <1 px accuracy

# --------------------------------------------------
# UTILITY FUNCTIONS
# --------------------------------------------------
def has_border_pixels(region, ratio_thresh=0.01):
    if region.size == 0:
        return False
    return (np.count_nonzero(region) / region.size) > ratio_thresh


# --------------------------------------------------
# REFINEMENT FUNCTIONS
# --------------------------------------------------
def refine_left_edge(mask, coarse_x, top, bottom, levels):
    left = coarse_x - 1
    right = coarse_x

    for _ in range(levels):
        if right - left <= 1:
            break
        mid = (left + right) // 2
        region = mask[top:bottom, mid:right]
        if has_border_pixels(region):
            left = mid
        else:
            right = mid
    return right


def refine_right_edge(mask, coarse_x, top, bottom, levels):
    left = coarse_x
    right = coarse_x + 1

    for _ in range(levels):
        if right - left <= 1:
            break
        mid = (left + right) // 2
        region = mask[top:bottom, left:mid]
        if has_border_pixels(region):
            right = mid
        else:
            left = mid
    return left


def refine_top_edge(mask, coarse_y, left, right, levels):
    top = coarse_y - 1
    bottom = coarse_y

    for _ in range(levels):
        if bottom - top <= 1:
            break
        mid = (top + bottom) // 2
        region = mask[mid:bottom, left:right]
        if has_border_pixels(region):
            top = mid
        else:
            bottom = mid
    return bottom


def refine_bottom_edge(mask, coarse_y, left, right, levels):
    top = coarse_y
    bottom = coarse_y + 1

    for _ in range(levels):
        if bottom - top <= 1:
            break
        mid = (top + bottom) // 2
        region = mask[top:mid, left:right]
        if has_border_pixels(region):
            bottom = mid
        else:
            top = mid
    return top


# --------------------------------------------------
# 1. Read image
# --------------------------------------------------
img = cv2.imread(input_image)
if img is None:
    raise RuntimeError("Failed to read input image")

h, w = img.shape[:2]

# --------------------------------------------------
# 2. Detect dashed brown / purple border
# --------------------------------------------------
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
mask = cv2.inRange(hsv, LOWER_BORDER, UPPER_BORDER)

# --------------------------------------------------
# 3. Close dashed gaps (controlled)
# --------------------------------------------------
kernel = cv2.getStructuringElement(
    cv2.MORPH_RECT, (KERNEL_SIZE, KERNEL_SIZE)
)
mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)

# --------------------------------------------------
# 4. Outer bounding box of border
# --------------------------------------------------
ys, xs = np.where(mask > 0)
if len(xs) == 0:
    raise RuntimeError("Border not detected")

left, right = xs.min(), xs.max()
top, bottom = ys.min(), ys.max()

# --------------------------------------------------
# 5. COARSE inner edge detection (column/row level)
# --------------------------------------------------
def coarse_left():
    clear = 0
    for x in range(left, right):
        col = mask[top:bottom, x]
        if np.count_nonzero(col) / len(col) < BORDER_PIXEL_RATIO:
            clear += 1
            if clear >= CONSECUTIVE_CLEAR:
                return x - CONSECUTIVE_CLEAR
        else:
            clear = 0
    return left


def coarse_right():
    clear = 0
    for x in range(right, left, -1):
        col = mask[top:bottom, x]
        if np.count_nonzero(col) / len(col) < BORDER_PIXEL_RATIO:
            clear += 1
            if clear >= CONSECUTIVE_CLEAR:
                return x + CONSECUTIVE_CLEAR
        else:
            clear = 0
    return right


def coarse_top():
    clear = 0
    for y in range(top, bottom):
        row = mask[y, left:right]
        if np.count_nonzero(row) / len(row) < BORDER_PIXEL_RATIO:
            clear += 1
            if clear >= CONSECUTIVE_CLEAR:
                return y - CONSECUTIVE_CLEAR
        else:
            clear = 0
    return top


def coarse_bottom():
    clear = 0
    for y in range(bottom, top, -1):
        row = mask[y, left:right]
        if np.count_nonzero(row) / len(row) < BORDER_PIXEL_RATIO:
            clear += 1
            if clear >= CONSECUTIVE_CLEAR:
                return y + CONSECUTIVE_CLEAR
        else:
            clear = 0
    return bottom


coarse_l = coarse_left()
coarse_r = coarse_right()
coarse_t = coarse_top()
coarse_b = coarse_bottom()

# --------------------------------------------------
# 6. RECURSIVE SUB-COLUMN / SUB-ROW REFINEMENT
# --------------------------------------------------
inner_left = refine_left_edge(
    mask, coarse_l, top, bottom, REFINE_LEVELS
)

inner_right = refine_right_edge(
    mask, coarse_r, top, bottom, REFINE_LEVELS
)

inner_top = refine_top_edge(
    mask, coarse_t, left, right, REFINE_LEVELS
)

inner_bottom = refine_bottom_edge(
    mask, coarse_b, left, right, REFINE_LEVELS
)

# --------------------------------------------------
# 7. Clamp and crop
# --------------------------------------------------
inner_left   = max(0, inner_left)
inner_top    = max(0, inner_top)
inner_right  = min(w, inner_right)
inner_bottom = min(h, inner_bottom)

inner_crop = img[inner_top:inner_bottom, inner_left:inner_right]

# --------------------------------------------------
# 8. Save result
# --------------------------------------------------
cv2.imwrite(output_image, inner_crop)

print("✅ Border fully removed with recursive refinement")
print("Saved as:", output_image)
