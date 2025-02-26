"""
Drug Clustering Analysis - Simplified Version

This script performs clustering analysis on drug pathway data and creates
an interactive visualization.
"""

import os
import pandas as pd
import numpy as np
import json
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score
from kneed import KneeLocator

# ---- DATA LOADING ----

def load_drug_pathway_data(directory='drugs_data'):
    """Load drug pathway data from CSV files."""
    print("Loading drug pathway data...")
    drug_pathway_matrix = {}
    pathway_set = set()
    
    # Check if directory exists
    if not os.path.exists(directory):
        print(f"Error: Directory {directory} not found.")
        return None, None, None
    
    files = [f for f in os.listdir(directory) if f.endswith('.csv')]
    if not files:
        print(f"Error: No CSV files found in {directory}.")
        return None, None, None
    
    for filename in files:
        drug_name = filename[:-4]
        try:
            df = pd.read_csv(os.path.join(directory, filename))
            if df.empty or 'Term' not in df.columns or 'NES' not in df.columns:
                print(f"Warning: File {filename} has invalid format. Skipping.")
                continue
            drug_pathway_matrix[drug_name] = dict(zip(df['Term'], df['NES']))
            pathway_set.update(df['Term'])
        except Exception as e:
            print(f"Error reading {filename}: {str(e)}")
            continue
    
    # Create matrix
    pathways = sorted(list(pathway_set))
    drugs = sorted(list(drug_pathway_matrix.keys()))
    final_matrix = pd.DataFrame(index=drugs, columns=pathways)
    
    for drug in drugs:
        for pathway in pathways:
            final_matrix.loc[drug, pathway] = float(drug_pathway_matrix[drug].get(pathway, 0))
    
    print(f"Loaded data for {len(drugs)} drugs and {len(pathways)} pathways")
    return final_matrix, drugs, pathways

def load_moa_data(filepath='drugs_association/all_matched_drugs.csv'):
    """Load mechanism of action data."""
    try:
        moa_data = pd.read_csv(filepath)
        # Set index to drug name for easier merging
        if 'GENERIC_NAME' in moa_data.columns:
            moa_data = moa_data.set_index('GENERIC_NAME')
        print(f"Loaded MOA data for {len(moa_data)} drugs")
        return moa_data
    except Exception as e:
        print(f"Warning: Could not load MOA data: {str(e)}")
        print("Continuing without MOA information...")
        return None

# ---- ANALYSIS ----

def perform_pca(data_matrix, n_components=3):
    """Perform PCA on the data matrix."""
    print("\nPerforming PCA...")
    # Scale the data
    scaled_data = StandardScaler().fit_transform(data_matrix)
    
    # Apply PCA
    pca = PCA(n_components=n_components)
    pca_result = pca.fit_transform(scaled_data)
    
    # Create results dataframe
    results_df = pd.DataFrame(
        data=pca_result, 
        columns=[f'PC{i+1}' for i in range(n_components)], 
        index=data_matrix.index
    )
    
    print(f"PCA explained variance: {pca.explained_variance_ratio_ * 100}")
    return results_df, pca

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
    print("\nPerforming KMeans clustering...")
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

def analyze_clusters(data_matrix, labels):
    """Analyze clusters and extract characteristics."""
    print("\nAnalyzing clusters...")
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

# ---- EXPORT FUNCTIONALITY ----

def export_results(results_df, labels, cluster_stats, moa_data=None):
    """Export clustering results to CSV files."""
    print("\nExporting results...")
    # Create results directory if it doesn't exist
    os.makedirs('results', exist_ok=True)
    
    # Create a copy of the results dataframe with cluster labels
    export_df = results_df.copy()
    export_df['cluster'] = labels
    
    # Add MoA information if available
    if moa_data is not None:
        # Ensure index alignment for joining
        export_df.index = export_df.index.astype(str)
        moa_data_copy = moa_data.copy()
        moa_data_copy.index = moa_data_copy.index.astype(str)
        
        # Find the MoA column - it might be named differently
        moa_column = None
        for col in moa_data_copy.columns:
            if 'moa' in col.lower() or 'mechanism' in col.lower():
                moa_column = col
                break
        
        if moa_column:
            # Join only the MoA column
            export_df = export_df.join(moa_data_copy[moa_column], how='left')
            # Rename to standardize
            export_df.rename(columns={moa_column: 'MoA'}, inplace=True)
            print(f"Added MOA information to {export_df['MoA'].notna().sum()} drugs")
    
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
            if total_count < 2:
                continue
                
            row = {'MOA': moa, 'Count': total_count}
            
            # Count drugs in each cluster
            for cluster in range(cluster_stats['n_clusters']):
                cluster_count = len(moa_drugs[moa_drugs['cluster'] == cluster])
                row[f'Cluster_{cluster}'] = cluster_count
            
            # Add this MOA row to our distribution dataframe
            moa_distribution = pd.concat([moa_distribution, pd.DataFrame([row])], ignore_index=True)
        
        # Sort by total count
        if not moa_distribution.empty:
            moa_distribution = moa_distribution.sort_values('Count', ascending=False)
            moa_distribution.to_csv('results/moa_cluster_distribution.csv', index=False)
            print(f"MOA cluster distribution saved with {len(moa_distribution)} MOAs")
        else:
            pd.DataFrame(columns=['MOA', 'Count']).to_csv('results/moa_cluster_distribution.csv', index=False)
    
    return export_df

