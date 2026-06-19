import pandas as pd
import numpy as np
from scipy.interpolate import interp1d

# -------------------------
# File paths
# -------------------------
input_file = "input.xlsx"
output_file = "output_Linear_3.xlsx"

# -------------------------
# Read Excel sheets
# -------------------------
vaitarna_df = pd.read_excel(input_file, sheet_name="Vaitarna_Grid")
ulhas_df = pd.read_excel(input_file, sheet_name="Ulhas_Grid")
query_df = pd.read_excel(input_file, sheet_name="Query_Points")

# -------------------------
# Rename SPS / PMP columns
# -------------------------
vaitarna_rename_map = {
    "SPS_1": "Vaitarna_WF102-15_SPS",
    "SPS_2": "Vaitarna_WF102-17_SPS",
    "SPS_3": "Vaitarna_WF102-18_SPS",
    "SPS_4": "Vaitarna_WF102-15_PMP",
    "SPS_5": "Vaitarna_WF102-17_PMP",
    "SPS_6": "Vaitarna_WF102-18_PMP",
}

ulhas_rename_map = {
    "SPS_1": "Ulhas_WF102-14_SPS",
    "SPS_2": "Ulhas_WF102-16_SPS",
    "SPS_3": "Ulhas_WF102-14_PMP",
    "SPS_4": "Ulhas_WF102-16_PMP",
}

vaitarna_df.rename(columns=vaitarna_rename_map, inplace=True)
ulhas_df.rename(columns=ulhas_rename_map, inplace=True)

# -------------------------
# Extract Grid IDs
# -------------------------
vaitarna_x = vaitarna_df.iloc[:, 0].values
ulhas_x = ulhas_df.iloc[:, 0].values

vaitarna_sps_cols = vaitarna_df.columns[1:]
ulhas_sps_cols = ulhas_df.columns[1:]

# -------------------------
# Read Query_Points sheet
# -------------------------
vaitarna_names = query_df["Vaitarna_Query_Points_Name"].dropna().values
vaitarna_query_raw = query_df["Vaitarna_Query_Points"].dropna().values

ulhas_names = query_df["Ulhas_Query_Points_Name"].dropna().values
ulhas_query_raw = query_df["Ulhas_Query_Points"].dropna().values

# -------------------------
# Clamp query points
# -------------------------
def clamp(query, min_x, max_x):
    return np.clip(query, min_x, max_x)

vaitarna_query_clamped = clamp(
    vaitarna_query_raw, vaitarna_x.min(), vaitarna_x.max()
)

ulhas_query_clamped = clamp(
    ulhas_query_raw, ulhas_x.min(), ulhas_x.max()
)

# -------------------------
# Linear interpolation function
# -------------------------
def interpolate_linear(x, y_df, names, query_raw, query_clamped):
    result = pd.DataFrame({
        "Name": names,
        "Area": query_raw,               # ORIGINAL input value
        "Query_Grid_ID": query_clamped   # ACTUAL value used
    })

    for col in y_df.columns:
        interpolator = interp1d(x, y_df[col].values, kind="linear")
        result[col] = interpolator(query_clamped)

    return result

# -------------------------
# Perform interpolation
# -------------------------
vaitarna_result = interpolate_linear(
    vaitarna_x,
    vaitarna_df[vaitarna_sps_cols],
    vaitarna_names,
    vaitarna_query_raw,
    vaitarna_query_clamped
)

ulhas_result = interpolate_linear(
    ulhas_x,
    ulhas_df[ulhas_sps_cols],
    ulhas_names,
    ulhas_query_raw,
    ulhas_query_clamped
)

# -------------------------
# Write output Excel
# -------------------------
with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
    vaitarna_result.to_excel(writer, sheet_name="Vaitarna", index=False)
    ulhas_result.to_excel(writer, sheet_name="Ulhas", index=False)

print("Linear interpolation completed successfully.")
