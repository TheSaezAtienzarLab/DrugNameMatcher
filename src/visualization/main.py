"""
Main visualization functionality.

This module combines all visualization components for easier importing 
and provides a convenience function for running the entire visualization
process in one step.
"""

import os
from .data_processing import create_visualization_data
from .html_generator import generate_html
from .templates import create_default_template

def visualize_clustering(results_df, pca, labels, cluster_stats, moa_data=None):
    """Run the complete visualization process in one step.
    
    Args:
        results_df (pandas.DataFrame): PCA results dataframe
        pca (sklearn.decomposition.PCA): PCA model
        labels (numpy.ndarray): Cluster labels
        cluster_stats (dict): Statistics about the clusters
        moa_data (pandas.DataFrame, optional): Mechanism of action data
    
    Returns:
        str: Path to the generated HTML visualization file
    """
    # Create the visualization data
    vis_data = create_visualization_data(results_df, pca, labels, cluster_stats, moa_data)
    
    # Generate the HTML
    html_path = generate_html(vis_data)
    
    # Create a default template if needed
    template_dir = os.path.join(os.path.dirname(html_path), 'templates')
    os.makedirs(template_dir, exist_ok=True)
    template_path = os.path.join(template_dir, 'default_template.html')
    if not os.path.exists(template_path):
        create_default_template(template_path)
    
    return html_path