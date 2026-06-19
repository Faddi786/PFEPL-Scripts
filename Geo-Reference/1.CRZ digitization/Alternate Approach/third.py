import os
import numpy as np
import rasterio
from skimage.morphology import skeletonize, closing, disk, remove_small_objects
from osgeo import ogr

# ------------------ INPUT ------------------
INPUT_RASTER = r"red_median_line.tif"
# -------------------------------------------

# ---------------- GAP BRIDGING -------------
# Connect nearby broken ends before tracing graph paths.
MAX_ENDPOINT_GAP_PIXELS = 45
MAX_BRIDGE_PASSES = 10
# Connect endpoint to nearby line when opposite side is not an endpoint.
SNAP_TO_LINE_RADIUS = 18
# Close tiny gaps in raster before skeletonizing.
PRE_CLOSE_RADIUS = 3
# Final micro-heal on skeleton after bridging/snapping.
POST_HEAL_RADIUS = 1
# Remove tiny disconnected dotted artifacts.
MIN_SKELETON_COMPONENT_PIXELS = 24
# -------------------------------------------

# ==========================================================
# PATH SETUP
# ==========================================================
input_name = os.path.splitext(os.path.basename(INPUT_RASTER))[0]

BASE_OUTPUT = "output"
PROJECT_FOLDER = os.path.join(BASE_OUTPUT, input_name)
SHP_FOLDER = os.path.join(PROJECT_FOLDER, "shapefiles")

os.makedirs(SHP_FOLDER, exist_ok=True)

OUTPUT_SHP = os.path.join(SHP_FOLDER, "boundary_middle_line_connected_v2.shp")

# ==========================================================
# READ RASTER
# ==========================================================
with rasterio.open(INPUT_RASTER) as src:
    data = src.read(1)
    transform = src.transform
    profile = src.profile

# ==========================================================
# BINARY MASK
# ==========================================================
binary = (data > 0).astype(np.uint8)

# ==========================================================
# PRE-CLOSE + SKELETONIZE
# ==========================================================
binary_bool = binary.astype(bool)
if PRE_CLOSE_RADIUS > 0:
    binary_bool = closing(binary_bool, footprint=disk(PRE_CLOSE_RADIUS))

skeleton = skeletonize(binary_bool)
skeleton = remove_small_objects(
    skeleton.astype(bool),
    min_size=MIN_SKELETON_COMPONENT_PIXELS,
    connectivity=2
)

# ==========================================================
# BRIDGE SMALL ENDPOINT GAPS
# ==========================================================
def bresenham_line(r0, c0, r1, c1):
    points = []
    dr = abs(r1 - r0)
    dc = abs(c1 - c0)
    sr = 1 if r0 < r1 else -1
    sc = 1 if c0 < c1 else -1
    err = dr - dc
    r, c = r0, c0

    while True:
        points.append((r, c))
        if r == r1 and c == c1:
            break
        e2 = 2 * err
        if e2 > -dc:
            err -= dc
            r += sr
        if e2 < dr:
            err += dr
            c += sc
    return points


def make_graph(pixel_set):
    neighbors_8_local = [
        (-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1),
    ]

    def neighbors_local(p):
        r, c = p
        return [(r + dr, c + dc) for dr, dc in neighbors_8_local if (r + dr, c + dc) in pixel_set]

    return {p: neighbors_local(p) for p in pixel_set}


def component_map_from_pixels(pixel_set):
    graph_local = make_graph(pixel_set)
    comp_map = {}
    comp_id = 0
    for p in pixel_set:
        if p in comp_map:
            continue
        comp_id += 1
        stack = [p]
        comp_map[p] = comp_id
        while stack:
            curr = stack.pop()
            for nxt in graph_local[curr]:
                if nxt not in comp_map:
                    comp_map[nxt] = comp_id
                    stack.append(nxt)
    return comp_map


def bridge_small_gaps(skel, max_gap_pixels, max_passes):
    total_bridges = 0
    max_gap2 = max_gap_pixels * max_gap_pixels

    for _ in range(max_passes):
        pixels_pass = set(zip(*np.where(skel)))
        graph_pass = make_graph(pixels_pass)
        endpoints = [p for p, n in graph_pass.items() if len(n) == 1]

        if len(endpoints) < 2:
            break

        # Global candidate list, then greedy disjoint shortest matching.
        candidates = []
        for i in range(len(endpoints)):
            r1, c1 = endpoints[i]
            for j in range(i + 1, len(endpoints)):
                r2, c2 = endpoints[j]
                d2 = (r2 - r1) * (r2 - r1) + (c2 - c1) * (c2 - c1)
                if 0 < d2 <= max_gap2:
                    candidates.append((d2, endpoints[i], endpoints[j]))

        if not candidates:
            break

        candidates.sort(key=lambda x: x[0])
        used = set()
        bridges_this_pass = 0

        for _, p1, p2 in candidates:
            if p1 in used or p2 in used:
                continue
            for rr, cc in bresenham_line(p1[0], p1[1], p2[0], p2[1]):
                if 0 <= rr < skel.shape[0] and 0 <= cc < skel.shape[1]:
                    skel[rr, cc] = True
            used.add(p1)
            used.add(p2)
            bridges_this_pass += 1

        total_bridges += bridges_this_pass
        if bridges_this_pass == 0:
            break

    return total_bridges


bridges_made = bridge_small_gaps(
    skeleton,
    max_gap_pixels=MAX_ENDPOINT_GAP_PIXELS,
    max_passes=MAX_BRIDGE_PASSES
)
print(f"Gaps bridged: {bridges_made}")

