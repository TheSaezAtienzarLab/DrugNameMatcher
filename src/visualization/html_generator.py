"""
HTML generator for visualization.

This module provides functions to generate HTML for visualizing 
drug clustering results.
"""

import os
import json
import pandas as pd
from .plotting import get_javascript_functions, get_css_styles

def generate_html(visualization_data):
    """Create an enhanced visualization HTML file with interactive 3D PCA plot.
    
    Args:
        visualization_data (dict): Visualization data from create_visualization_data
    
    Returns:
        str: Path to the generated HTML file
    """
    import os
    import json
    import pandas as pd
    
    # Define strong, distinct colors for the clusters
    cluster_colors = [
        'rgb(31, 119, 180)',   # Blue
        'rgb(255, 127, 14)',   # Orange
        'rgb(44, 160, 44)',    # Green
        'rgb(214, 39, 40)',    # Red
        'rgb(148, 103, 189)'   # Purple
    ]
    
    # Create MOA distribution table HTML
    moa_table_html = create_moa_table_html(visualization_data)
    
    # Extract unique MOAs directly
    unique_moas = extract_unique_moas()
    moa_array_str = json.dumps(unique_moas)
    
    # Get the JavaScript code and replace the MOA placeholder with our MOA list
    js_functions = get_javascript_functions()
    js_functions = js_functions.replace('var uniqueMoas = [];', f'var uniqueMoas = {moa_array_str};')
    
    # Create the HTML content with enhanced MoA highlighting
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Drug Clustering Analysis</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
    {get_css_styles()}
    </style>
</head>
<body>
    <div class="container">
        <h1>Drug Clustering Analysis</h1>
        
        <div class="controls">
            <div class="control-group">
                <select id="moa-select">
                    <option value="">Select MoA...</option>
                </select>
                <button id="highlight-btn">Highlight</button>
                <button id="reset-btn" class="reset">Reset View</button>
            </div>
            
            <div class="checkbox-container">
                <input type="checkbox" id="color-by-cluster" checked>
                <label for="color-by-cluster">Color by cluster</label>
            </div>
            
            <div class="checkbox-container">
                <input type="checkbox" id="show-connections">
                <label for="show-connections">Show connections between related drugs</label>
            </div>
            
            <div class="slider-container">
                <label for="proximity-slider">Proximity threshold:</label>
                <input type="range" id="proximity-slider" min="0.1" max="2" step="0.1" value="0.5">
                <span id="proximity-value">0.5</span>
            </div>
        </div>
        
        <div id="highlight-info" class="highlight-info">
            Currently highlighting: <span id="current-moa">None</span>
        </div>
        
        <div id="plot" class="plot-container"></div>
        
        <div class="stats-container">
            <h2>Cluster Distribution</h2>
            <p>Number of clusters: {visualization_data['cluster_stats']['n_clusters']}</p>
            <p>Cluster sizes: {visualization_data['cluster_stats']['sizes']}</p>
            
            <h2>PCA Information</h2>
            <p>Explained variance: {[round(v*100, 2) for v in visualization_data['pca_info']['explained_variance']]}</p>
        </div>
        
        {moa_table_html}
    </div>

    <script>
        // Load the visualization data
        var plotData = {json.dumps(visualization_data['data'])};
        var layout = {json.dumps(visualization_data['layout'])};
        var clusterColors = {json.dumps(cluster_colors)};
        
        {js_functions}
    </script>
</body>
</html>"""

    # Write the HTML to a file
    output_path = write_html_to_file(html_content)
    
    return output_path

def create_moa_table_html(visualization_data):
    """Create HTML table for MOA distribution.
    
    Args:
        visualization_data (dict): Visualization data
    
    Returns:
        str: HTML for MOA distribution table
    """
    moa_table_html = """
    <div class="moa-distribution">
        <h2>MOA Distribution Across Clusters</h2>
        <p>This table shows how drugs with the same Mechanism of Action (MOA) are distributed across different clusters.</p>
    """
    
    # Check if we have MOA data in the results CSV
    moa_distribution_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'results', 'moa_cluster_distribution.csv')
    
    if os.path.exists(moa_distribution_path):
        try:
            # Load the MOA distribution data
            moa_dist_df = pd.read_csv(moa_distribution_path)
            
            if moa_dist_df.empty:
                moa_table_html += "<p>No MOA distribution data available.</p>"
            else:
                # Create the table
                moa_table_html += """
                <table>
                    <tr>
                        <th>MOA</th>
                        <th>Total Drugs</th>
                        <th>Cluster Distribution</th>
                    </tr>
                """
                
                # Add rows for each MOA
                for _, row in moa_dist_df.iterrows():
                    moa = row['MOA']
                    count = row['Count']
                    
                    # Create cluster distribution text
                    cluster_dist = []
                    for i in range(visualization_data['cluster_stats']['n_clusters']):
                        col_name = f'Cluster_{i}'
                        if col_name in row and row[col_name] > 0:
                            percentage = (row[col_name] / count) * 100
                            cluster_dist.append(f"Cluster {i}: {int(row[col_name])} ({percentage:.1f}%)")
                    
                    moa_table_html += f"""
                    <tr>
                        <td>{moa}</td>
                        <td>{int(count)}</td>
                        <td>{', '.join(cluster_dist)}</td>
                    </tr>
                    """
                
                moa_table_html += "</table>"
        except Exception as e:
            moa_table_html += f"<p>Error loading MOA distribution: {str(e)}</p>"
    else:
        moa_table_html += "<p>No MOA distribution data available.</p>"
    
    moa_table_html += "</div>"
    return moa_table_html

def extract_unique_moas():
    """Extract unique MOAs from the distribution data.
    
    Returns:
        list: List of unique MOAs
    """
    unique_moas = []
    try:
        # Try to read from the MOA distribution file
        moa_distribution_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'results', 'moa_cluster_distribution.csv')
        if os.path.exists(moa_distribution_path):
            moa_dist_df = pd.read_csv(moa_distribution_path)
            if 'MOA' in moa_dist_df.columns:
                unique_moas = moa_dist_df['MOA'].tolist()
                print(f"Extracted {len(unique_moas)} MOAs from distribution file")
            else:
                print("Warning: MOA column not found in distribution file")
        else:
            # If distribution file doesn't exist, try to read from clustering results
            results_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'results', 'clustering_results.csv')
            if os.path.exists(results_path):
                results_df = pd.read_csv(results_path)
                if 'MoA' in results_df.columns:
                    unique_moas = results_df['MoA'].dropna().unique().tolist()
                    print(f"Extracted {len(unique_moas)} MOAs from clustering results")
                else:
                    print("Warning: MoA column not found in clustering results")
    except Exception as e:
        print(f"Warning: Could not extract unique MOAs: {e}")
    
    # Sort alphabetically for better usability
    unique_moas.sort()
    return unique_moas

def write_html_to_file(html_content):
    """Write HTML content to a file.
    
    Args:
        html_content (str): HTML content
    
    Returns:
        str: Path to the written file
    """
    # Write the HTML to a file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    output_path = os.path.join(project_root, 'results', 'visualization.html')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    print(f"Writing HTML to {output_path}")
    with open(output_path, 'w') as f:
        f.write(html_content)
    
    # Debug: Check if HTML was written successfully
    if os.path.exists(output_path):
        html_size = os.path.getsize(output_path)
        print(f"HTML file created successfully ({html_size} bytes)")
    else:
        print("Error: HTML file was not created")
    
    return output_path