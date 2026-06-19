import pandas as pd
import numpy as np
from scipy.interpolate import interp1d

# -------------------------
# File paths
# -------------------------
input_file = "input.xlsx"
output_file = "output_ARF.xlsx"

# -------------------------
# Read sheets
# -------------------------
arf_scale_df = pd.read_excel(input_file, sheet_name="ARF_Scale")
data_df = pd.read_excel(input_file, sheet_name="Data")

# -------------------------
# Extract x and y from ARF_Scale
# -------------------------
x_scale = arf_scale_df.iloc[:, 0].values   # Area (SQ.KM)
y_scale = arf_scale_df.iloc[:, 1].values   # ARF

# -------------------------
# Extract x (Area) from Data sheet (3rd column)
# -------------------------
x_query_raw = data_df.iloc[:, 2].values

# -------------------------
# Clamp query values to scale range
# -------------------------
x_query_clamped = np.clip(
    x_query_raw,
    x_scale.min(),
    x_scale.max()
)

# -------------------------
# Linear interpolation
# -------------------------
interpolator = interp1d(
    x_scale,
    y_scale,
    kind="linear"
)

y_interpolated = interpolator(x_query_clamped)

# -------------------------
# Write result to 6th column
# -------------------------
# If column exists, overwrite; otherwise create
if data_df.shape[1] >= 6:
    data_df.iloc[:, 5] = y_interpolated
else:
    data_df.insert(5, "ARF", y_interpolated)

# -------------------------
# Write output Excel
# -------------------------
with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
    arf_scale_df.to_excel(writer, sheet_name="ARF_Scale", index=False)
    data_df.to_excel(writer, sheet_name="Data", index=False)

print("ARF interpolation completed successfully.")
