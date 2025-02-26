# Save this as debug_moa_loading.py in your project root
import os
import json
import pandas as pd

def debug_moa_extraction():
    print("===== Debugging MOA Extraction =====")
    
    # Define paths
    moa_dist_path = os.path.join('results', 'moa_cluster_distribution.csv')
    html_path = os.path.join('results', 'visualization.html')
    
    # Check if files exist
    print(f"MOA distribution file exists: {os.path.exists(moa_dist_path)}")
    print(f"Visualization HTML file exists: {os.path.exists(html_path)}")
    
    if os.path.exists(moa_dist_path):
        # Load the MOA distribution data
        try:
            moa_dist_df = pd.read_csv(moa_dist_path)
            print(f"Successfully loaded MOA distribution with {len(moa_dist_df)} rows")
            
            if 'MOA' in moa_dist_df.columns:
                unique_moas = moa_dist_df['MOA'].tolist()
                print(f"Found {len(unique_moas)} MOAs in distribution file")
                print(f"First 5 MOAs: {unique_moas[:5]}")
                
                # Generate the JavaScript array string that should be inserted
                moa_array_str = json.dumps(unique_moas)
                print(f"MOA array string length: {len(moa_array_str)} characters")
                
                # Check if the replacement might be too large for standard string replacement
                if len(moa_array_str) > 10000:
                    print("Warning: MOA array string is very large, may cause issues with string replacement")
                
                # Check if the HTML file has the MOA list
                if os.path.exists(html_path):
                    with open(html_path, 'r') as f:
                        html_content = f.read()
                        
                    if 'var uniqueMoas = [];' in html_content:
                        print("Found empty MOA array in HTML file")
                        print("This suggests the replacement in html_generator.py isn't working")
                    elif 'var uniqueMoas = [' in html_content:
                        # Count the number of MOAs in the HTML file
                        import re
                        moa_list_pattern = re.compile(r'var uniqueMoas = \[(.*?)\];', re.DOTALL)
                        match = moa_list_pattern.search(html_content)
                        if match:
                            moa_list_str = match.group(1)
                            # Count the number of items by counting commas
                            comma_count = moa_list_str.count(',')
                            print(f"Found MOA array in HTML with approximately {comma_count + 1} items")
                        else:
                            print("MOA array found but couldn't extract item count")
                    else:
                        print("Didn't find MOA array in HTML file")
            else:
                print("MOA column not found in distribution file")
        except Exception as e:
            print(f"Error processing MOA distribution: {e}")
    
    # Try to directly fix the issue
    print("\n===== Attempting to fix the issue directly =====")
    try:
        if os.path.exists(moa_dist_path) and os.path.exists(html_path):
            # Load the MOAs
            moa_dist_df = pd.read_csv(moa_dist_path)
            unique_moas = moa_dist_df['MOA'].tolist()
            moa_array_str = json.dumps(unique_moas)
            
            # Read the HTML
            with open(html_path, 'r') as f:
                html_content = f.read()
            
            # Make the replacement
            if 'var uniqueMoas = [];' in html_content:
                html_content = html_content.replace('var uniqueMoas = [];', f'var uniqueMoas = {moa_array_str};')
                
                # Write the updated HTML
                with open(html_path, 'w') as f:
                    f.write(html_content)
                
                print(f"Successfully updated HTML file with {len(unique_moas)} MOAs")
            else:
                print("Couldn't find the MOA array placeholder in HTML")
    except Exception as e:
        print(f"Error fixing HTML file: {e}")

if __name__ == "__main__":
    debug_moa_extraction()