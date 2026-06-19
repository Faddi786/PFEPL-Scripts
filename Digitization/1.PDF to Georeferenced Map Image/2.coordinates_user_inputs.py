import cv2
import pytesseract
import numpy as np
import re
import os

# -------------------------------
# INPUT
# -------------------------------
image_path = "outside_cropped_MH80.png"
output_txt = "boundary_coordinates_MH80.txt"
debug_dir = "debug_boundaries"
os.makedirs(debug_dir, exist_ok=True)

STEP = 0.0416667

img = cv2.imread(image_path)
h, w = img.shape[:2]

# -------------------------------
# BOUNDARY STRIPS
# -------------------------------
STRIP_THICKNESS = int(0.12 * min(h, w))

BOUNDARIES = {
    "top":    img[0:STRIP_THICKNESS, :],
    "bottom": img[h-STRIP_THICKNESS:h, :],
    "left":   img[:, 0:STRIP_THICKNESS],
    "right":  img[:, w-STRIP_THICKNESS:w]
}

# -------------------------------
# PREPROCESS
# -------------------------------
def preprocess(img, name):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(2.5, (8, 8))
    enhanced = clahe.apply(gray)
    blur = cv2.GaussianBlur(enhanced, (3, 3), 0)
    _, thresh = cv2.threshold(
        blur, 0, 255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )
    cv2.imwrite(f"{debug_dir}/{name}_processed.png", thresh)
    return thresh

# -------------------------------
# DMS → DECIMAL
# -------------------------------
def dms_to_decimal(match):
    deg = int(match.group(1))
    min_ = int(match.group(2))
    sec = int(match.group(3)) if match.group(3) else 0
    direction = match.group(4)

    dec = deg + min_ / 60 + sec / 3600
    if direction in ["S", "W"]:
        dec *= -1
    return dec

DMS_REGEX = r"(\d+)[°\s]+(\d+)'?\s*(\d+)?\"?\s*([NSEW])"

# -------------------------------
# OCR + PARSE
# -------------------------------
results = {}

for side, strip in BOUNDARIES.items():

    if side in ["left", "right"]:
        strip = cv2.rotate(strip, cv2.ROTATE_90_CLOCKWISE)

    cv2.imwrite(f"{debug_dir}/{side}_strip.png", strip)
    processed = preprocess(strip, side)

    text = pytesseract.image_to_string(processed, config="--psm 11")

    print(f"\n---- RAW OCR ({side.upper()}) ----")
    print(text)

    values = []
    for match in re.finditer(DMS_REGEX, text):
        values.append(dms_to_decimal(match))

    if side in ["top", "bottom"]:
        values.sort()
    else:
        values.sort(reverse=True)

    results[side.upper()] = values

# -------------------------------
# INTERACTIVE VALUE HANDLING
# -------------------------------
def interactive_fix(label, values):
    print(f"\n📌 {label}")
    print("Captured values:")
    for i, v in enumerate(values):
        print(f"  [{i}] {v:.8f}")

    # Case 1: less than 4 → old behaviour
    if len(values) < 4:
        print("⚠️ Less than 4 values detected. Manual reconstruction required.")
        idx = int(input("Select index to use as BASE value: "))
        base_val = values[idx]

        base_pos = int(input("What should be its correct index (0–3)? "))
        start = base_val - base_pos * STEP
        return [start + i * STEP for i in range(4)]

    # Case 2: exactly 4 → confirm or edit
    if len(values) == 4:
        choice = input("Confirm values? (C = confirm / E = edit): ").strip().upper()
        if choice == "C":
            return values

        print("\n✏️ Editing mode")
        idx = int(input("Which index value is correct? (0–3): "))
        correct_val = values[idx]

        correct_pos = int(input(
            "What should be its correct index (0–3)? "
        ))

        start = correct_val - correct_pos * STEP
        fixed = [start + i * STEP for i in range(4)]

        print("✅ Recalculated values:")
        for i, v in enumerate(fixed):
            print(f"  [{i}] {v:.8f}")

        return fixed

    # Safety fallback (should not occur)
    print("⚠️ More than 4 values detected. Using first 4.")
    return values[:4]

# -------------------------------
# GROUP VALUES
# -------------------------------
horizontal_vals = sorted(set(results["TOP"]) | set(results["BOTTOM"]))
vertical_vals   = sorted(set(results["LEFT"]) | set(results["RIGHT"]))

horizontal_vals = interactive_fix("HORIZONTAL (E)", horizontal_vals)
vertical_vals   = interactive_fix("VERTICAL (N)", vertical_vals)

# -------------------------------
# SAVE OUTPUT
# -------------------------------
with open(output_txt, "w") as f:
    f.write("HORIZONTAL (E):\n")
    for v in horizontal_vals:
        f.write(f"{v:.8f}\n")

    f.write("\nVERTICAL (N):\n")
    for v in vertical_vals:
        f.write(f"{v:.8f}\n")

print("\n✅ Boundary coordinates finalized.")
print("Saved to:", output_txt)
print("Debug images in:", debug_dir)
