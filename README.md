# Drug Clustering Analysis

A machine learning pipeline for clustering drugs based on their pathway data and analyzing relationships between drug mechanisms of action (MOA).

## Overview

This project implements a complete workflow for clustering drugs based on their biological pathway data. It uses Principal Component Analysis (PCA) for dimensionality reduction and K-means clustering to identify groups of drugs with similar pathway profiles. The results are visualized in an interactive 3D plot, with special emphasis on analyzing how drugs with the same mechanism of action (MOA) distribute across different clusters.

## Features

- **Data Loading**: Import drug pathway data from CSV files
- **Preprocessing**: Standardize data and perform PCA for dimensionality reduction
- **Clustering**: Automatic determination of optimal cluster number using the elbow method
- **Performance Metrics**: Calculate and report silhouette, Calinski-Harabasz, and Davies-Bouldin scores
- **Interactive Visualization**: 3D visualization of clusters with:
  - Color-coding by cluster
  - Highlighting drugs by MOA
  - Filtering to focus on specific mechanisms
  - Visualization of connections between related drugs
  - Adjustable proximity threshold
- **MOA Analysis**: Distribution analysis of drugs with the same mechanism across different clusters

## Prerequisites

- Python 3.7+
- Required packages:
  - numpy
  - pandas
  - scikit-learn
  - plotly
  - kneed (for elbow method)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/drug-clustering-analysis.git
   cd drug-clustering-analysis
   ```

2. Install required packages:
   ```
   pip install -r requirements.txt
   ```

## Project Structure

```
drug-clustering-analysis/
├── main.py                     # Main script to run the complete workflow
├── src/
│   ├── data_loader.py          # Functions for loading drug pathway and MOA data
│   ├── preprocessing.py        # Data preprocessing and PCA
│   ├── clustering.py           # K-means clustering and metrics calculation
│   ├── utils.py                # Utility functions for analysis and export
│   └── visualization/          # Visualization modules
│       ├── __init__.py         # Package initialization
│       ├── main.py             # Main visualization entry point
│       ├── data_processing.py  # Process data for visualization
│       ├── html_generator.py   # Generate HTML for interactive visualization
│       ├── plotting.py         # JavaScript functions for interactive plots
│       ├── templates.py        # HTML templates
│       └── moa_replacement.py  # MOA data injection utilities
├── drugs_moable/               # Directory for drug pathway CSV files
├── final_output/               # Directory for MOA data
│   └── all_matched_drugs.csv   # Mechanism of action information
└── results/                    # Generated results (created during execution)
    ├── clustering_results.csv  # Complete clustering results
    ├── cluster_details.csv     # Metrics and details about each cluster
    ├── moa_cluster_distribution.csv # MOA distribution across clusters
    └── visualization.html      # Interactive visualization
```

## Usage

1. Prepare your data:
   - Place drug pathway CSV files in the `drugs_moable` directory
   - Each CSV should have columns for `Term` (pathway name) and `NES` (normalized enrichment score)
   - Place MOA data in `final_output/all_matched_drugs.csv` with `GENERIC_NAME` as drug identifier

2. Run the analysis:
   ```
   python main.py
   ```

3. View the results:
   - Results are saved in the `results` directory
   - Open `results/visualization.html` in a web browser to explore the interactive visualization

## Workflow Details

1. **Data Loading**:
   - Drug pathway data is loaded from CSV files in the `drugs_moable` directory
   - Each file represents one drug with its pathway enrichment scores
   - MOA data is loaded from `final_output/all_matched_drugs.csv`

2. **Preprocessing**:
   - Data is standardized (zero mean, unit variance)
   - PCA reduces dimensionality to 3 components for visualization

3. **Clustering**:
   - Optimal number of clusters is determined using the elbow method
   - K-means clustering is performed on the PCA results
   - Clustering metrics are calculated to evaluate quality

4. **Analysis**:
   - Cluster characteristics are analyzed
   - MOA distribution across clusters is calculated

5. **Visualization**:
   - Interactive 3D visualization is generated with Plotly
   - HTML file includes controls for exploration and filtering
   - Drugs with the same MOA can be highlighted

## Interactive Visualization Features

The generated visualization provides several interactive features:

- **3D Plot**: Explore the clusters in three dimensions
- **MOA Highlighting**: Select a specific MOA to highlight drugs with that mechanism
- **Connection Visualization**: Show connections between drugs with the same MOA
- **Proximity Threshold**: Adjust the threshold for showing connections
- **Hover Information**: View drug names, MOA, and cluster information on hover
- **Cluster Statistics**: View information about cluster sizes and distribution
- **MOA Distribution Table**: Analyze how drugs with the same MOA are distributed across clusters

## Extending the Framework

### Adding New Data Sources

To add new data sources:

1. Place new drug pathway files in the `drugs_moable` directory
2. Update the MOA information in `final_output/all_matched_drugs.csv`
3. Run the pipeline again

### Customizing the Visualization

To customize the visualization:

1. Modify the `get_css_styles()` function in `src/visualization/plotting.py`
2. Adjust the JavaScript functions in `get_javascript_functions()`
3. Update the HTML template in `src/visualization/html_generator.py`

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- https://github.com/dmis-lab/moable

## Contact

Saez Atienzar Lab - Ohio State
