# ----------------------------------
# INPUT FILE (from previous step)
# ----------------------------------
input_txt = "boundary_coordinates_MH80.txt"

# ----------------------------------
# OUTPUT FILE (for next script)
# ----------------------------------
output_txt = "map_corners.txt"

# ----------------------------------
# READ INPUT
# ----------------------------------
with open(input_txt, "r") as f:
    lines = f.readlines()

horizontal_vals = []
vertical_vals = []

mode = None
for line in lines:
    line = line.strip()

    if line.startswith("HORIZONTAL"):
        mode = "H"
        continue
    elif line.startswith("VERTICAL"):
        mode = "V"
        continue
    elif not line:
        continue

    value = float(line)

    if mode == "H":
        horizontal_vals.append(value)
    elif mode == "V":
        vertical_vals.append(value)

# ----------------------------------
# SORT VALUES
# ----------------------------------
horizontal_vals.sort()
vertical_vals.sort()

min_E, max_E = horizontal_vals[0], horizontal_vals[-1]
min_N, max_N = vertical_vals[0], vertical_vals[-1]

# ----------------------------------
# DEFINE CORNERS (lat, lon)
# ----------------------------------
corners = {
    "a": (max_N, min_E),  # 4th Corner: top-left
    "e": (max_N, max_E),  # 3rd Corner: top-right
    "u": (min_N, min_E),  # 1st Corner: bottom-left
    "y": (min_N, max_E),  # 2nd Corner: bottom-right
}

# ----------------------------------
# WRITE OUTPUT IN SCRIPT-READY FORMAT
# ----------------------------------
with open(output_txt, "w") as f:
    f.write("MAP_CORNERS = {\n")
    f.write(f'    "a": ({corners["a"][0]:.8f}, {corners["a"][1]:.8f}),   # top-left\n')
    f.write(f'    "e": ({corners["e"][0]:.8f}, {corners["e"][1]:.8f}),   # top-right\n')
    f.write(f'    "u": ({corners["u"][0]:.8f}, {corners["u"][1]:.8f}),   # bottom-left\n')
    f.write(f'    "y": ({corners["y"][0]:.8f}, {corners["y"][1]:.8f})    # bottom-right\n')
    f.write("}\n")

print("MAP_CORNERS saved to:", output_txt)



# import re

# # ----------------------------------
# # INPUT
# # ----------------------------------
# input_txt = "outside_cropped_MH80_boundary_coordinates.txt"

# # ----------------------------------
# # READ FILE
# # ----------------------------------
# with open(input_txt, "r") as f:
#     content = f.read()

# # ----------------------------------
# # PARSE VALUES
# # ----------------------------------
# horizontal_vals = []
# vertical_vals = []

# current = None
# for line in content.splitlines():
#     line = line.strip()

#     if line.startswith("HORIZONTAL"):
#         current = "H"
#         continue
#     elif line.startswith("VERTICAL"):
#         current = "V"
#         continue
#     elif not line:
#         continue

#     value = float(line)

#     if current == "H":
#         horizontal_vals.append(value)
#     elif current == "V":
#         vertical_vals.append(value)

# # ----------------------------------
# # SORT
# # ----------------------------------
# horizontal_vals.sort()
# vertical_vals.sort()

# # ----------------------------------
# # EXTREME VALUES
# # ----------------------------------
# min_E = horizontal_vals[0]
# max_E = horizontal_vals[-1]

# min_N = vertical_vals[0]
# max_N = vertical_vals[-1]

# # ----------------------------------
# # COMPUTE CORNERS
# # (latitude, longitude) = (N, E)
# # ----------------------------------
# corners = {
#     "TOP_LEFT":     (max_N, min_E),
#     "TOP_RIGHT":    (max_N, max_E),
#     "BOTTOM_LEFT":  (min_N, min_E),
#     "BOTTOM_RIGHT": (min_N, max_E),
# }

# # ----------------------------------
# # OUTPUT
# # ----------------------------------
# print("\nComputed Extreme Corners:\n")
# for name, (lat, lon) in corners.items():
#     print(f"{name}: ({lat:.8f}, {lon:.8f})")
