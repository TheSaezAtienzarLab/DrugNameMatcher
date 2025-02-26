import os
import pandas as pd
import numpy as np
from src.data_loader import load_drug_pathway_data, load_moa_data
from src.preprocessing import perform_pca
from src.clustering import perform_clustering, find_optimal_k
from src.utils import analyze_clusters, export_results
# Import the visualize_clustering function from the restructured module
from src.visualization.main import visualize_clustering

def main():
    # Load and prepare data
    print("Loading drug pathway data...")
    final_matrix, drugs, pathways = load_drug_pathway_data('drugs_moable')
    if final_matrix is None:
        print("Error loading data. Exiting.")
        return
    
    print(f"Loaded data for {len(drugs)} drugs and {len(pathways)} pathways")
    
    # Load MOA data if available
    moa_data = load_moa_data('final_output/all_matched_drugs.csv')
    
    # Perform PCA
    print("\nPerforming PCA...")
    results_df, pca = perform_pca(final_matrix)
    print(f"PCA explained variance: {pca.explained_variance_ratio_ * 100}")
    
    # Find optimal number of clusters
    optimal_k = find_optimal_k(results_df)
    
    # Perform clustering
    print("\nPerforming KMeans clustering...")
    labels, metrics, kmeans = perform_clustering(results_df, optimal_k)
    
    # Analyze clusters
    print("\nAnalyzing clusters...")
    characteristics = analyze_clusters(final_matrix, labels)
    
    # Store statistics
    cluster_stats = {
        'n_clusters': len(np.unique(labels)),
        'sizes': pd.Series(labels).value_counts().sort_index().tolist(),
        'metrics': metrics,
        'characteristics': characteristics
    }
    
    # Export results to CSV
    print("\nExporting results...")
    export_results(results_df, labels, cluster_stats, moa_data)
    
    # Create visualization using the new modular approach
    print("\nCreating visualization...")
    html_path = visualize_clustering(results_df, pca, labels, cluster_stats, moa_data)
    
    print(f"\nAnalysis complete! Open {html_path} to view the results.")

if __name__ == "__main__":
    main()