import json
import os

# Path to the HTML file
html_path = 'results/visualization.html'

# Read the HTML file
with open(html_path, 'r') as f:
    html_content = f.read()

# Read the MOA list
moa_list_path = 'results/moa_list.txt'
with open(moa_list_path, 'r') as f:
    moa_list = [line.strip() for line in f.readlines()]

# Create the JavaScript array string
moa_array_str = json.dumps(moa_list)

# Replace the empty array with our MOA list
if 'var uniqueMoas = [];' in html_content:
    html_content = html_content.replace('var uniqueMoas = [];', f'var uniqueMoas = {moa_array_str};')
    print("Replaced empty MOA array with actual list of MOAs")
else:
    print("Could not find 'var uniqueMoas = [];' in the HTML file")

# Write the updated HTML file
with open(html_path, 'w') as f:
    f.write(html_content)

print(f"Updated HTML file saved to {html_path}")
print(f"Included {len(moa_list)} MOAs in the dropdown")