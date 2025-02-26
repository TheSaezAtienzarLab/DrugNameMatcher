"""
Utility script to open the correct visualization HTML file in a web browser.
"""

import os
import webbrowser
import sys

def main():
    # Path to the results directory
    project_root = os.path.dirname(os.path.abspath(__file__))
    visualization_path = os.path.join(project_root, 'results', 'visualization.html')
    
    # Check if the file exists
    if not os.path.exists(visualization_path):
        print(f"Error: Visualization file not found at {visualization_path}")
        return
    
    # Print the path
    print(f"Opening visualization from: {visualization_path}")
    
    # Convert to file URL
    file_url = f"file://{os.path.abspath(visualization_path)}"
    
    # Open in web browser
    try:
        webbrowser.open(file_url)
        print("Visualization opened in your default web browser.")
    except Exception as e:
        print(f"Error opening browser: {str(e)}")
        print(f"Please manually open this file: {visualization_path}")

if __name__ == "__main__":
    main()