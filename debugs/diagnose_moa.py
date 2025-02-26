"""
Utility script to diagnose MOA data issues and fix them.
"""

import os
import pandas as pd
import numpy as np

def main():
    print("MOA Data Diagnosis Utility")
    print("=========================")
    
    # Check if the MOA file exists
    moa_path = 'final_output/all_matched_drugs.csv'
    if not os.path.exists(moa_path):
        print(f"Error: MOA file not found at {moa_path}")
        return
    
    # Load the MOA data
    print(f"Loading MOA data from {moa_path}")
    try:
        moa_data = pd.read_csv(moa_path)
        print(f"Successfully loaded {len(moa_data)} rows of MOA data")
        
        # Display column information
        print("\nColumns in MOA data:")
        for col in moa_data.columns:
            print(f"- {col}: {moa_data[col].dtype}")
            
        # Check for MOA column
        moa_column = None
        for col in moa_data.columns:
            if 'moa' in col.lower() or 'mechanism' in col.lower():
                moa_column = col
                break
        
        if moa_column:
            print(f"\nFound MOA column: {moa_column}")
            # Check for non-null values
            non_null_count = moa_data[moa_column].notna().sum()
            print(f"- Contains {non_null_count} non-null values ({non_null_count/len(moa_data)*100:.1f}%)")
            
            # Get unique MOA values
            unique_moas = moa_data[moa_column].dropna().unique()
            print(f"- Contains {len(unique_moas)} unique MOA values")
            print("- Sample MOAs:", ", ".join(str(x) for x in unique_moas[:5]))
        else:
            print("\nWarning: No column identified as MOA found in the data")
        
        # Check for drug name/GENERIC_NAME column
        drug_name_col = None
        for col_name in ['GENERIC_NAME', 'drug_name', 'name', 'drug']:
            if col_name in moa_data.columns:
                drug_name_col = col_name
                break
                
        if drug_name_col:
            print(f"\nFound drug name column: {drug_name_col}")
            
            # Check if it's set as index
            if moa_data.index.name == drug_name_col:
                print("- Already set as index")
            else:
                print("- Not set as index - this might cause matching issues")
                
                # Check if the column has duplicates
                dupe_count = moa_data[drug_name_col].duplicated().sum()
                if dupe_count > 0:
                    print(f"- Warning: Contains {dupe_count} duplicate drug names")
                else:
                    print("- No duplicates found, can be safely set as index")
                    
                # Suggest fixing
                print("\nSuggested fix: Set drug name as index and save:")
                print("moa_data = moa_data.set_index('GENERIC_NAME')")
                print("moa_data.to_csv('final_output/all_matched_drugs_fixed.csv')")
        else:
            print("\nWarning: No drug name column identified")
            
        # Check for clustering results
        results_path = 'results/clustering_results.csv'
        if os.path.exists(results_path):
            print("\nChecking clustering results...")
            results_df = pd.read_csv(results_path)
            
            # Check for index column
            if 'Unnamed: 0' in results_df.columns:
                print("- Found drug names in 'Unnamed: 0' column")
                results_df = results_df.set_index('Unnamed: 0')
            
            # Check for MOA column
            if 'MoA' in results_df.columns:
                print("- MOA column exists in clustering results")
                non_null = results_df['MoA'].notna().sum()
                print(f"- Contains {non_null} non-null MOA values ({non_null/len(results_df)*100:.1f}%)")
            else:
                print("- No MOA column found in clustering results")
            
            # Check if drug names match
            if drug_name_col:
                if moa_data.index.name == drug_name_col:
                    moa_names = set(moa_data.index)
                else:
                    moa_names = set(moa_data[drug_name_col])
                    
                result_names = set(results_df.index)
                common_names = moa_names.intersection(result_names)
                
                print(f"\nName matching analysis:")
                print(f"- MOA data has {len(moa_names)} drug names")
                print(f"- Clustering results has {len(result_names)} drug names")
                print(f"- Found {len(common_names)} matching drug names")
                
                if len(common_names) < min(len(moa_names), len(result_names)) * 0.5:
                    print("\nWarning: Low name matching rate. Possible case sensitivity or formatting issues.")
                    
                    # Sample some names for comparison
                    print("\nSample name comparison:")
                    moa_sample = list(moa_names)[:5]
                    result_sample = list(result_names)[:5]
                    
                    print("MOA data names:", moa_sample)
                    print("Result names:", result_sample)
                    
                    # Check for case sensitivity issues
                    moa_lower = {n.lower() for n in moa_names if isinstance(n, str)}
                    result_lower = {n.lower() for n in result_names if isinstance(n, str)}
                    common_lower = moa_lower.intersection(result_lower)
                    
                    if len(common_lower) > len(common_names):
                        print(f"\nFound {len(common_lower)} matches when ignoring case - case sensitivity is likely an issue")
                        print("Suggested fix: Convert both indices to lowercase before joining")
        else:
            print(f"\nClustering results file not found at {results_path}")
        
        # Check for MOA distribution file
        moa_dist_path = 'results/moa_cluster_distribution.csv'
        if os.path.exists(moa_dist_path):
            print("\nChecking MOA distribution file...")
            try:
                moa_dist = pd.read_csv(moa_dist_path)
                print(f"- Contains {len(moa_dist)} MOA entries")
                if len(moa_dist) == 0:
                    print("- File exists but is empty (only headers)")
                if 'MOA' in moa_dist.columns:
                    print(f"- MOA column exists with {moa_dist['MOA'].nunique()} unique values")
                else:
                    print("- MOA column missing from distribution file")
            except Exception as e:
                print(f"- Error reading MOA distribution file: {e}")
        else:
            print(f"\nMOA distribution file not found at {moa_dist_path}")
            
    except Exception as e:
        print(f"Error processing MOA data: {e}")

if __name__ == "__main__":
    main()