import geopandas as gpd
import pandas as pd
import re
import os

# === Paths ===
shapefile_path = r"C:\Users\Swapnali\Desktop\Test Upstream\Upstream Utilization\Vaitarna\Vaitarna_Planned_Utilisation_Completed_Projects.shp"
excel_path     = r"C:\Users\Swapnali\Desktop\Test Upstream\Vaitarna_Plan_utilisation_Completed_Projects.xlsx"


output_path    = r"C:\Users\Swapnali\Desktop\Test Upstream\Upstream Utilization\Vaitarna_With_Upstream\Vaitarna_With_Upstream.shp"

# output_unmatched = r"C:\Users\Swapnali\Desktop\dam and the points subtraction\Cleaned\Step 1\Outputs\unmatched_junctions.xlsx"
# output_collisions = r"C:\Users\Swapnali\Desktop\dam and the points subtraction\Cleaned\Step 1\Outputs\excel_key_collisions.xlsx"

# === Helpers ===
def extract_number(x):
    m = re.search(r"\d+", str(x))
    return int(m.group()) if m else None

def normalize_name(x):
    # lower, remove spaces, hyphens, underscores and collapse multiple spaces
    s = re.sub(r"[\s\-_]+", "", str(x).strip().lower())
    return s

# === Load data ===
gdf = gpd.read_file(shapefile_path)
df  = pd.read_excel(excel_path, usecols=[0, 1]).copy()
df.columns = ["NAME", "rainfall"]

# === Build matching keys ===
# gdf["name_norm"]     = gdf["NAME"].apply(normalize_name)
# gdf["JunctionID"]    = gdf["NAME"].apply(extract_number)

gdf["name_norm"]  = gdf["Name"].apply(normalize_name)
gdf["JunctionID"] = gdf["Name"].apply(extract_number)

df["name_norm"]      = df["NAME"].apply(normalize_name)
df["JunctionID"]     = df["NAME"].apply(extract_number)

# === Detect collisions (many rows in Excel for the same key) ===
collisions_name = (df.groupby("name_norm", dropna=False)
                     .size().reset_index(name="count")
                     .query("count > 1"))
collisions_num  = (df.groupby("JunctionID", dropna=False)
                     .size().reset_index(name="count")
                     .query("count > 1"))

# Save details so you can inspect what will cause duplication
# with pd.ExcelWriter(output_collisions) as xw:
#     if not collisions_name.empty:
#         df[df["name_norm"].isin(collisions_name["name_norm"])].to_excel(xw, "by_name", index=False)
#     if not collisions_num.empty:
#         df[df["JunctionID"].isin(collisions_num["JunctionID"])].to_excel(xw, "by_number", index=False)

# === Choose a de-duplication policy on the Excel side ===
# Options: "first", "max", "min", "mean", "sum". Pick ONE.
agg_policy = "first"

def reduce_df(key_col):
    if agg_policy == "first":
        # keep the first non-null rainfall per key
        return (df.sort_values(key_col)
                  .drop_duplicates(subset=[key_col], keep="first")[[key_col, "rainfall"]])
    else:
        func = {"max": "max", "min": "min", "mean": "mean", "sum": "sum"}[agg_policy]
        return (df.groupby(key_col, dropna=False, as_index=False)["rainfall"]
                  .agg(func))

# Reduced tables (no duplicate keys)
df_by_name = reduce_df("name_norm")
df_by_num  = reduce_df("JunctionID")

# === Merge Strategy ===
# 1) exact name match first (no duplication because df_by_name has unique keys)
merged = gdf.merge(df_by_name, how="left", on="name_norm", suffixes=("", "_byname"))

# 2) For those still missing rainfall, try numeric fallback (also unique keys)
left_missing = merged["rainfall"].isna()
if left_missing.any():
    merged2 = merged[left_missing].merge(
        df_by_num.rename(columns={"rainfall": "rainfall_num"}),
        how="left",
        on="JunctionID"
    )
    merged.loc[left_missing, "rainfall"] = merged2["rainfall_num"].values

# === Output dirs ===
os.makedirs(os.path.dirname(output_path), exist_ok=True)

# ✅ Remove helper columns
merged = merged.drop(columns=["name_norm", "JunctionID"], errors="ignore")

# ✅ Rename column
merged = merged.rename(columns={"rainfall": "upstream_u"})

# === Save shapefile ===
merged.to_file(output_path)

# === Show sample ===
print("\n[Matched sample]")
# print(merged[["NAME", "JunctionID", "rainfall"]].head(20))
# print(merged[["Name", "JunctionID", "rainfall"]].head(20))

print(merged[["Name", "upstream_u"]].head(20))

# === Save unmatched for review ===
# unmatched = merged.loc[merged["rainfall"].isna(), ["NAME", "JunctionID", "name_norm"]].drop_duplicates()

# unmatched = merged.loc[merged["rainfall"].isna(), ["Name", "JunctionID", "name_norm"]]

# unmatched.to_excel(output_unmatched, index=False)

print(f"\n[INFO] Saved shapefile: {output_path}")
# print(f"[INFO] Unmatched count: {len(unmatched)} → {output_unmatched}")
# if (not collisions_name.empty) or (not collisions_num.empty):
#     print(f"[WARN] Detected duplicate keys in Excel; details saved to {output_collisions}")
#     print("      Consider opening it to see which rows would have caused duplication.")
