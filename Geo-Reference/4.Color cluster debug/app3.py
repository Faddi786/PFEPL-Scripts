import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
import cv2  # pip install opencv-python if not already

def color_code_all_lines(image_path, num_clusters=6, sat_threshold=30, output_path='color_coded_lines.png'):
    """
    Detects ALL colored lines/structures (high saturation pixels) in the image,
    clusters them into distinct shades, and colors each cluster with a unique bright color
    on a black background. This catches ANY color (not just blue) for map lines like CRZ.
    Background (low sat, white/gray/black) is ignored.
    """
    # Step 1: Load image
    image = Image.open(image_path).convert('RGB')
    image_array = np.array(image, dtype=np.uint8)
    h, w = image_array.shape[:2]
    
    print(f"Image loaded: {h}x{w} pixels")
    
    # Debug: Print overall RGB/HSV stats
    hsv = cv2.cvtColor(image_array, cv2.COLOR_RGB2HSV)
    print(f"RGB min/max: R({image_array[:,:,0].min()}-{image_array[:,:,0].max()}), "
          f"G({image_array[:,:,1].min()}-{image_array[:,:,1].max()}), "
          f"B({image_array[:,:,2].min()}-{image_array[:,:,2].max()})")
    print(f"HSV min/max: H({hsv[:,:,0].min()}-{hsv[:,:,0].max()}), "
          f"S({hsv[:,:,1].min()}-{hsv[:,:,1].max()}), "
          f"V({hsv[:,:,2].min()}-{hsv[:,:,2].max()})")
    
    # Step 2: Detect high-saturation pixels (colored lines, ignore grays/whites/blacks)
    # Saturation > sat_threshold to catch any colored features
    sat_mask = hsv[:,:,1] > sat_threshold
    colored_count = np.sum(sat_mask)
    print(f"High-sat pixels detected: {colored_count} ({colored_count / (h*w) * 100:.1f}% of image)")
    
    if colored_count < 100:
        print(f"WARNING: Very few colored pixels (sat > {sat_threshold}). Try lowering sat_threshold to 20 or 10.")
        # Fallback: Lower threshold and retry
        sat_mask = hsv[:,:,1] > (sat_threshold - 10)
        colored_count = np.sum(sat_mask)
        print(f"Fallback (sat > {sat_threshold-10}): {colored_count} pixels")
        if colored_count < 100:
            print("ERROR: Image may be grayscale or lines too faint. Share a sample pixel RGB!")
            return
    
    # Save raw colored mask for debug
    colored_img = Image.fromarray((sat_mask * 255).astype(np.uint8), mode='L')
    colored_img.save('colored_mask.png')
    print("Saved: colored_mask.png (white = any colored pixels)")
    
    # Step 3: Extract colored pixels for clustering
    colored_pixels = image_array[sat_mask].reshape(-1, 3).astype(np.float32)
    if len(colored_pixels) == 0:
        print("No colored pixels to cluster!")
        return
    
    print(f"Clustering {len(colored_pixels)} colored pixels into {num_clusters} groups...")
    
    # K-means on RGB values
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    _, labels, centers = cv2.kmeans(colored_pixels, num_clusters, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
    
    labels = labels.flatten()
    print(f"Cluster centers (RGB):")
    for i, center in enumerate(centers):
        print(f"  Cluster {i}: RGB{np.round(center).astype(int)} (size: {np.sum(labels == i)} px)")
    
    # Step 4: Assign unique bright colors to each cluster
    unique_colors = [
        [255, 0, 0],      # Red
        [0, 255, 0],      # Green
        [0, 0, 255],      # Blue
        [255, 255, 0],    # Yellow
        [255, 0, 255],    # Magenta
        [0, 255, 255],    # Cyan
        [255, 165, 0],    # Orange
        [128, 0, 128],    # Purple
        [0, 128, 0],      # Dark Green
        [255, 192, 203]   # Pink
    ][:num_clusters]
    
    # Create black output image
    output_array = np.zeros((h, w, 3), dtype=np.uint8)
    
    # Assign colors based on cluster
    linear_indices = np.where(sat_mask)[0]  # Flat indices of colored pixels
    for i, color in enumerate(unique_colors):
        cluster_mask = (labels == i)
        if np.sum(cluster_mask) > 0:
            cluster_indices = linear_indices[cluster_mask]
            y_coords, x_coords = np.unravel_index(cluster_indices, (h, w))
            output_array[y_coords, x_coords] = color
    
    # Save
    output_image = Image.fromarray(output_array)
    output_image.save(output_path)
    
    # Preview
    plt.figure(figsize=(12, 8))
    plt.imshow(output_image)
    plt.title('Color-Coded All Lines (Each color = one shade group)')
    plt.axis('off')
    plt.show()
    
    print(f"\nColor-coded image saved: {output_path}")
    print("INSTRUCTIONS:")
    print("1. Open the saved image or view the plot above.")
    print("2. Identify the color representing the CRZ boundary line (e.g., 'yellow line snaking inland').")
    print("3. Note its cluster number from console (e.g., Cluster 2: RGB[200,200,0]).")
    print("4. To extract JUST that line: Run extract_line_by_cluster('output_polynomial_MH_75.jpg', cluster_id=2)")
    print("   (Replace 2 with your cluster ID. It will thin to a clean line.)")
    
    return output_array, labels, centers

def extract_line_by_cluster(image_path, cluster_id, output_path='extracted_line.png'):
    """
    Extracts and thins a specific cluster to a clean white line on black.
    """
    image = Image.open(image_path).convert('RGB')
    image_array = np.array(image, dtype=np.uint8)
    h, w = image_array.shape[:2]
    
    hsv = cv2.cvtColor(image_array, cv2.COLOR_RGB2HSV)
    sat_mask = hsv[:,:,1] > 30  # Reuse same detection
    
    colored_pixels = image_array[sat_mask].reshape(-1, 3).astype(np.float32)
    if len(colored_pixels) == 0:
        print("No colored pixels!")
        return
    
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    _, labels, _ = cv2.kmeans(colored_pixels, 6, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)  # Match num_clusters=6
    labels = labels.flatten()
    
    # Specific cluster
    cluster_mask = (labels == cluster_id)
    if np.sum(cluster_mask) == 0:
        print(f"No pixels in cluster {cluster_id}!")
        return
    
    linear_indices = np.where(sat_mask)[0][cluster_mask]
    y_coords, x_coords = np.unravel_index(linear_indices, (h, w))
    
    # Binary mask for this cluster
    cluster_binary = np.zeros((h, w), dtype=bool)
    cluster_binary[y_coords, x_coords] = True
    
    # Thin to skeleton (clean line)
    from skimage import morphology
    cluster_skeleton = morphology.skeletonize(cluster_binary)
    
    # Output: white skeleton on black
    output_array = np.zeros((h, w, 3), dtype=np.uint8)
    output_array[cluster_skeleton] = [255, 255, 255]
    
    output_image = Image.fromarray(output_array)
    output_image.save(output_path)
    
    # Preview
    plt.figure(figsize=(12, 8))
    plt.imshow(output_image)
    plt.title(f'Extracted Line from Cluster {cluster_id}')
    plt.axis('off')
    plt.show()
    
    print(f"Clean line saved to: {output_path}")
    return output_path

# Run the color-coding
if __name__ == "__main__":
    color_coded_img, labels, centers = color_code_all_lines('output_polynomial_MH_75.jpg', num_clusters=6, sat_threshold=30)
    
    # Example extraction (uncomment after identifying cluster):
    # extract_line_by_cluster('output_polynomial_MH_75.jpg', cluster_id=0)  # e.g., cluster 0