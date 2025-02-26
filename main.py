import os
import pandas as pd
import numpy as np
import json
import re
from src.data_loader import load_drug_pathway_data, load_moa_data
from src.preprocessing import perform_pca
from src.clustering import perform_clustering, find_optimal_k
from src.utils import analyze_clusters, export_results
# Import the visualize_clustering function from the restructured module
from src.visualization.main import visualize_clustering

def update_visualization_html():
    """Update the visualization HTML with MOA data."""
    print("\nUpdating visualization HTML with MOA data...")
    
    # Define file paths
    moa_distribution_path = os.path.join('results', 'moa_cluster_distribution.csv')
    visualization_path = os.path.join('results', 'visualization.html')
    
    # Check if files exist
    if not os.path.exists(moa_distribution_path):
        print(f"Error: MOA distribution file not found at {moa_distribution_path}")
        return False
    
    if not os.path.exists(visualization_path):
        print(f"Error: Visualization HTML file not found at {visualization_path}")
        return False
    
    try:
        # Load MOA data
        moa_df = pd.read_csv(moa_distribution_path)
        if 'MOA' not in moa_df.columns:
            print("Error: MOA column not found in distribution file")
            return False
        
        unique_moas = moa_df['MOA'].tolist()
        print(f"Loaded {len(unique_moas)} MOAs from distribution file")
        
        # Convert to JavaScript array
        moa_array_str = json.dumps(unique_moas)
        
        # Read HTML file
        with open(visualization_path, 'r') as f:
            html_content = f.read()
        
        # Replace the empty MOA array
        if 'var uniqueMoas = [];' in html_content:
            html_content = html_content.replace('var uniqueMoas = [];', f'var uniqueMoas = {moa_array_str};')
            
            # Write updated HTML
            with open(visualization_path, 'w') as f:
                f.write(html_content)
            
            print(f"Successfully updated visualization with {len(unique_moas)} MOAs")
            return True
        else:
            print("Warning: Could not find MOA array placeholder in HTML")
            return False
            
    except Exception as e:
        print(f"Error updating visualization: {e}")
        return False

def inject_moa_hover_text():
    """Inject MOA information into the hover text of the visualization."""
    print("\nInjecting MOA information into visualization hover text...")
    
    # Path to the HTML file
    html_path = os.path.join('results', 'visualization.html')
    
    if not os.path.exists(html_path):
        print(f"Error: Visualization file not found at {html_path}")
        return False
    
    # Read the HTML file
    with open(html_path, 'r') as f:
        html_content = f.read()
    
    # Extract the plot data
    plot_data_match = re.search(r'var plotData = (\[.*?\]);', html_content, re.DOTALL)
    if not plot_data_match:
        print("Error: Could not find plot data in HTML file")
        return False
    
    # Try to parse the plot data
    try:
        plot_data_str = plot_data_match.group(1)
        plot_data = json.loads(plot_data_str)
        
        print(f"Found {len(plot_data)} traces in plot data")
        
        # Load clustering results to get MOA data
        results_path = os.path.join('results', 'clustering_results.csv')
        if not os.path.exists(results_path):
            print(f"Error: Clustering results file not found at {results_path}")
            return False
        
        print(f"Loading clustering results from {results_path}")
        results_df = pd.read_csv(results_path)
        
        # Set index if needed
        if 'Unnamed: 0' in results_df.columns:
            results_df.set_index('Unnamed: 0', inplace=True)
        
        # Check if MOA data is available
        if 'MoA' not in results_df.columns:
            print("Error: MOA column not found in clustering results")
            return False
        
        print(f"Found MOA data for {results_df['MoA'].notna().sum()} drugs")
        
        # Create a dictionary of drug to MOA
        drug_to_moa = {}
        for drug, row in results_df.iterrows():
            if pd.notna(row.get('MoA')):
                drug_to_moa[str(drug)] = row['MoA']
        
        # Check if we have any MOA data
        if not drug_to_moa:
            print("Error: No valid MOA data found in clustering results")
            return False
        
        # Count how many traces need fixing
        need_fixing_count = 0
        for trace in plot_data:
            if 'text' in trace and len(trace['text']) > 0:
                # Check if the current text already has MOA info
                has_moa = any('MoA:' in str(t) for t in trace['text'][:5])
                if not has_moa:
                    need_fixing_count += 1
        
        if need_fixing_count == 0:
            print("All traces already have MOA information. No fixes needed.")
            return True
        
        # Try to fix the hover text in each trace
        for i, trace in enumerate(plot_data):
            if 'text' in trace and len(trace['text']) > 0:
                # Check if the current text already has MOA info
                has_moa = any('MoA:' in str(t) for t in trace['text'][:5])
                
                if not has_moa:
                    print(f"Adding MOA information to trace {i}: {trace.get('name', 'Unnamed')}")
                    
                    # Try to add MOA information
                    new_texts = []
                    matched_count = 0
                    
                    for text in trace['text']:
                        drug_name = text.split('<br>')[0] if '<br>' in text else text
                        if drug_name in drug_to_moa:
                            moa = drug_to_moa[drug_name]
                            new_text = f"{drug_name}<br>MoA: {moa}<br>Cluster: {trace.get('name', '').split()[-1]}"
                            new_texts.append(new_text)
                            matched_count += 1
                        else:
                            # If no MOA found, keep original text but add cluster info
                            if '<br>' not in text:
                                new_text = f"{text}<br>MoA: Unknown<br>Cluster: {trace.get('name', '').split()[-1]}"
                                new_texts.append(new_text)
                            else:
                                new_texts.append(text)
                    
                    # Update trace with new texts
                    plot_data[i]['text'] = new_texts
                    print(f"  Added MOA information to {matched_count} drugs in trace {i}")
        
        # Update the HTML with fixed plot data
        new_plot_data_str = json.dumps(plot_data)
        new_html_content = html_content.replace(plot_data_str, new_plot_data_str)
        
        # Write the updated HTML
        with open(html_path, 'w') as f:
            f.write(new_html_content)
        
        print("Successfully updated HTML file with MOA hover text information")
        return True
    
    except Exception as e:
        print(f"Error injecting MOA hover text: {e}")
        return False

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
    
    # Post-process the HTML file to insert MOA data
    update_visualization_html()
    
    # Inject MOA information into hover text
    inject_moa_hover_text()
    
    print(f"\nAnalysis complete! Open {html_path} to view the results.")
    print("Use 'python view_visualization.py' to open the visualization in your browser.")

if __name__ == "__main__":
    main()