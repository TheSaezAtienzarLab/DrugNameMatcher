"""
This script directly injects the MOA list into the visualization HTML file.
Run this after the main.py script but before opening the visualization.
"""

import os
import json
import pandas as pd

def update_visualization_html():
    print("Updating visualization HTML with MOA data...")
    
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

if __name__ == "__main__":
    update_visualization_html()