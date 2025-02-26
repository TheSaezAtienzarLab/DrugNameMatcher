import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score
from sklearn.metrics import silhouette_samples
from kneed import KneeLocator

def find_optimal_k(data, max_k=10):
    """Find optimal number of clusters using the elbow method."""
    inertias = []
    silhouette_scores = []
    
    # Try different values of k
    for k in range(2, min(max_k + 1, len(data) // 5)):
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        kmeans.fit(data)
        inertias.append(kmeans.inertia_)
        
        # Calculate silhouette score
        labels = kmeans.labels_
        silhouette_scores.append(silhouette_score(data, labels))
    
    # Find the elbow point
    k_range = range(2, min(max_k + 1, len(data) // 5))
    if len(k_range) > 2:
        try:
            kl = KneeLocator(k_range, inertias, curve='convex', direction='decreasing')
            optimal_k = kl.elbow
        except:
            # If KneeLocator fails, use the k with highest silhouette score
            optimal_k = k_range[np.argmax(silhouette_scores)]
    else:
        optimal_k = 2
    
    return optimal_k if optimal_k else 4  # Default to 4 if no elbow is found

def perform_clustering(pca_result, n_clusters=None):
    """Perform KMeans clustering on PCA results."""
    if n_clusters is None:
        n_clusters = find_optimal_k(pca_result)
        print(f"\nOptimal number of clusters: {n_clusters}")
    
    # Perform KMeans clustering
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(pca_result)
    
    # Calculate metrics
    metrics = {
        'Silhouette': silhouette_score(pca_result, labels),
        'Calinski-Harabasz': calinski_harabasz_score(pca_result, labels),
        'Davies-Bouldin': davies_bouldin_score(pca_result, labels)
    }
    
    print(f"KMeans clustering metrics:")
    for metric_name, value in metrics.items():
        print(f"  {metric_name}: {value:.4f}")
    
    return labels, metrics, kmeans 