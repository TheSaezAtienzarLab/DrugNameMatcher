"""
Data processing module for visualization.

This module provides functions to process clustering and PCA results
and prepare them for visualization.
"""

import numpy as np
import pandas as pd
import random
import plotly.graph_objects as go

def create_visualization_data(results_df, pca, labels, cluster_stats, moa_data=None):
    """Create data for visualization.
    
    Args:
        results_df (pandas.DataFrame): PCA results dataframe
        pca (sklearn.decomposition.PCA): PCA model
        labels (numpy.ndarray): Cluster labels
        cluster_stats (dict): Statistics about the clusters
        moa_data (pandas.DataFrame, optional): Mechanism of action data
    
    Returns:
        dict: Visualization data including plot data, layout, and configuration
    """
    # Debug: Print input data shapes
    print(f"Creating visualization data:")
    print(f"- Results dataframe shape: {results_df.shape}")
    print(f"- Number of labels: {len(labels)}")
    print(f"- Number of unique clusters: {len(np.unique(labels))}")
    
    try:
        # Ensure we have a copy of the original data with cluster labels
        visualization_df = results_df.copy()
        visualization_df['cluster'] = labels
        
        # Add MoA information if available
        if moa_data is not None:
            print(f"- MoA data shape: {moa_data.shape}")
            visualization_df = visualization_df.join(moa_data, how='left')
        
        # Define consistent cluster colors
        unique_clusters = np.unique(labels)
        cluster_colors = {
            0: 'rgb(31, 119, 180)',   # Blue
            1: 'rgb(255, 127, 14)',   # Orange
            2: 'rgb(44, 160, 44)',    # Green
            3: 'rgb(214, 39, 40)',    # Red
            4: 'rgb(148, 103, 189)'   # Purple
        }
        
        # Add fallback colors for additional clusters if needed
        for i in range(5, max(unique_clusters) + 1):
            cluster_colors[i] = f'rgb({random.randint(0, 255)}, {random.randint(0, 255)}, {random.randint(0, 255)})'
        
        # Add color information to the dataframe
        visualization_df['color'] = visualization_df['cluster'].map(cluster_colors)
        
        # Prepare the data for Plotly
        plot_data = []
        
        # Create a trace for each cluster to maintain color consistency
        for cluster in unique_clusters:
            cluster_data = visualization_df[visualization_df['cluster'] == cluster]
            
            # Create the trace for this cluster
            trace = {
                'type': 'scatter3d',
                'x': cluster_data['PC1'].tolist(),
                'y': cluster_data['PC2'].tolist(),
                'z': cluster_data['PC3'].tolist(),
                'mode': 'markers',
                'marker': {
                    'size': 5,
                    'color': cluster_colors[cluster],
                    'line': {'width': 0.5, 'color': 'white'}
                },
                'name': f'Cluster {cluster}',
                'text': cluster_data.index.tolist(),  # Drug names as hover text
                'hoverinfo': 'text',
                'customdata': cluster_data['cluster'].tolist()  # Store cluster info for filtering
            }
            
            # Add MoA information to hover text if available
            if moa_data is not None and 'MoA' in cluster_data.columns:
                hover_texts = []
                for idx, row in cluster_data.iterrows():
                    moa_text = f"MoA: {row['MoA']}" if pd.notna(row['MoA']) else "MoA: Unknown"
                    hover_texts.append(f"{idx}<br>{moa_text}<br>Cluster: {row['cluster']}")
                trace['text'] = hover_texts
            
            plot_data.append(trace)
        
        # Create the layout
        layout = {
            'title': 'Drug Clustering Analysis',
            'scene': {
                'xaxis': {'title': 'PC1'},
                'yaxis': {'title': 'PC2'},
                'zaxis': {'title': 'PC3'}
            },
            'margin': {'l': 0, 'r': 0, 'b': 0, 't': 50},
            'legend': {'x': 0.8, 'y': 0.9}
        }
        
        # Add filter controls for MoA if available
        moa_buttons = create_moa_buttons(visualization_df, unique_clusters, plot_data, moa_data)
        
        if moa_buttons:
            # Add dropdown for MoA filtering
            layout['updatemenus'] = [{
                'buttons': moa_buttons,
                'direction': 'down',
                'showactive': True,
                'x': 0.1,
                'y': 1.1,
                'xanchor': 'left',
                'yanchor': 'top'
            }]
        
        print(f"- Created {len(plot_data)} traces for visualization")
        
        return {
            'data': plot_data,
            'layout': layout,
            'config': {'responsive': True},
            'cluster_stats': cluster_stats,
            'pca_info': {
                'explained_variance': pca.explained_variance_ratio_.tolist()
            },
            'moa_buttons': moa_buttons
        }
    
    except Exception as e:
        print(f"Error creating visualization data: {str(e)}")
        # Return minimal valid data structure
        return {
            'data': [],
            'layout': {'title': 'Error in Visualization'},
            'config': {'responsive': True},
            'cluster_stats': {'n_clusters': 0, 'sizes': []},
            'pca_info': {'explained_variance': [0, 0, 0]}
        }

def create_moa_buttons(visualization_df, unique_clusters, plot_data, moa_data=None):
    """Create buttons for MoA filtering in the visualization.
    
    Args:
        visualization_df (pandas.DataFrame): Dataframe with visualization data
        unique_clusters (numpy.ndarray): Array of unique cluster labels
        plot_data (list): List of plot traces
        moa_data (pandas.DataFrame, optional): MoA data
    
    Returns:
        list: List of button configurations for MoA filtering
    """
    moa_buttons = []
    
    if moa_data is not None and 'MoA' in visualization_df.columns:
        unique_moas = visualization_df['MoA'].dropna().unique().tolist()
        unique_moas.sort()
        print(f"- Number of unique MoAs: {len(unique_moas)}")
        
        # Add "All" button
        moa_buttons.append({
            'args': [{'visible': [True] * len(plot_data)}],
            'label': 'All MOAs',
            'method': 'restyle'
        })
        
        # Add a button for each MOA
        for moa in unique_moas:
            # For each MOA, we need to determine which traces should be visible
            visibility = []
            for cluster in unique_clusters:
                # Get the data for this cluster
                cluster_data = visualization_df[visualization_df['cluster'] == cluster]
                
                # Check if this cluster has any drugs with this MOA
                has_moa = False
                if 'MoA' in cluster_data.columns:
                    has_moa = (cluster_data['MoA'] == moa).any()
                
                # If this cluster has drugs with this MOA, make it visible
                visibility.append(has_moa)
            
            moa_buttons.append({
                'args': [{'visible': visibility}],
                'label': moa,
                'method': 'restyle'
            })
    
    return moa_buttons