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
        
        {get_javascript_functions()}
    </script>
</body>
</html>"""

    # Extract unique MOAs and replace the placeholder in JavaScript
    unique_moas = extract_unique_moas()
    html_content = html_content.replace('var uniqueMoas = UNIQUE_MOAS;', f'var uniqueMoas = {json.dumps(unique_moas)};')
    
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
        moa_distribution_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'results', 'moa_cluster_distribution.csv')
        if os.path.exists(moa_distribution_path):
            moa_dist_df = pd.read_csv(moa_distribution_path)
            unique_moas = moa_dist_df['MOA'].tolist()
    except Exception as e:
        print(f"Warning: Could not extract unique MOAs: {e}")
    
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

def create_default_template():
    """Create a default HTML template for visualization.
    
    This function provides a simplified template when no specific
    visualization data is available.
    
    Returns:
        str: Path to the generated default HTML file
    """
    html_content = """<!DOCTYPE html>
<html>
<head>
    <title>Drug Clustering Analysis - Default Template</title>
    <style>
    body {
        font-family: Arial, sans-serif;
        margin: 20px;
        line-height: 1.6;
    }
    .container {
        max-width: 800px;
        margin: 0 auto;
    }
    .message {
        padding: 20px;
        background-color: #f8f9fa;
        border-radius: 5px;
        border-left: 5px solid #6c757d;
    }
    </style>
</head>
<body>
    <div class="container">
        <h1>Drug Clustering Analysis</h1>
        <div class="message">
            <h2>Default Visualization</h2>
            <p>This is a default template. No specific clustering data has been provided for visualization.</p>
            <p>To generate a complete visualization, please run the clustering analysis first.</p>
        </div>
    </div>
</body>
</html>"""

    # Write the HTML to a file
    return write_html_to_file(html_content)