import pandas as pd
import numpy as np
import os

def analyze_clusters(data_matrix, labels):
    """Analyze clusters and extract characteristics."""
    characteristics = {}
    for cluster in np.unique(labels):
        cluster_mask = labels == cluster
        cluster_data = data_matrix.iloc[cluster_mask]
        cluster_means = cluster_data.mean().astype(float)
        characteristics[cluster] = {
            'size': len(cluster_data),
            'top_pathways': cluster_means.nlargest(5).to_string()
        }
    
    return characteristics

def export_results(results_df, labels, cluster_stats, moa_data=None):
    """Export clustering results to CSV files."""
    # Create results directory if it doesn't exist
    os.makedirs('results', exist_ok=True)
    
    # Create a copy of the results dataframe with cluster labels
    export_df = results_df.copy()
    export_df['cluster'] = labels
    
    # Add MoA information if available
    if moa_data is not None:
        # Ensure index alignment for joining
        common_indices = export_df.index.intersection(moa_data.index)
        if len(common_indices) > 0:
            # Find the MoA column - it might be named differently
            moa_column = None
            for col in moa_data.columns:
                if 'moa' in col.lower():
                    moa_column = col
                    break
            
            if moa_column:
                # Join only the MoA column
                export_df = export_df.join(moa_data[moa_column], how='left')
                # Rename to standardize
                export_df.rename(columns={moa_column: 'MoA'}, inplace=True)
    
    # Export the main results
    export_df.to_csv('results/clustering_results.csv')
    print("Results saved to results/clustering_results.csv")
    
    # Export cluster details
    cluster_details = pd.DataFrame({
        'cluster': range(cluster_stats['n_clusters']),
        'size': cluster_stats['sizes'],
        'silhouette': [cluster_stats['metrics']['Silhouette']] * cluster_stats['n_clusters'],
        'calinski_harabasz': [cluster_stats['metrics']['Calinski-Harabasz']] * cluster_stats['n_clusters'],
        'davies_bouldin': [cluster_stats['metrics']['Davies-Bouldin']] * cluster_stats['n_clusters']
    })
    cluster_details.to_csv('results/cluster_details.csv', index=False)
    print("Cluster details saved to results/cluster_details.csv")
    
    # Export MoA distribution across clusters if MoA data is available
    if moa_data is not None and 'MoA' in export_df.columns:
        # Create a pivot table of MoA distribution across clusters
        moa_distribution = pd.DataFrame()
        
        # Get unique MOAs
        unique_moas = export_df['MoA'].dropna().unique()
        
        for moa in unique_moas:
            moa_drugs = export_df[export_df['MoA'] == moa]
            total_count = len(moa_drugs)
            
            # Skip MOAs with very few drugs
            if total_count < 3:
                continue
                
            row = {'MOA': moa, 'Count': total_count}
            
            # Count drugs in each cluster
            for cluster in range(cluster_stats['n_clusters']):
                cluster_count = len(moa_drugs[moa_drugs['cluster'] == cluster])
                row[f'Cluster_{cluster}'] = cluster_count
            
            moa_distribution = pd.concat([moa_distribution, pd.DataFrame([row])], ignore_index=True)
        
        # Sort by total count
        moa_distribution = moa_distribution.sort_values('Count', ascending=False)
        
        # Export
        moa_distribution.to_csv('results/moa_cluster_distribution.csv', index=False)
        print("MOA cluster distribution saved to results/moa_cluster_distribution.csv") 