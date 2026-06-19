import numpy as np
from sklearn.cluster import KMeans

def detect_shades(pixels, clusters=5):

    kmeans = KMeans(n_clusters=clusters, n_init=10)
    kmeans.fit(pixels)

    return kmeans.cluster_centers_.astype(int)