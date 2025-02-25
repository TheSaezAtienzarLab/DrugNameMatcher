# Drug Matching Pipeline

A comprehensive Python pipeline for matching drug names between datasets using both exact and fuzzy matching techniques, with advanced normalization and pattern analysis.

## Overview

This script addresses the challenge of matching drug names across different datasets where naming conventions, chemical nomenclature, and synonyms may vary. It implements a three-step approach:

1. **Exact Matching**: Normalizes drug names and performs exact matching
2. **Fuzzy Matching**: Applies similarity-based matching for remaining unmatched drugs
3. **Pattern Analysis**: Analyzes patterns in drugs that couldn't be matched

The pipeline handles various drug naming complexities including:
- Chemical nomenclature variations (L-, D-, alpha-, beta-, etc.)
- Language variations (acid/acide/ácido/acidum)
- Common abbreviations and synonyms
- Special character handling

# Installation

### Clone the repository

    git clone https://github.com/yourusername/drug-matching-pipeline.git

    cd drug-matching-pipeline

# Install required packages

    pip install pandas fuzzywuzzy python-Levenshtein {or}
    conda install pandas fuzzywuzzy python-Levenshtein


## Input Files

The pipeline requires two CSV files:

1. **filtered_drugs.csv**: Contains drug information with at least:
   - `GENERIC_NAME`: Primary drug name
   - `SYNONYMS`: Optional semicolon-separated list of alternative names

2. **repurposing_drugs.csv**: Contains drug repurposing information with at least:
   - `pert_iname`: Drug name
   - `clinical_phase`: Clinical trial phase
   - `moa`: Mechanism of action
   - `target`: Drug target
   - `disease_area`: Disease area
   - `indication`: Medical indication

## Output Structure

The pipeline creates an organized output structure:
```output_directory/

output_directory/

├── **final_output**/

│      └── all_matched_drugs.csv # Combined results from exact and fuzzy matching

└── **intermediate_output**/

     ├── matched_drugs.csv # Drugs matched through exact matching

     ├── unmatched_drugs.csv # Drugs that didn't match exactly

     ├── fuzzy_matches.csv # Drugs matched through fuzzy matching

     └── remaining_unmatched.csv # Drugs that couldn't be matched by any method
```

## Workflow

![Drug Matching Pipeline Workflow](workflow_diagram.png)

1. **Normalization**: Drug names undergo extensive normalization:
   - Lowercase conversion
   - Parenthetical content removal
   - Vitamin and common drug mapping
   - Acid variation standardization
   - Chemical nomenclature normalization
   - Special character removal

2. **Exact Matching**: 
   - Normalized names are compared for exact matches
   - Synonyms are expanded and checked
   - Matched drugs are saved with repurposing information

3. **Fuzzy Matching**:
   - Similarity scores are calculated for unmatched drugs
   - Matches above the similarity threshold are accepted
   - Results are saved with similarity scores

4. **Pattern Analysis**:
   - Remaining unmatched drugs are analyzed for patterns
   - Drugs are categorized (peptides, vitamins, antibiotics, etc.)
   - Statistics and examples are provided for each category

## Key Functions

### normalize_drug_name(name)
Performs comprehensive normalization of drug names, handling various naming conventions and chemical nomenclature.

### get_all_names(row)
Extracts all possible names for a drug from its generic name and synonyms.

### perform_exact_matching(filtered_df, repurposing_df)
Performs exact matching between normalized drug names.

### perform_fuzzy_matching(unmatched_df, repurposing_df, similarity_threshold)
Applies fuzzy matching to find additional matches based on name similarity.

### analyze_remaining_unmatched(fuzzy_matches_df, unmatched_df)
Analyzes patterns in drugs that couldn't be matched to identify common categories.

### drug_matching_pipeline(filtered_drugs_path, repurposing_drugs_path, output_dir, similarity_threshold)
Main function that orchestrates the entire matching process.

## Usage

### Basic Usage

```python

    from drug_matching_pipeline import drug_matching_pipeline
 
 ```

# Run the pipeline with default settings

  ```  drug_matching_pipeline(
    
    'filtered_drugs.csv',
    
    'repurposing_drugs.csv',
    
    './',
    
    similarity_threshold=80
    
    )
```

### Command Line Usage

```bash

    python drug_matching_pipeline.py

```
## Customization

### Adding New Mappings

To add new vitamin mappings or common drug mappings, modify the respective functions:

```python

        def create_vitamin_mappings():
        
        return {
        
        'vitamin c': 'ascorbic acid',
        
        'vitamin b6': 'pyridoxine',
    
    # Add your new mappings here
    
        'vitamin k': 'phylloquinone',
        
        }
```

### Adjusting Similarity Threshold

The similarity threshold for fuzzy matching can be adjusted based on your needs:
- Higher threshold (e.g., 90): More precision, fewer matches
- Lower threshold (e.g., 60): More matches, less precision

## Performance Considerations

- For large datasets (>10,000 drugs), the fuzzy matching step may take significant time
- Consider using a higher similarity threshold for initial runs
- The script is optimized for accuracy rather than speed

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- FuzzyWuzzy library for fuzzy string matching
- Python-Levenshtein for efficient string distance calculations