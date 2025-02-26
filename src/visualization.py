import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import pandas as pd
import plotly.express as px
import random
import json
import os
from jinja2 import Environment, FileSystemLoader, Template

def create_visualization_data(results_df, pca, labels, cluster_stats, moa_data=None):
    """Create data for visualization."""
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
        
        # Define consistent cluster colors - using the same colors as in generate_html
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

def generate_html(visualization_data):
    """Create an enhanced visualization HTML file with interactive 3D PCA plot and spatial relationship tools."""
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
    
    # Create the HTML content with enhanced MoA highlighting
    html_content = """<!DOCTYPE html>
<html>
<head>
    <title>Drug Clustering Analysis</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
            border-radius: 5px;
        }
        h1, h2 {
            color: #333;
        }
        .plot-container {
            height: 600px;
            margin-bottom: 20px;
        }
        .controls {
            background-color: #f0f0f0;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 15px;
        }
        .control-group {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        select {
            padding: 8px;
            border-radius: 4px;
            border: 1px solid #ccc;
            min-width: 200px;
        }
        button {
            padding: 8px 15px;
            border-radius: 4px;
            border: none;
            background-color: #4CAF50;
            color: white;
            cursor: pointer;
            font-weight: bold;
        }
        button:hover {
            background-color: #45a049;
        }
        button.reset {
            background-color: #f44336;
        }
        button.reset:hover {
            background-color: #d32f2f;
        }
        .checkbox-container {
            display: flex;
            align-items: center;
            gap: 5px;
        }
        .slider-container {
            display: flex;
            align-items: center;
            gap: 10px;
            min-width: 250px;
        }
        .slider-container label {
            min-width: 120px;
        }
        input[type="range"] {
            width: 100%;
        }
        .stats-container, .moa-distribution {
            margin: 20px 0;
            padding: 15px;
            background-color: #f9f9f9;
            border-radius: 5px;
            border: 1px solid #ddd;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        th {
            background-color: #f2f2f2;
        }
        .highlight-info {
            margin-top: 10px;
            padding: 10px;
            background-color: #e8f5e9;
            border-radius: 4px;
            border-left: 4px solid #4CAF50;
            display: none;
        }
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
            <p>Number of clusters: CLUSTER_COUNT</p>
            <p>Cluster sizes: CLUSTER_SIZES</p>
            
            <h2>PCA Information</h2>
            <p>Explained variance: PCA_VARIANCE</p>
        </div>
        
        MOA_TABLE_HTML
    </div>

    <script>
        // Load the visualization data
        var plotData = VISUALIZATION_DATA;
        var layout = VISUALIZATION_LAYOUT;
        var clusterColors = CLUSTER_COLORS;
        
        // Store original marker properties for reset
        var originalMarkerProps = [];
        for (var i = 0; i < plotData.length; i++) {
            originalMarkerProps.push({
                size: plotData[i].marker.size,
                opacity: 1.0,
                color: plotData[i].marker.color
            });
        }
        
        // Create the 3D scatter plot
        Plotly.newPlot('plot', plotData, layout, {responsive: true});
        
        // Populate the MoA dropdown
        var moaSelect = document.getElementById('moa-select');
        var uniqueMoas = UNIQUE_MOAS;
        
        // Sort MoAs alphabetically
        uniqueMoas.sort();
        
        // Add options to the dropdown
        uniqueMoas.forEach(function(moa) {
            var option = document.createElement('option');
            option.value = moa;
            option.textContent = moa;
            moaSelect.appendChild(option);
        });
        
        // Highlight button click handler
        document.getElementById('highlight-btn').addEventListener('click', function() {
            var selectedMoa = moaSelect.value;
            if (!selectedMoa) {
                alert('Please select a Mechanism of Action first');
                return;
            }
            
            highlightMoa(selectedMoa);
        });
        
        // Reset button click handler
        document.getElementById('reset-btn').addEventListener('click', function() {
            resetVisualization();
        });
        
        // Update proximity threshold value display
        document.getElementById('proximity-slider').addEventListener('input', function() {
            document.getElementById('proximity-value').textContent = this.value;
        });
        
        // Color by cluster checkbox handler
        document.getElementById('color-by-cluster').addEventListener('change', function() {
            var newData = JSON.parse(JSON.stringify(plotData));
            
            if (!this.checked) {
                // Color by MoA instead of cluster
                var moaColors = {};
                var colorIndex = 0;
                
                for (var i = 0; i < newData.length; i++) {
                    if (newData[i].text) {
                        var colors = [];
                        for (var j = 0; j < newData[i].text.length; j++) {
                            var text = newData[i].text[j];
                            var parts = text.split('<br>');
                            var moa = "Unknown";
                            
                            if (parts.length > 1 && parts[1].startsWith('MoA:')) {
                                moa = parts[1].replace('MoA: ', '');
                            }
                            
                            if (moa !== "Unknown") {
                                if (!moaColors[moa]) {
                                    moaColors[moa] = colorIndex % clusterColors.length;
                                    colorIndex++;
                                }
                                colors.push(clusterColors[moaColors[moa]]);
                            } else {
                                colors.push('rgba(200, 200, 200, 0.7)');
                            }
                        }
                        
                        newData[i].marker.color = colors;
                    }
                }
            } else {
                // Reset to color by cluster
                for (var i = 0; i < newData.length; i++) {
                    newData[i].marker.color = originalMarkerProps[i].color;
                }
            }
            
            Plotly.react('plot', newData, layout);
        });
        
        // Function to highlight drugs with the selected MoA
        function highlightMoa(moa) {
            var newData = JSON.parse(JSON.stringify(plotData));
            var highlightInfo = document.getElementById('highlight-info');
            var currentMoa = document.getElementById('current-moa');
            
            // Show the highlight info box
            highlightInfo.style.display = 'block';
            currentMoa.textContent = moa;
            
            // Modify marker properties for all traces
            for (var i = 0; i < newData.length; i++) {
                if (newData[i].text) {
                    var sizes = [];
                    var opacities = [];
                    
                    for (var j = 0; j < newData[i].text.length; j++) {
                        var text = newData[i].text[j];
                        
                        // Check if this drug has the selected MoA
                        if (text.includes('MoA: ' + moa)) {
                            // Highlighted drugs: larger size, full opacity
                            sizes.push(10);  // Increased size
                            opacities.push(1.0);  // Full opacity
                        } else {
                            // Non-highlighted drugs: normal size, low opacity
                            sizes.push(5);  // Normal size
                            opacities.push(0.2);  // Low opacity
                        }
                    }
                    
                    // Update marker properties
                    newData[i].marker.size = sizes;
                    newData[i].marker.opacity = opacities;
                }
            }
            
            // Update the plot
            Plotly.react('plot', newData, layout);
            
            // Show connections between related drugs if checkbox is checked
            if (document.getElementById('show-connections').checked) {
                showConnectionsBetweenRelatedDrugs(moa);
            }
        }
        
        // Function to show connections between drugs with the same MoA
        function showConnectionsBetweenRelatedDrugs(moa) {
            var newData = JSON.parse(JSON.stringify(plotData));
            var relatedDrugs = [];
            
            // Find all drugs with the selected MoA
            for (var i = 0; i < newData.length; i++) {
                if (newData[i].text) {
                    for (var j = 0; j < newData[i].text.length; j++) {
                        var text = newData[i].text[j];
                        
                        if (text.includes('MoA: ' + moa)) {
                            relatedDrugs.push({
                                x: newData[i].x[j],
                                y: newData[i].y[j],
                                z: newData[i].z[j],
                                name: text.split('<br>')[0]
                            });
                        }
                    }
                }
            }
            
            // Create connections between related drugs
            if (relatedDrugs.length > 1) {
                // Calculate centroid
                var centroid = {x: 0, y: 0, z: 0};
                relatedDrugs.forEach(function(drug) {
                    centroid.x += drug.x;
                    centroid.y += drug.y;
                    centroid.z += drug.z;
                });
                centroid.x /= relatedDrugs.length;
                centroid.y /= relatedDrugs.length;
                centroid.z /= relatedDrugs.length;
                
                // Create lines from each drug to the centroid
                var lines = {
                    type: 'scatter3d',
                    mode: 'lines',
                    name: moa + ' connections',
                    line: {
                        color: 'rgba(100, 200, 100, 0.5)',
                        width: 2
                    },
                    x: [],
                    y: [],
                    z: []
                };
                
                relatedDrugs.forEach(function(drug) {
                    // Add line from drug to centroid
                    lines.x.push(drug.x, centroid.x, null);
                    lines.y.push(drug.y, centroid.y, null);
                    lines.z.push(drug.z, centroid.z, null);
                });
                
                // Add the lines to the plot
                newData.push(lines);
                
                // Add the centroid as a marker
                newData.push({
                    type: 'scatter3d',
                    mode: 'markers',
                    name: moa + ' centroid',
                    marker: {
                        size: 12,
                        color: 'rgba(100, 200, 100, 1)',
                        symbol: 'diamond'
                    },
                    x: [centroid.x],
                    y: [centroid.y],
                    z: [centroid.z],
                    text: [moa + ' centroid'],
                    hoverinfo: 'text'
                });
                
                // Update the plot
                Plotly.react('plot', newData, layout);
            }
        }
        
        // Function to reset the visualization to its original state
        function resetVisualization() {
            var newData = JSON.parse(JSON.stringify(plotData));
            
            // Reset marker properties for all traces
            for (var i = 0; i < newData.length; i++) {
                newData[i].marker.size = originalMarkerProps[i].size;
                newData[i].marker.opacity = 1.0;
                newData[i].marker.color = originalMarkerProps[i].color;
            }
            
            // Hide the highlight info box
            document.getElementById('highlight-info').style.display = 'none';
            
            // Reset the MoA dropdown
            document.getElementById('moa-select').value = '';
            
            // Update the plot
            Plotly.react('plot', newData, layout);
        }
    </script>
</body>
</html>"""

    # Replace placeholders with actual data
    html_content = html_content.replace('CLUSTER_COUNT', str(visualization_data['cluster_stats']['n_clusters']))
    html_content = html_content.replace('CLUSTER_SIZES', str(visualization_data['cluster_stats']['sizes']))
    html_content = html_content.replace('PCA_VARIANCE', str([round(v*100, 2) for v in visualization_data['pca_info']['explained_variance']]))
    html_content = html_content.replace('MOA_TABLE_HTML', moa_table_html)
    html_content = html_content.replace('VISUALIZATION_DATA', json.dumps(visualization_data['data']))
    html_content = html_content.replace('CLUSTER_COLORS', json.dumps(cluster_colors))
    html_content = html_content.replace('VISUALIZATION_LAYOUT', json.dumps(visualization_data['layout']))
    
    # Extract unique MOAs from the data
    unique_moas = []
    try:
        moa_distribution_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'results', 'moa_cluster_distribution.csv')
        if os.path.exists(moa_distribution_path):
            moa_dist_df = pd.read_csv(moa_distribution_path)
            unique_moas = moa_dist_df['MOA'].tolist()
    except Exception as e:
        print(f"Warning: Could not extract unique MOAs: {e}")
    
    html_content = html_content.replace('UNIQUE_MOAS', json.dumps(unique_moas))
    
    # Write the HTML to a file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
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