# ---- VISUALIZATION ----

def create_visualization_data(results_df, pca, labels, cluster_stats, moa_data=None):
    """Create data for visualization."""
    print("\nCreating visualization data...")
    
    # Ensure we have a copy of the original data with cluster labels
    visualization_df = results_df.copy()
    visualization_df['cluster'] = labels
    
    # Add MoA information if available
    if moa_data is not None:
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
                'color': cluster_colors.get(cluster, f'rgb({np.random.randint(0, 255)}, {np.random.randint(0, 255)}, {np.random.randint(0, 255)})'),
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
    
    return {
        'data': plot_data,
        'layout': layout,
        'cluster_stats': cluster_stats,
        'pca_info': {
            'explained_variance': pca.explained_variance_ratio_.tolist()
        }
    }

def generate_html(visualization_data, results_df, unique_moas=None):
    """Generate HTML visualization."""
    print("\nGenerating HTML visualization...")
    
    # Get unique MOAs if not provided
    if unique_moas is None:
        try:
            moa_dist_path = 'results/moa_cluster_distribution.csv'
            if os.path.exists(moa_dist_path):
                moa_df = pd.read_csv(moa_dist_path)
                unique_moas = moa_df['MOA'].tolist() if 'MOA' in moa_df.columns else []
            elif 'MoA' in results_df.columns:
                unique_moas = results_df['MoA'].dropna().unique().tolist()
            else:
                unique_moas = []
        except Exception:
            unique_moas = []
    
    # Create MOA distribution table HTML
    moa_table_html = create_moa_table_html(visualization_data, unique_moas)
    
    # CSS and JavaScript code
    css_styles = """
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
    """
    
    js_functions = """
    // Store the original plot data for reset functionality
    var originalPlotData = JSON.parse(JSON.stringify(plotData));
    
    // Create the 3D scatter plot
    Plotly.newPlot('plot', plotData, layout, {responsive: true});
    
    // Populate the MoA dropdown
    var moaSelect = document.getElementById('moa-select');
    var uniqueMoas = """ + json.dumps(unique_moas) + """;
    
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
    
    // Show connections checkbox handler
    document.getElementById('show-connections').addEventListener('change', function() {
        var selectedMoa = moaSelect.value;
        if (selectedMoa) {
            if (this.checked) {
                showConnectionsBetweenRelatedDrugs(selectedMoa);
            } else {
                // Just re-highlight without connections
                highlightMoa(selectedMoa);
            }
        }
    });
    
    // Color by cluster checkbox handler
    document.getElementById('color-by-cluster').addEventListener('change', function() {
        if (!this.checked) {
            this.checked = true;
            alert("The 'Color by cluster' feature cannot be disabled as it's essential for visualizing cluster relationships.");
        }
    });
    
    // Function to highlight drugs with the selected MoA
    function highlightMoa(moa) {
        // Create a deep copy of the plot data
        var newData = JSON.parse(JSON.stringify(originalPlotData));
        var highlightInfo = document.getElementById('highlight-info');
        var currentMoa = document.getElementById('current-moa');
        
        // Show the highlight info box
        highlightInfo.style.display = 'block';
        currentMoa.textContent = moa;
        
        // For each cluster trace
        for (var i = 0; i < newData.length; i++) {
            if (newData[i].text) {
                var highlightedIndices = [];
                var nonHighlightedIndices = [];
                
                // Identify which points have the selected MoA
                for (var j = 0; j < newData[i].text.length; j++) {
                    var text = newData[i].text[j];
                    if (text.includes('MoA: ' + moa)) {
                        highlightedIndices.push(j);
                    } else {
                        nonHighlightedIndices.push(j);
                    }
                }
                
                // If we have any highlighted points in this cluster
                if (highlightedIndices.length > 0) {
                    // Create two separate traces - one for highlighted points and one for faded points
                    var highlightedTrace = {
                        type: 'scatter3d',
                        mode: 'markers',
                        name: newData[i].name + ' (Highlighted)',
                        marker: {
                            size: newData[i].marker.size,
                            color: newData[i].marker.color,
                            line: newData[i].marker.line,
                            opacity: 1.0
                        },
                        x: highlightedIndices.map(idx => newData[i].x[idx]),
                        y: highlightedIndices.map(idx => newData[i].y[idx]),
                        z: highlightedIndices.map(idx => newData[i].z[idx]),
                        text: highlightedIndices.map(idx => newData[i].text[idx]),
                        hoverinfo: 'text',
                        showlegend: false
                    };
                    
                    var fadedTrace = {
                        type: 'scatter3d',
                        mode: 'markers',
                        name: newData[i].name + ' (Faded)',
                        marker: {
                            size: newData[i].marker.size,
                            color: newData[i].marker.color,
                            line: newData[i].marker.line,
                            opacity: 0.2
                        },
                        x: nonHighlightedIndices.map(idx => newData[i].x[idx]),
                        y: nonHighlightedIndices.map(idx => newData[i].y[idx]),
                        z: nonHighlightedIndices.map(idx => newData[i].z[idx]),
                        text: nonHighlightedIndices.map(idx => newData[i].text[idx]),
                        hoverinfo: 'text',
                        showlegend: false
                    };
                    
                    // Replace the original trace with the two new ones
                    newData[i] = highlightedTrace;
                    if (nonHighlightedIndices.length > 0) {
                        newData.push(fadedTrace);
                    }
                } else {
                    // If no highlighted points in this cluster, just fade the entire cluster
                    newData[i].marker.opacity = 0.2;
                }
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
        var newData = [];
        var relatedDrugs = [];
        
        // First collect all the currently displayed data (which may already have highlighting)
        var displayedData = document.getElementById('plot').data;
        for (var i = 0; i < displayedData.length; i++) {
            newData.push(displayedData[i]);
        }
        
        // Find all drugs with the selected MoA across all traces
        for (var i = 0; i < originalPlotData.length; i++) {
            if (originalPlotData[i].text) {
                for (var j = 0; j < originalPlotData[i].text.length; j++) {
                    var text = originalPlotData[i].text[j];
                    
                    if (text.includes('MoA: ' + moa)) {
                        relatedDrugs.push({
                            x: originalPlotData[i].x[j],
                            y: originalPlotData[i].y[j],
                            z: originalPlotData[i].z[j],
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
        // Update the plot with the original data
        Plotly.react('plot', originalPlotData, layout);
        
        // Hide the highlight info box
        document.getElementById('highlight-info').style.display = 'none';
        
        // Reset the MoA dropdown
        document.getElementById('moa-select').value = '';
    }
    """
    
    # Create the HTML content
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Drug Clustering Analysis</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
    {css_styles}
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
        
        {js_functions}
    </script>
