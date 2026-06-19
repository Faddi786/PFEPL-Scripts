import pandas as pd
import numpy as np
from scipy.interpolate import PchipInterpolator

# -------------------------
# File paths
# -------------------------
input_file = "input.xlsx"
output_file = "output_PCHIP.xlsx"

# -------------------------
# Read Excel sheets
# -------------------------
vaitarna_df = pd.read_excel(input_file, sheet_name="Vaitarna_Grid")
ulhas_df = pd.read_excel(input_file, sheet_name="Ulhas_Grid")
query_df = pd.read_excel(input_file, sheet_name="Query_Points")

# -------------------------
# Rename SPS columns
# -------------------------
vaitarna_rename_map = {
    "SPS_1": "Vaitarna_WF102-14_SPS",
    "SPS_2": "Vaitarna_WF102-16_SPS",
    "SPS_3": "Vaitarna_WF102-18_SPS",
    "SPS_4": "Vaitarna_WF102-14_PMP",
    "SPS_5": "Vaitarna_WF102-16_PMP",
    "SPS_6": "Vaitarna_WF102-18_PMP",
}

ulhas_rename_map = {
    "SPS_1": "Ulhas_WF102-14_SPS",
    "SPS_2": "Ulhas_WF102-14_PMP",
    "SPS_3": "Ulhas_WF102-16_SPS",
    "SPS_4": "Ulhas_WF102-16_PMP",
}

vaitarna_df.rename(columns=vaitarna_rename_map, inplace=True)
ulhas_df.rename(columns=ulhas_rename_map, inplace=True)

# -------------------------
# Extract X and SPS columns
# -------------------------
vaitarna_x = vaitarna_df.iloc[:, 0].values
ulhas_x = ulhas_df.iloc[:, 0].values

vaitarna_sps_cols = vaitarna_df.columns[1:]
ulhas_sps_cols = ulhas_df.columns[1:]

vaitarna_query_raw = query_df.iloc[:, 0].dropna().values
ulhas_query_raw = query_df.iloc[:, 1].dropna().values

# -------------------------
# Clamp query points
# -------------------------
def clamp_queries(query, x_min, x_max):
    return np.clip(query, x_min, x_max)

vaitarna_query = clamp_queries(vaitarna_query_raw, vaitarna_x.min(), vaitarna_x.max())
ulhas_query = clamp_queries(ulhas_query_raw, ulhas_x.min(), ulhas_x.max())

# -------------------------
# Interpolation function (PCHIP)
# -------------------------
def interpolate_pchip(x, y_df, query_points):
    result = pd.DataFrame({"Query_Grid_ID": query_points})

    for col in y_df.columns:
        interpolator = PchipInterpolator(x, y_df[col].values)
        result[col] = interpolator(query_points)

    return result

# -------------------------
# Perform interpolation
# -------------------------
vaitarna_result = interpolate_pchip(
    vaitarna_x,
    vaitarna_df[vaitarna_sps_cols],
    vaitarna_query
)

ulhas_result = interpolate_pchip(
    ulhas_x,
    ulhas_df[ulhas_sps_cols],
    ulhas_query
)

# -------------------------
# Write output Excel
# -------------------------
with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
    vaitarna_result.to_excel(writer, sheet_name="Vaitarna", index=False)
    ulhas_result.to_excel(writer, sheet_name="Ulhas", index=False)

print("PCHIP interpolation with clamping completed.")
