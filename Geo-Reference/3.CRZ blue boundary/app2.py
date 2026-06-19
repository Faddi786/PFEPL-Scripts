import numpy as np
from scipy import ndimage
from skimage import morphology, feature, measure
from PIL import Image
import matplotlib.pyplot as plt
import cv2  # pip install opencv-python if not already

def extract_crz_boundary(image_path, output_path='extracted_crz_line.png'):
    # Step 1: Load image
    image = Image.open(image_path).convert('RGB')
    image_array = np.array(image, dtype=np.uint8)
    h, w = image_array.shape[:2]
    
    print(f"Image loaded: {h}x{w} pixels")
    
    # Step 2: Convert to HSV and detect blue (broader range for variations)
    hsv = cv2.cvtColor(image_array, cv2.COLOR_RGB2HSV)
    
    # Broader blue: Hue 80-150 (covers cyan to purple-blues), Sat/Val 30+ to catch pale/dull
    lower_blue = np.array([80, 30, 30])
    upper_blue = np.array([150, 255, 255])
    blue_mask = cv2.inRange(hsv, lower_blue, upper_blue)
    
    # Extra pass for very dark blues/navy
    dark_lower = np.array([100, 20, 20])
    dark_upper = np.array([160, 255, 255])
    dark_mask = cv2.inRange(hsv, dark_lower, dark_upper)
    blue_mask = cv2.bitwise_or(blue_mask, dark_mask)
    
    # Light denoising (for JPG artifacts)
    blue_mask = cv2.medianBlur(blue_mask.astype(np.uint8), 3)
    blue_mask = (blue_mask > 0)
    
    # Save & stats: Blue detection
    blue_count = np.sum(blue_mask)
    print(f"Blue pixels detected: {blue_count} ({blue_count / (h*w) * 100:.1f}% of image)")
    
    blue_img = Image.fromarray((blue_mask * 255).astype(np.uint8), mode='L')
    blue_img.save('blue_mask.png')
    print("Saved: blue_mask.png (check if CRZ line appears white)")
    
    if blue_count < 100:
        print("WARNING: Very few blue pixels—HSV ranges may need tweaking. Pick a CRZ line pixel RGB and share it!")
        return
    
    # Step 3: Clean and thin to lines
    blue_mask = morphology.remove_small_objects(blue_mask, max_size=49)  # Small noise gone
    
    # Optional light erosion (set iterations=0 to skip if lines are already thin)
    blue_mask = morphology.erosion(blue_mask, morphology.disk(0))  # No erosion for now
    
    skeleton = morphology.skeletonize(blue_mask)
    
    # Save skeleton
    skeleton_count = np.sum(skeleton)
    print(f"Skeleton pixels (lines): {skeleton_count}")
    skeleton_img = Image.fromarray((skeleton * 255).astype(np.uint8), mode='L')
    skeleton_img.save('skeleton.png')
    print("Saved: skeleton.png (should show thin white lines)")
    
    if skeleton_count < 50:
        print("WARNING: Skeleton is empty/thin—try skipping erosion or broadening HSV further.")
        return
    
    # Step 4: Remove Hazard Line (blobs + perimeter)
    blobs = feature.blob_log(skeleton.astype(float), min_sigma=1, max_sigma=4, threshold=0.05)  # Lower threshold for small circles
    print(f"Blobs detected (possible circles): {len(blobs)}")
    temp_skeleton = skeleton.copy()
    if len(blobs) > 0:
        for blob in blobs:
            y, x, _ = blob
            y, x = int(y), int(x)
            temp_skeleton[max(0, y-3):y+4, max(0, x-3):x+4] = False  # Smaller buffer
    
    # Perimeter removal (smaller buffer: 2% to avoid cutting inner lines)
    edge_buffer = int(min(h, w) * 0.02)
    temp_skeleton[:edge_buffer, :] = False
    temp_skeleton[-edge_buffer:, :] = False
    temp_skeleton[:, :edge_buffer] = False
    temp_skeleton[:, -edge_buffer:] = False
    
    # Save after hazard removal
    after_hazard_count = np.sum(temp_skeleton)
    print(f"Pixels after hazard removal: {after_hazard_count}")
    after_img = Image.fromarray((temp_skeleton * 255).astype(np.uint8), mode='L')
    after_img.save('after_hazard_removal.png')
    print("Saved: after_hazard_removal.png (lines minus perimeter/blobs)")
    
    if after_hazard_count < 50:
        print("WARNING: Almost everything removed—Hazard filter too aggressive. Check after_hazard_removal.png")
        skeleton = temp_skeleton  # Use this anyway
    else:
        skeleton = temp_skeleton
    
    # Step 5: Select main CRZ line (longest, looser filters)
    labeled = measure.label(skeleton, connectivity=1, background=0)
    
    # Version compatibility
    if isinstance(labeled, tuple):
        labels, num_features = labeled
    else:
        labels = labeled
        num_features = labels.max() if labels.size > 0 else 0
    
    print(f"Connected components found: {num_features}")
    
    if num_features > 0:
        regions = measure.regionprops(labels)
        # Looser: area >50, eccentricity >0.5 (more curvy OK)
        valid_regions = [r for r in regions if r.area > 50 and r.eccentricity > 0.5]
        
        if valid_regions:
            crz_region = max(valid_regions, key=lambda r: r.area)
            print(f"Selected region: label={crz_region.label}, area={crz_region.area}, ecc={crz_region.eccentricity:.2f}")
            skeleton = (labels == crz_region.label)
        else:
            # Fallback: longest overall
            crz_region = max(regions, key=lambda r: r.area)
            print(f"Fallback to longest region: label={crz_region.label}, area={crz_region.area}")
            skeleton = (labels == crz_region.label)
    else:
        print("ERROR: No lines left—check intermediates!")
        skeleton = np.zeros_like(skeleton)
    
    # Step 6: Output
    output_array = np.zeros((h, w, 3), dtype=np.uint8)
    output_array[skeleton] = [255, 255, 255]
    output_image = Image.fromarray(output_array)
    output_image.save(output_path)
    
    final_count = np.sum(skeleton)
    print(f"Final line pixels: {final_count}")
    if final_count > 0:
        print("SUCCESS: CRZ line extracted!")
    else:
        print("Still black—need HSV tweak. Share RGB of a CRZ line pixel (use Paint: right-click > Edit > Color picker).")
    
    # Preview
    plt.figure(figsize=(12, 8))
    plt.imshow(output_image)
    plt.title('Extracted CRZ Boundary Line')
    plt.axis('off')
    plt.show()
    
    print(f"Final output: {output_path}")
    return output_path

# Run
if __name__ == "__main__":
    extract_crz_boundary('output_polynomial_MH_75.jpg')