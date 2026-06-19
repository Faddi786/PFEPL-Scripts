import rasterio
import numpy as np

def load_tif(path):

    with rasterio.open(path) as src:
        img = src.read([1,2,3])
        profile = src.profile

    img = np.transpose(img, (1,2,0))

    img = img.astype(np.uint8)

    return img, profile