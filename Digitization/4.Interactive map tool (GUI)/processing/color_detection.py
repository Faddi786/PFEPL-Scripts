import numpy as np
from sklearn.cluster import KMeans

def detect_colors(image, clusters=8):

    pixels = image.reshape(-1,3)

    kmeans = KMeans(n_clusters=clusters, n_init=10)
    kmeans.fit(pixels)

    colors = kmeans.cluster_centers_.astype(int)

    return colors