</body>
</html>"""

    # Write the HTML to a file
    os.makedirs('results', exist_ok=True)
    output_path = os.path.join('results', 'visualization.html')
    
    with open(output_path, 'w') as f:
        f.write(html_content)
    
    print(f"Visualization saved to {output_path}")
    return output_path

def create_moa_table_html(visualization_data, unique_moas=None):
    """Create HTML table for MOA distribution."""
    moa_table_html = """
    <div class="moa-distribution">
        <h2>MOA Distribution Across Clusters</h2>
        <p>This table shows how drugs with the same Mechanism of Action (MOA) are distributed across different clusters.</p>
    """
    
    # Check if we have MOA data in the results CSV
    moa_distribution_path = 'results/moa_cluster_distribution.csv'
    
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

# ---- MAIN FUNCTION ----

def main():
    """Main function to run the complete drug clustering analysis pipeline."""
    # Load and prepare data
    final_matrix, drugs, pathways = load_drug_pathway_data('drugs_data')
    if final_matrix is None:
        print("Error loading data. Exiting.")
        return
    
    # Load MOA data if available
    moa_data = load_moa_data('drugs_association/all_matched_drugs.csv')
    
    # Perform PCA
    results_df, pca = perform_pca(final_matrix)
    
    # Find optimal number of clusters and perform clustering
    optimal_k = find_optimal_k(results_df)
    labels, metrics, kmeans = perform_clustering(results_df, optimal_k)
    
    # Analyze clusters
    characteristics = analyze_clusters(final_matrix, labels)
    
    # Store statistics
    cluster_stats = {
        'n_clusters': len(np.unique(labels)),
        'sizes': pd.Series(labels).value_counts().sort_index().tolist(),
        'metrics': metrics,
        'characteristics': characteristics
    }
    
    # Export results to CSV
    export_df = export_results(results_df, labels, cluster_stats, moa_data)
    
    # Create visualization data
    vis_data = create_visualization_data(results_df, pca, labels, cluster_stats, moa_data)
    
    # Generate HTML visualization
    html_path = generate_html(vis_data, export_df)
    
    print(f"\nAnalysis complete! Open {html_path} to view the results.")
    print("Use 'python view_visualization.py' to open the visualization in your browser.")

if __name__ == "__main__":
    main()