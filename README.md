# Drug Clustering Analysis Tool

![Drug Clustering Visualization](results/visualization_example.png)

An interactive data visualization tool that clusters drugs based on their pathway activation patterns, helps identify relationships between drugs with similar mechanisms of action (MoA), and visualizes these relationships in an explorable 3D space.

## Overview

This tool performs several key operations:
1. Loads drug pathway data from CSV files
2. Analyzes the data using Principal Component Analysis (PCA)
3. Groups similar drugs using K-means clustering
4. Creates an interactive 3D visualization for exploring the results
5. Integrates mechanism of action (MoA) data to provide context

The visualization allows researchers to identify drugs with similar pathway profiles, discover potential new applications for existing drugs, and understand the relationship between pathway activation patterns and clinical effects.

## Features

- **PCA-Based Dimensionality Reduction**: Condenses complex pathway data into a 3D visualization
- **Automatic Optimal Clustering**: Finds the best number of clusters using the elbow method
- **Interactive 3D Visualization**: Explore the drug landscape with zoom, rotation, and pan controls
- **MoA Integration**: Hover over drugs to see their mechanism of action
- **Cluster Analysis**: See detailed statistics about each cluster
- **Filtering Capabilities**: Highlight drugs by MoA to observe patterns
- **Connection Visualization**: See how drugs with the same MoA relate to each other spatially

## Installation

```bash
# Clone the repository
git clone https://github.com/TheSaezAtienzarLab/clustering-project.git
cd drug-clustering

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Preparing your data

1. Place your drug pathway data CSV files in the `drugs_data/` directory
   - Each file should be named after the drug (e.g., `aspirin.csv`)
   - Files should contain columns for `Term` (pathway name) and `NES` (normalized enrichment score)

2. (Optional) Place your MoA data in `drugs_association/all_matched_drugs.csv` with columns for drug names and their mechanisms of action

### Running the analysis

```bash
# Run the main analysis script
python main.py
```

### Interpreting the visualization

- Each point represents a drug
- Colors represent different clusters
- Hover over points to see drug name, MoA, and cluster assignment
- Use the dropdown to select and highlight drugs by MoA
- Toggle connections to see relationships between drugs with the same MoA
- Use cluster statistics to understand the distribution of drugs

## Files

- `main.py`: Main script that performs analysis and generates visualization
- `requirements.txt`: List of required Python packages
- `results/`: Directory where analysis results and visualization are saved

## Requirements

- Python 3.7+
- pandas
- numpy
- scikit-learn
- plotly
- kneed (for finding optimal cluster number)

If you encounter issues with missing data:
1. Check that your drug pathway files follow the required format
2. Ensure the MoA data file contains the correct column names

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- This tool uses [Plotly](https://plotly.com/) for interactive visualizations
- Clustering algorithms are powered by [scikit-learn](https://scikit-learn.org/)
- MoA analysis was done using [MoAble](https://github.com/dmis-lab/moable)

---

*Note: This tool is for research purposes only and should not be used for clinical decision making.*