# Endpoint-to-line snapping handles near-miss breaks where one side ends at
# the side of another segment (not endpoint-to-endpoint).
pixels_after = set(zip(*np.where(skeleton)))
graph_after = make_graph(pixels_after)
endpoints_after = [p for p, n in graph_after.items() if len(n) == 1]
comp_map = component_map_from_pixels(pixels_after)

snap_bridges = 0
for r, c in endpoints_after:
    this_comp = comp_map.get((r, c))
    best = None
    best_d2 = None
    rr0 = max(0, r - SNAP_TO_LINE_RADIUS)
    rr1 = min(skeleton.shape[0], r + SNAP_TO_LINE_RADIUS + 1)
    cc0 = max(0, c - SNAP_TO_LINE_RADIUS)
    cc1 = min(skeleton.shape[1], c + SNAP_TO_LINE_RADIUS + 1)

    for rr in range(rr0, rr1):
        for cc in range(cc0, cc1):
            if not skeleton[rr, cc]:
                continue
            if rr == r and cc == c:
                continue
            if comp_map.get((rr, cc)) == this_comp:
                continue
            d2 = (rr - r) * (rr - r) + (cc - c) * (cc - c)
            if d2 == 0 or d2 > (SNAP_TO_LINE_RADIUS * SNAP_TO_LINE_RADIUS):
                continue
            if best_d2 is None or d2 < best_d2:
                best = (rr, cc)
                best_d2 = d2

    if best is None:
        continue

    for rr, cc in bresenham_line(r, c, best[0], best[1]):
        if 0 <= rr < skeleton.shape[0] and 0 <= cc < skeleton.shape[1]:
            skeleton[rr, cc] = True
    snap_bridges += 1

print(f"Endpoint-to-line snaps: {snap_bridges}")

# Final heal pass for tiny remaining discontinuities, then re-thin to 1-pixel.
if POST_HEAL_RADIUS > 0:
    skeleton = skeletonize(closing(skeleton, footprint=disk(POST_HEAL_RADIUS)))
    skeleton = remove_small_objects(
        skeleton.astype(bool),
        min_size=MIN_SKELETON_COMPONENT_PIXELS,
        connectivity=2
    )

# ==========================================================
# BUILD PIXEL GRAPH
# ==========================================================
rows, cols = np.where(skeleton)
pixels = set(zip(rows, cols))

neighbors_8 = [
    (-1, -1), (-1, 0), (-1, 1),
    ( 0, -1),          ( 0, 1),
    ( 1, -1), ( 1, 0), ( 1, 1),
]

def neighbors(p):
    r, c = p
    return [(r+dr, c+dc) for dr, dc in neighbors_8 if (r+dr, c+dc) in pixels]

graph = {p: neighbors(p) for p in pixels}

# ==========================================================
# CLASSIFY PIXELS
# ==========================================================
endpoints = {p for p, n in graph.items() if len(n) == 1}
junctions = {p for p, n in graph.items() if len(n) > 2}

visited_edges = set()
paths = []

# ==========================================================
# TRACE BETWEEN NODES (ENDPOINT ↔ JUNCTION)
# ==========================================================
def trace_path(start, nxt):
    path = [start, nxt]
    prev = start
    curr = nxt

    while curr not in endpoints and curr not in junctions:
        nbrs = [n for n in graph[curr] if n != prev]
        if not nbrs:
            break
        prev, curr = curr, nbrs[0]
        path.append(curr)

    return path

def trace_cycle(start):
    path = [start]
    prev = None
    curr = start

    while True:
        nbrs = [n for n in graph[curr] if n != prev]
        if not nbrs:
            break

        nxt = nbrs[0]
        path.append(nxt)

        edge = tuple(sorted((curr, nxt)))
        visited_edges.add(edge)

        prev, curr = curr, nxt
        if curr == start:
            break

    return path

for node in endpoints | junctions:
    for n in graph[node]:
        edge = tuple(sorted((node, n)))
        if edge in visited_edges:
            continue

        path = trace_path(node, n)

        for i in range(len(path) - 1):
            visited_edges.add(tuple(sorted((path[i], path[i+1]))))

        paths.append(path)

# Handle components with only degree-2 nodes (closed loops)
for p in pixels:
    unvisited = [n for n in graph[p] if tuple(sorted((p, n))) not in visited_edges]
    if not unvisited:
        continue

    cycle_path = trace_cycle(p)
    if len(cycle_path) >= 2:
        paths.append(cycle_path)

# ==========================================================
# CONVERT TO LINE GEOMETRIES
# ==========================================================
line_geoms = []

for path in paths:
    if len(path) < 2:
        continue

    line = ogr.Geometry(ogr.wkbLineString)
    for r, c in path:
        x, y = rasterio.transform.xy(transform, r, c)
        line.AddPoint(x, y)

    line_geoms.append(line)

# ==========================================================
# WRITE SHAPEFILE
# ==========================================================
driver = ogr.GetDriverByName("ESRI Shapefile")
if os.path.exists(OUTPUT_SHP):
    driver.DeleteDataSource(OUTPUT_SHP)

ds = driver.CreateDataSource(OUTPUT_SHP)
layer = ds.CreateLayer("centerline", geom_type=ogr.wkbLineString)
layer.CreateField(ogr.FieldDefn("id", ogr.OFTInteger))

for i, geom in enumerate(line_geoms, start=1):
    feat = ogr.Feature(layer.GetLayerDefn())
    feat.SetField("id", i)
    feat.SetGeometry(geom)
    layer.CreateFeature(feat)
    feat = None

ds = None

print("DONE")
print(f"Connected centerline features: {len(line_geoms)}")
print(f"Saved to: {OUTPUT_SHP}")
