import pandas as pd
import re
from fuzzywuzzy import process, fuzz
import os

def create_vitamin_mappings():
    """Create dictionary of vitamin name mappings"""
    return {
        'vitamin c': 'ascorbic acid',
        'vitamina c': 'ascorbic acid',
        'vitamin b6': 'pyridoxine',
        'vitamina b6': 'pyridoxine',
        'vitamin b1': 'thiamine',
        'vitamina b1': 'thiamine',
        'vitamin d': 'calciferol',
        'vitamina d': 'calciferol',
    }

def create_common_drug_mappings():
    """Create dictionary of common drug name mappings"""
    return {
        'csa': 'cyclosporine',
        'cya': 'cyclosporine',
        'cyclosporin': 'cyclosporine',
        'ciclosporin': 'cyclosporine',
        'ddavp': 'desmopressin',
        'plp': 'pyridoxal phosphate',
        'pyridoxal5p': 'pyridoxal phosphate',
        'pyridoxal 5p': 'pyridoxal phosphate',
    }

def normalize_drug_name(name):
    """
    Enhanced normalization with special cases handling
    """
    if pd.isna(name):
        return ''

    name = str(name).lower()

    # Remove content in parentheses
    name = re.sub(r'\([^)]*\)', '', name)

    # Initial mappings for vitamins and common drugs
    vitamin_mappings = create_vitamin_mappings()
    common_drug_mappings = create_common_drug_mappings()

    # Check if name exists in mappings
    if name.strip() in vitamin_mappings:
        name = vitamin_mappings[name.strip()]
    if name.strip() in common_drug_mappings:
        name = common_drug_mappings[name.strip()]

    # Handle acid variations
    acid_patterns = ['acide', 'ácido', 'acidum', 'säure']
    for pattern in acid_patterns:
        name = name.replace(pattern, 'acid')

    # Chemical nomenclature standardization
    replacements = {
        'l-': '',
        'd-': '',
        'dl-': '',
        'beta-': 'b',
        'alpha-': 'a',
        'gamma-': 'g',
        '-phosphate': 'p',
        '5-phosphate': '5p',
        "5'-phosphate": '5p',
        '-monophosphate': 'p',
        '5-monophosphate': '5p',
        'hydroxy': 'oh',
        'amino': 'nh2',
        'ascorbate': 'ascorbic acid',
        'phosphoric': 'p',
        'carboxylic': 'cooh',
        '1-deamino': '1d',
        '8-d-arginine': '8darg'
    }

    for old, new in replacements.items():
        name = name.replace(old, new)

    # Remove accents and special characters
    name = name.encode('ascii', 'ignore').decode('ascii')

    # Remove special characters except spaces and hyphens
    name = re.sub(r'[^a-z0-9\s\-]', '', name)

    # Replace multiple spaces with single space
    name = re.sub(r'\s+', ' ', name)

    # Strip whitespace
    name = name.strip()

    return name

def get_all_names(row):
    """
    Get all possible names from a row including generic name and synonyms
    """
    names = {normalize_drug_name(row['GENERIC_NAME'])}

    if pd.notna(row['SYNONYMS']):
        # Split synonyms by semicolon and normalize each
        synonyms = str(row['SYNONYMS']).split(';')
        names.update(normalize_drug_name(syn) for syn in synonyms)

        # Add special handling for known patterns in synonyms
        for syn in synonyms:
            # Handle cases where chemical name might be split
            parts = syn.split()
            if len(parts) > 1:
                names.add(normalize_drug_name(''.join(parts)))

    # Remove empty strings
    names = {name for name in names if name}

    return names

