import cv2
import matplotlib.pyplot as plt
import string
import os
import json

# -------------------------------
# CONFIG
# -------------------------------
image_path = "inside_cropped_MH80.png"
DIVISIONS = 4  # 4x4 grid → 25 points

output_dir = "grid_output"
os.makedirs(output_dir, exist_ok=True)

output_image_path = os.path.join(output_dir, "grid_labeled_points.png")
output_json_path = os.path.join(output_dir, "grid_points_with_latlon.json")

# -------------------------------
# MAP COORDINATES (INPUT)
# -------------------------------
# (LATITUDE, LONGITUDE)
# (NORTH, EAST)

# MAP_CORNERS = {
#     "a": (19.250, 72.750),   # top-left 45'0" 0.75
#     "e": (19.250, 72.875),   # top-right 52'30" 0.875
#     "u": (19.125, 72.750),   # bottom-left
#     "y": (19.125, 72.875)    # bottom-right
# }

# ----------------------------------
# READ MAP_CORNERS FROM TXT
# ----------------------------------
map_corners_file = "map_corners.txt"

namespace = {}
with open(map_corners_file, "r") as f:
    exec(f.read(), {}, namespace)

MAP_CORNERS = namespace["MAP_CORNERS"]

# Example usage
top_left = MAP_CORNERS["a"]
top_right = MAP_CORNERS["e"]
bottom_left = MAP_CORNERS["u"]
bottom_right = MAP_CORNERS["y"]

# -------------------------------
# LOAD IMAGE
# -------------------------------
img = cv2.imread(image_path)
img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
h, w = img.shape[:2]

# -------------------------------
# GRID STEPS (PIXELS)
# -------------------------------
x_steps = [int(w * i / DIVISIONS) for i in range(DIVISIONS + 1)]
y_steps = [int(h * i / DIVISIONS) for i in range(DIVISIONS + 1)]

# -------------------------------
# DRAW GRID
# -------------------------------
grid_img = img_rgb.copy()

for x in x_steps:
    cv2.line(grid_img, (x, 0), (x, h), (255, 0, 0), 2)

for y in y_steps:
    cv2.line(grid_img, (0, y), (w, y), (255, 0, 0), 2)

# -------------------------------
# EXTRACT CORNER COORDINATES
# -------------------------------
lat_a, lon_a = MAP_CORNERS["a"]
lat_e, lon_e = MAP_CORNERS["e"]
lat_u, lon_u = MAP_CORNERS["u"]
lat_y, lon_y = MAP_CORNERS["y"]

# Longitude (horizontal interpolation)
d_lon_top = (lon_e - lon_a) / DIVISIONS
d_lon_bottom = (lon_y - lon_u) / DIVISIONS

# Latitude (vertical interpolation)
d_lat_left = (lat_u - lat_a) / DIVISIONS
d_lat_right = (lat_y - lat_e) / DIVISIONS

# -------------------------------
# LABEL POINTS + INTERPOLATE LAT/LON
# -------------------------------
letters = list(string.ascii_lowercase)
idx = 0
points = {}

for row, py in enumerate(y_steps):
    for col, px in enumerate(x_steps):

        label = letters[idx]

        # ---- Image coordinates ----
        img_x = int(px)
        img_y = int(py)

        # ---- Longitude interpolation (left → right) ----
        lon_top = lon_a + d_lon_top * col
        lon_bottom = lon_u + d_lon_bottom * col
        longitude = lon_top + (lon_bottom - lon_top) * (row / DIVISIONS)

        # ---- Latitude interpolation (top → bottom) ----
        lat_left = lat_a + d_lat_left * row
        lat_right = lat_e + d_lat_right * row
        latitude = lat_left + (lat_right - lat_left) * (col / DIVISIONS)

        points[label] = {
            "image": {
                "x": img_x,
                "y": img_y
            },
            "map": {
                "latitude": round(latitude, 6),
                "longitude": round(longitude, 6)
            }
        }

        # Draw point + label
        cv2.circle(grid_img, (img_x, img_y), 4, (0, 255, 0), -1)
        cv2.putText(
            grid_img,
            label,
            (img_x + 6, img_y - 6),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 0),
            2,
            cv2.LINE_AA
        )

        idx += 1

# -------------------------------
# SAVE IMAGE
# -------------------------------
cv2.imwrite(output_image_path, cv2.cvtColor(grid_img, cv2.COLOR_RGB2BGR))

# -------------------------------
# SAVE JSON
# -------------------------------
json_data = {
    "image": os.path.basename(image_path),
    "width": w,
    "height": h,
    "divisions": DIVISIONS,
    "coordinate_system": "latitude_longitude_decimal_degrees",
    "map_corners": MAP_CORNERS,
    "points": points
}

with open(output_json_path, "w", encoding="utf-8") as f:
    json.dump(json_data, f, indent=4)

# -------------------------------
# DISPLAY
# -------------------------------
plt.figure(figsize=(8, 6))
plt.imshow(grid_img)
plt.title("4×4 Grid with Image + Latitude/Longitude Coordinates")
plt.axis("off")
plt.show()

print(f"\nSaved image → {output_image_path}")
print(f"Saved JSON  → {output_json_path}")
