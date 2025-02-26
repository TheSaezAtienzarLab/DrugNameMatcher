"""
Utility script to debug and fix the hover text in the visualization HTML file.
This script checks if the MOA information is correctly included in the plot data.
"""

import os
import json
import re
import pandas as pd

def debug_hover_text():
    print("===== Debugging Hover Text in Visualization =====")
    
    # Path to the HTML file
    html_path = os.path.join('results', 'visualization.html')
    
    if not os.path.exists(html_path):
        print(f"Error: Visualization file not found at {html_path}")
        return
    
    # Read the HTML file
    with open(html_path, 'r') as f:
        html_content = f.read()
    
    # Extract the plot data
    plot_data_match = re.search(r'var plotData = (\[.*?\]);', html_content, re.DOTALL)
    if not plot_data_match:
        print("Error: Could not find plot data in HTML file")
        return
    
    # Try to parse the plot data
    try:
        plot_data_str = plot_data_match.group(1)
        plot_data = json.loads(plot_data_str)
        
        print(f"Found {len(plot_data)} traces in plot data")
        
        # Check text/hover information in each trace
        hover_text_issues = False
        
        for i, trace in enumerate(plot_data):
            print(f"\nTrace {i}: {trace.get('name', 'Unnamed')}")
            
            if 'text' not in trace:
                print("  Warning: No 'text' field found in trace")
                hover_text_issues = True
                continue
            
            # Sample a few texts
            sample_texts = trace['text'][:min(3, len(trace['text']))]
            print(f"  Sample texts ({len(trace['text'])} total):")
            
            moa_count = 0
            for text in sample_texts:
                print(f"    {text}")
                if 'MoA:' in text:
                    moa_count += 1
            
            # Check if texts contain MOA info
            if moa_count == 0:
                print("  Warning: No MOA information found in sample texts")
                hover_text_issues = True
        
        if hover_text_issues:
            print("\nIssues found with hover text. The MOA information might be missing or formatted incorrectly.")
            
            # Try to fix the issue
            print("\n===== Attempting to fix hover text =====")
            
            # Load clustering results to get MOA data
            results_path = os.path.join('results', 'clustering_results.csv')
            if os.path.exists(results_path):
                print(f"Loading clustering results from {results_path}")
                results_df = pd.read_csv(results_path)
                
                # Set index if needed
                if 'Unnamed: 0' in results_df.columns:
                    results_df.set_index('Unnamed: 0', inplace=True)
                
                # Check if MOA data is available
                if 'MoA' in results_df.columns:
                    print(f"Found MOA data for {results_df['MoA'].notna().sum()} drugs")
                    
                    # Create a dictionary of drug to MOA
                    drug_to_moa = {}
                    for drug, row in results_df.iterrows():
                        if pd.notna(row.get('MoA')):
                            drug_to_moa[str(drug)] = row['MoA']
                    
                    # Check if we have fixed text data available
                    any_fixed = False
                    
                    # Try to fix the hover text in each trace
                    for i, trace in enumerate(plot_data):
                        if 'text' in trace and len(trace['text']) > 0:
                            # Check if the current text already has MOA info
                            has_moa = any('MoA:' in str(t) for t in trace['text'][:5])
                            
                            if not has_moa:
                                # Try to add MOA information
                                new_texts = []
                                for text in trace['text']:
                                    drug_name = text.split('<br>')[0] if '<br>' in text else text
                                    if drug_name in drug_to_moa:
                                        moa = drug_to_moa[drug_name]
                                        new_text = f"{drug_name}<br>MoA: {moa}<br>Cluster: {trace.get('name', '').split()[-1]}"
                                        new_texts.append(new_text)
                                    else:
                                        new_texts.append(text)
                                
                                # Update trace with new texts
                                plot_data[i]['text'] = new_texts
                                any_fixed = True
                    
                    if any_fixed:
                        # Update the HTML with fixed plot data
                        new_plot_data_str = json.dumps(plot_data)
                        new_html_content = html_content.replace(plot_data_str, new_plot_data_str)
                        
                        # Write the updated HTML
                        with open(html_path, 'w') as f:
                            f.write(new_html_content)
                        
                        print("Updated HTML file with fixed hover text")
                    else:
                        print("No fixes needed or applied to hover text")
                else:
                    print("MOA column not found in clustering results")
            else:
                print(f"Clustering results file not found at {results_path}")
        else:
            print("\nHover text appears to be correct with MOA information included.")
    
    except Exception as e:
        print(f"Error processing plot data: {e}")

if __name__ == "__main__":
    debug_hover_text()