def perform_exact_matching(filtered_df, repurposing_df):
    """
    Perform exact matching between filtered drugs and repurposing drugs
    """
    # Create normalized name column for repurposing drugs
    repurposing_df['normalized_name'] = repurposing_df['pert_iname'].apply(normalize_drug_name)

    # Create a dictionary to store all entries for each normalized name
    repurposing_dict = {}
    for _, row in repurposing_df.iterrows():
        norm_name = row['normalized_name']
        if norm_name not in repurposing_dict:
            repurposing_dict[norm_name] = []
        repurposing_dict[norm_name].append({
            'clinical_phase': row['clinical_phase'],
            'moa': row['moa'],
            'target': row['target'],
            'disease_area': row['disease_area'],
            'indication': row['indication'],
            'original_name': row['pert_iname']
        })

    # Initialize new columns in filtered_df
    new_columns = ['clinical_phase', 'moa', 'target', 'disease_area', 'indication', 'matched_name']
    for col in new_columns:
        filtered_df[col] = None

    # Create a column to track matches
    filtered_df['is_matched'] = False

    # Match and merge data
    matches = 0
    synonym_matches = 0
    multiple_matches = 0
    total = len(filtered_df)

    for idx, row in filtered_df.iterrows():
        # Get all possible names for this drug
        all_names = get_all_names(row)

        # Try to match any of the names
        for name in all_names:
            if name in repurposing_dict:
                matches += 1
                if matches > 1:
                    synonym_matches += 1

                # If multiple matches exist, use the first one but log it
                if len(repurposing_dict[name]) > 1:
                    multiple_matches += 1
                    print(f"\nMultiple matches found for {row['GENERIC_NAME']}:")
                    for match in repurposing_dict[name]:
                        print(f"  - {match['original_name']}")

                match_data = repurposing_dict[name][0]
                for col in new_columns[:-1]:
                    filtered_df.at[idx, col] = match_data[col]
                filtered_df.at[idx, 'matched_name'] = match_data['original_name']
                filtered_df.at[idx, 'is_matched'] = True
                break

    # Split into matched and unmatched dataframes
    matched_df = filtered_df[filtered_df['is_matched']].copy()
    unmatched_df = filtered_df[~filtered_df['is_matched']].copy()

    # Remove the tracking column
    matched_df = matched_df.drop('is_matched', axis=1)
    unmatched_df = unmatched_df.drop(['is_matched'] + new_columns, axis=1)

    # Print statistics
    print(f"\nExact Matching complete:")
    print(f"Total drugs in filtered_drugs: {total}")
    print(f"Total matched drugs: {matches}")
    print(f"  - Matched through synonyms: {synonym_matches}")
    print(f"Drugs with multiple matches: {multiple_matches}")
    print(f"Unmatched drugs: {len(unmatched_df)}")

    return matched_df, unmatched_df, repurposing_df

def perform_fuzzy_matching(unmatched_df, repurposing_df, similarity_threshold=80):
    """
    Perform fuzzy matching on unmatched drugs
    """
    # Create lists for fuzzy matching
    unmatched_names = unmatched_df['GENERIC_NAME'].tolist()
    repurposing_names = repurposing_df['pert_iname'].tolist()
    
    # Create a mapping from normalized names to original repurposing data
    repurposing_map = {}
    for _, row in repurposing_df.iterrows():
        repurposing_map[row['pert_iname']] = {
            'clinical_phase': row['clinical_phase'],
            'moa': row['moa'],
            'target': row['target'],
            'disease_area': row['disease_area'],
            'indication': row['indication']
        }
    
    # Perform fuzzy matching
    fuzzy_matches = []
    for name in unmatched_names:
        # Find the best match
        best_match, score = process.extractOne(name, repurposing_names, scorer=fuzz.token_sort_ratio)
        
        # If the score is above threshold, consider it a match
        if score >= similarity_threshold:
            match_data = repurposing_map[best_match]
            fuzzy_matches.append({
                'original_name': name,
                'matched_name': best_match,
                'similarity_score': score,
                'clinical_phase': match_data['clinical_phase'],
                'moa': match_data['moa'],
                'target': match_data['target'],
                'disease_area': match_data['disease_area'],
                'indication': match_data['indication']
            })
    
    # Create DataFrame from fuzzy matches
    fuzzy_matches_df = pd.DataFrame(fuzzy_matches)
    
    return fuzzy_matches_df

def analyze_remaining_unmatched(fuzzy_matches_df, unmatched_df):
    """
    Analyze the drugs that are still unmatched after fuzzy matching
    """
    # Get the drugs that were matched by fuzzy matching
    matched_names = fuzzy_matches_df['original_name'].tolist() if not fuzzy_matches_df.empty else []

    # Get the remaining unmatched drugs
    still_unmatched = unmatched_df[~unmatched_df['GENERIC_NAME'].isin(matched_names)].copy()

    # Analyze patterns in remaining unmatched drugs
    patterns = {
        'peptides': r'peptide|protein|factor|hormone|insulin|globulin',
        'vitamins': r'vitamin|ascorb|folic|thiamin|riboflavin',
        'antibiotics': r'mycin|cillin|cycline',
        'steroids': r'steroid|sterone|sterol',
        'enzymes': r'enzyme|ase$',
        'salts': r'sodium|potassium|chloride|sulfate|phosphate$',
        'acids': r'acid$|acid\s',
        'complex_names': r'\d|[\(\)\[\]]|\-'
    }

    pattern_counts = {k: 0 for k in patterns}
    pattern_examples = {k: [] for k in patterns}

    for _, row in still_unmatched.iterrows():
        name = row['GENERIC_NAME'].lower()
        for pattern_name, pattern in patterns.items():
            if re.search(pattern, name):
                pattern_counts[pattern_name] += 1
                if len(pattern_examples[pattern_name]) < 3:
                    pattern_examples[pattern_name].append(row['GENERIC_NAME'])

    return pattern_counts, pattern_examples, still_unmatched

