import os
import pandas as pd
import numpy as np

def load_drug_pathway_data(directory='drugs_moable'):
    """Load drug pathway data from CSV files."""
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
    
    return final_matrix, drugs, pathways

def load_moa_data(filepath='final_output/all_matched_drugs.csv'):
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