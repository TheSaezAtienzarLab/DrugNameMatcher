import pandas as pd

# Load the MOA distribution file
moa_dist = pd.read_csv('results/moa_cluster_distribution.csv')

# Print the first few rows
print(moa_dist.head())

# Check if there are specific columns we need
print("Columns:", moa_dist.columns.tolist())

# Write the MOAs to a simple text file for easier debugging
with open('results/moa_list.txt', 'w') as f:
    for moa in moa_dist['MOA'].tolist():
        f.write(f"{moa}\n")

print(f"Wrote {len(moa_dist)} MOAs to results/moa_list.txt")