def drug_matching_pipeline(filtered_drugs_path, repurposing_drugs_path, 
                          output_dir='./', similarity_threshold=80):
    """
    Complete drug matching pipeline combining exact and fuzzy matching
    """
    try:
        print("\n=== STARTING DRUG MATCHING PIPELINE ===\n")
        
        # Create output directories
        final_output_dir = os.path.join(output_dir, "final_output")
        intermediate_output_dir = os.path.join(output_dir, "intermediate_output")
        
        # Create directories if they don't exist
        os.makedirs(final_output_dir, exist_ok=True)
        os.makedirs(intermediate_output_dir, exist_ok=True)
        
        # Read the CSV files
        filtered_df = pd.read_csv(filtered_drugs_path)
        repurposing_df = pd.read_csv(repurposing_drugs_path)
        
        # Step 1: Exact Matching
        print("\n=== STEP 1: EXACT MATCHING ===\n")
        matched_df, unmatched_df, repurposing_df = perform_exact_matching(filtered_df, repurposing_df)
        
        # Save intermediate results
        matched_output_path = f"{intermediate_output_dir}/matched_drugs.csv"
        unmatched_output_path = f"{intermediate_output_dir}/unmatched_drugs.csv"
        matched_df.to_csv(matched_output_path, index=False)
        unmatched_df.to_csv(unmatched_output_path, index=False)
        
        # Step 2: Fuzzy Matching
        print("\n=== STEP 2: FUZZY MATCHING ===\n")
        fuzzy_matches_df = perform_fuzzy_matching(unmatched_df, repurposing_df, similarity_threshold)
        
        # Save fuzzy matches
        fuzzy_output_path = f"{intermediate_output_dir}/fuzzy_matches.csv"
        fuzzy_matches_df.to_csv(fuzzy_output_path, index=False)
        
        # Step 3: Analyze Remaining Unmatched
        print("\n=== STEP 3: ANALYZING REMAINING UNMATCHED DRUGS ===\n")
        pattern_counts, pattern_examples, still_unmatched = analyze_remaining_unmatched(
            fuzzy_matches_df, unmatched_df
        )
        
        # Save remaining unmatched
        remaining_unmatched_path = f"{intermediate_output_dir}/remaining_unmatched.csv"
        still_unmatched.to_csv(remaining_unmatched_path, index=False)
        
        # Combine all matched drugs
        all_matched = pd.concat([
            matched_df,
            fuzzy_matches_df.rename(columns={'original_name': 'GENERIC_NAME'})
        ]) if not fuzzy_matches_df.empty else matched_df
        
        all_matched_path = f"{final_output_dir}/all_matched_drugs.csv"
        all_matched.to_csv(all_matched_path, index=False)
        
        # Print statistics
        print("\nMATCHING STATISTICS:")
        print(f"Originally matched: {len(matched_df)}")
        print(f"Fuzzy matches found: {len(fuzzy_matches_df)}")
        print(f"Total matched: {len(all_matched)}")
        print(f"Still unmatched: {len(still_unmatched)}")
        
        # Print pattern analysis
        print("\nPATTERNS IN REMAINING UNMATCHED DRUGS:")
        for pattern, count in pattern_counts.items():
            if count > 0:
                print(f"\n{pattern.title()} ({count} drugs)")
                print("Examples:", ', '.join(pattern_examples[pattern][:3]))
        
        # Print fuzzy match score distribution if there are any fuzzy matches
        if not fuzzy_matches_df.empty:
            print("\nFUZZY MATCH SCORE DISTRIBUTION:")
            print(fuzzy_matches_df['similarity_score'].describe())
        
        print("\nFiles created:")
        print(f"- Final output:")
        print(f"  - {all_matched_path} (combined exact and fuzzy matches)")
        print(f"- Intermediate output:")
        print(f"  - {matched_output_path} (exact matches)")
        print(f"  - {unmatched_output_path} (drugs without exact matches)")
        print(f"  - {fuzzy_output_path} (fuzzy matches)")
        print(f"  - {remaining_unmatched_path} (drugs still without matches)")
        
        print("\n=== DRUG MATCHING PIPELINE COMPLETED ===\n")
        
        return {
            'matched_df': matched_df,
            'fuzzy_matches_df': fuzzy_matches_df,
            'still_unmatched': still_unmatched,
            'all_matched': all_matched,
            'pattern_counts': pattern_counts,
            'pattern_examples': pattern_examples
        }
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        # You may need to install fuzzywuzzy: pip install fuzzywuzzy python-Levenshtein
        drug_matching_pipeline(
            'filtered_drugs.csv',
            'repurposing_drugs.csv',
            './',
            similarity_threshold=80
        )
    except Exception as e:
        print(f"Error occurred: {str(e)}") 