import numpy as np
import rasterio
from scipy import ndimage as ndi
from skimage.measure import label, regionprops
from scipy.spatial import cKDTree
from rasterio.enums import ColorInterp

# -------------------------
# Input / Output
# -------------------------
input_raster = "digitized_boundary.tif"
output_raster = "digitized_boundary.tif"

def remove_text_labels(input_path, output_path):
    print(f"Reading {input_path}...")
    with rasterio.open(input_path) as src:
        profile = src.profile
        img = src.read()
    
    mask = np.any(img > 0, axis=0)
    
    print("Labeling components...")
    labels, count = ndi.label(mask)
    if count == 0:
        print("No foreground found.")
        return

    print(f"Found {count} components. Analyzing props...")
    props = regionprops(labels)
    
    # Filter for labels (exclude very large things like boundaries)
    # Letters are usually small (e.g., 50-1000 pixels)
    candidates = []
    for p in props:
        if 20 < p.area < 2000:
            candidates.append(p)
            
    print(f"{len(candidates)} candidate components for text.")
    if not candidates:
        return

    # Use KDTree on centroids for fast clustering
    centroids = [p.centroid for p in candidates]
    tree = cKDTree(centroids)
    
    # Clustering: group components that are within 150 pixels of each other
    clusters = []
    visited = np.zeros(len(candidates), dtype=bool)
    
    for i in range(len(candidates)):
        if visited[i]:
            continue
        
        current_cluster_indices = [i]
        visited[i] = True
        
        # BFS to find all neighbors
        queue = [i]
        while queue:
            idx = queue.pop(0)
            # Find neighbors within 150px
            neighbors = tree.query_ball_point(centroids[idx], r=150)
            for n in neighbors:
                if not visited[n]:
                    visited[n] = True
                    current_cluster_indices.append(n)
                    queue.append(n)
        
        clusters.append([candidates[idx] for idx in current_cluster_indices])
    
    print(f"Formed {len(clusters)} clusters.")
    
    mask_to_remove = np.zeros_like(mask, dtype=bool)
    removed_count = 0
    
    for cluster in clusters:
        if len(cluster) >= 5: # Multiple letters/words
            # Dimensions
            min_r = min(p.bbox[0] for p in cluster)
            max_r = max(p.bbox[2] for p in cluster)
            min_c = min(p.bbox[1] for p in cluster)
            max_c = max(p.bbox[3] for p in cluster)
            
            width = max_c - min_c
            height = max_r - min_r
            aspect_ratio = width / max(1, height)
            
            # Text strings are usually horizontal (or vertical)
            if aspect_ratio > 2.0 or aspect_ratio < 0.5:
                print(f"Removing cluster at ({min_r}, {min_c}) to ({max_r}, {max_c}) with {len(cluster)} letters.")
                for p in cluster:
                    mask_to_remove[labels == p.label] = True
                removed_count += 1

    if removed_count == 0:
        print("No large labels found.")
        return

    # Apply removal
    print(f"Removing {removed_count} clusters...")
    for i in range(img.shape[0]):
        img[i][mask_to_remove] = 0
    
    # Save result
    profile.update(compress='lzw')
    with rasterio.open(output_path, "w", **profile) as dst:
        dst.write(img)
    
    print(f"Successfully saved to {output_path}")

if __name__ == "__main__":
    remove_text_labels(input_raster, output_raster)