def create_default_template(template_path):
    """Create a default HTML template for visualization."""
    template_content = """<!DOCTYPE html>
<html>
<head>
    <title>Drug Clustering Analysis</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }
        h1 {
            text-align: center;
            color: #333;
        }
        .stats-container {
            margin: 20px 0;
            padding: 15px;
            background-color: #f9f9f9;
            border-radius: 5px;
            border: 1px solid #ddd;
        }
        .plot-container {
            height: 600px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Drug Clustering Analysis</h1>
        
        <div id="plot" class="plot-container"></div>
        
        <div class="stats-container">
            <h2>Cluster Distribution</h2>
            <p>Number of clusters: {{ cluster_stats.n_clusters }}</p>
            <p>Cluster sizes: {{ cluster_stats.sizes }}</p>
            
            <h2>PCA Information</h2>
            <p>Explained variance: {{ pca_info.explained_variance }}</p>
        </div>
    </div>

    <script>
        // Create the 3D scatter plot
        var data = {{ plot_data|safe }};
        var layout = {{ plot_layout|safe }};
        var config = {{ plot_config|safe }};
        
        Plotly.newPlot('plot', data, layout, config);
        
        // Add event listener for the MoA dropdown if it exists
        if (layout.updatemenus) {
            var dropdown = document.querySelector('.updatemenu-dropdown-button');
            if (dropdown) {
                dropdown.addEventListener('click', function() {
                    var menuItems = document.querySelectorAll('.updatemenu-item');
                    menuItems.forEach(function(item) {
                        item.addEventListener('click', function() {
                            var selectedMoA = this.textContent.trim();
                            filterByMoA(selectedMoA);
                        });
                    });
                });
            }
        }
        
        // Function to filter by MoA
        function filterByMoA(moa) {
            if (moa === 'All MoAs') {
                // Show all data points
                data.forEach(function(trace) {
                    trace.visible = true;
                });
            } else {
                // Filter data points by MoA
                data.forEach(function(trace) {
                    var textArray = trace.text;
                    var newVisibility = [];
                    
                    for (var i = 0; i < textArray.length; i++) {
                        if (textArray[i].includes('MoA: ' + moa)) {
                            newVisibility.push(true);
                        } else {
                            newVisibility.push(false);
                        }
                    }
                    
                    trace.visible = newVisibility.includes(true) ? true : 'legendonly';
                });
            }
            
            Plotly.redraw('plot');
        }
    </script>
</body>
</html>"""

    # Create the directory if it doesn't exist
    os.makedirs(os.path.dirname(template_path), exist_ok=True)
    
    # Write the template to file
    with open(template_path, 'w') as f:
        f.write(template_content) 