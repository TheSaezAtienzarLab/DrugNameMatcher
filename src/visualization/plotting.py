"""
Plotting utilities for visualization.

This module contains JavaScript code for interactive plotting
that will be embedded in the HTML output.
"""

def get_javascript_functions():
    """Get JavaScript functions for the interactive visualization.
    
    Returns:
        str: JavaScript code for interactive visualization
    """
    return """
    // Store the original plot data for reset functionality
    var originalPlotData = JSON.parse(JSON.stringify(plotData));
    
    // Create the 3D scatter plot
    Plotly.newPlot('plot', plotData, layout, {responsive: true});
    
    // Populate the MoA dropdown
    var moaSelect = document.getElementById('moa-select');
    var uniqueMoas = [];  // This will be replaced with actual MOA list in html_generator.py
    
    // Add options to the dropdown
    uniqueMoas.forEach(function(moa) {
        var option = document.createElement('option');
        option.value = moa;
        option.textContent = moa;
        moaSelect.appendChild(option);
    });
    
    // Highlight button click handler
    document.getElementById('highlight-btn').addEventListener('click', function() {
        var selectedMoa = moaSelect.value;
        if (!selectedMoa) {
            alert('Please select a Mechanism of Action first');
            return;
        }
        
        highlightMoa(selectedMoa);
    });
    
    // Reset button click handler
    document.getElementById('reset-btn').addEventListener('click', function() {
        resetVisualization();
    });
    
    // Update proximity threshold value display
    document.getElementById('proximity-slider').addEventListener('input', function() {
        document.getElementById('proximity-value').textContent = this.value;
    });
    
    // Show connections checkbox handler
    document.getElementById('show-connections').addEventListener('change', function() {
        var selectedMoa = moaSelect.value;
        if (selectedMoa) {
            if (this.checked) {
                showConnectionsBetweenRelatedDrugs(selectedMoa);
            } else {
                // Just re-highlight without connections
                highlightMoa(selectedMoa);
            }
        }
    });
    
    // Color by cluster checkbox handler - fixes the bug with colors turning white
    document.getElementById('color-by-cluster').addEventListener('change', function() {
        if (!this.checked) {
            this.checked = true;
            alert("The 'Color by cluster' feature cannot be disabled as it's essential for visualizing cluster relationships.");
        }
    });
    
    // Function to highlight drugs with the selected MoA
    function highlightMoa(moa) {
        // Create a deep copy of the plot data
        var newData = JSON.parse(JSON.stringify(originalPlotData));
        var highlightInfo = document.getElementById('highlight-info');
        var currentMoa = document.getElementById('current-moa');
        
        // Show the highlight info box
        highlightInfo.style.display = 'block';
        currentMoa.textContent = moa;
        
        // For each cluster trace
        for (var i = 0; i < newData.length; i++) {
            if (newData[i].text) {
                var highlightedIndices = [];
                var nonHighlightedIndices = [];
                
                // Identify which points have the selected MoA
                for (var j = 0; j < newData[i].text.length; j++) {
                    var text = newData[i].text[j];
                    if (text.includes('MoA: ' + moa)) {
                        highlightedIndices.push(j);
                    } else {
                        nonHighlightedIndices.push(j);
                    }
                }
                
                // If we have any highlighted points in this cluster
                if (highlightedIndices.length > 0) {
                    // Create two separate traces - one for highlighted points and one for faded points
                    var highlightedTrace = {
                        type: 'scatter3d',
                        mode: 'markers',
                        name: newData[i].name + ' (Highlighted)',
                        marker: {
                            size: newData[i].marker.size,
                            color: newData[i].marker.color,
                            line: newData[i].marker.line,
                            opacity: 1.0
                        },
                        x: highlightedIndices.map(idx => newData[i].x[idx]),
                        y: highlightedIndices.map(idx => newData[i].y[idx]),
                        z: highlightedIndices.map(idx => newData[i].z[idx]),
                        text: highlightedIndices.map(idx => newData[i].text[idx]),
                        hoverinfo: 'text',
                        showlegend: false
                    };
                    
                    var fadedTrace = {
                        type: 'scatter3d',
                        mode: 'markers',
                        name: newData[i].name + ' (Faded)',
                        marker: {
                            size: newData[i].marker.size,
                            color: newData[i].marker.color,
                            line: newData[i].marker.line,
                            opacity: 0.2
                        },
                        x: nonHighlightedIndices.map(idx => newData[i].x[idx]),
                        y: nonHighlightedIndices.map(idx => newData[i].y[idx]),
                        z: nonHighlightedIndices.map(idx => newData[i].z[idx]),
                        text: nonHighlightedIndices.map(idx => newData[i].text[idx]),
                        hoverinfo: 'text',
                        showlegend: false
                    };
                    
                    // Replace the original trace with the two new ones
                    newData[i] = highlightedTrace;
                    if (nonHighlightedIndices.length > 0) {
                        newData.push(fadedTrace);
                    }
                } else {
                    // If no highlighted points in this cluster, just fade the entire cluster
                    newData[i].marker.opacity = 0.2;
                }
            }
        }
        
        // Update the plot
        Plotly.react('plot', newData, layout);
        
        // Show connections between related drugs if checkbox is checked
        if (document.getElementById('show-connections').checked) {
            showConnectionsBetweenRelatedDrugs(moa);
        }
    }
    
    // Function to show connections between drugs with the same MoA
    function showConnectionsBetweenRelatedDrugs(moa) {
        var newData = [];
        var relatedDrugs = [];
        
        // First collect all the currently displayed data (which may already have highlighting)
        var displayedData = document.getElementById('plot').data;
        for (var i = 0; i < displayedData.length; i++) {
            newData.push(displayedData[i]);
        }
        
        // Find all drugs with the selected MoA across all traces
        for (var i = 0; i < originalPlotData.length; i++) {
            if (originalPlotData[i].text) {
                for (var j = 0; j < originalPlotData[i].text.length; j++) {
                    var text = originalPlotData[i].text[j];
                    
                    if (text.includes('MoA: ' + moa)) {
                        relatedDrugs.push({
                            x: originalPlotData[i].x[j],
                            y: originalPlotData[i].y[j],
                            z: originalPlotData[i].z[j],
                            name: text.split('<br>')[0]
                        });
                    }
                }
            }
        }
        
        // Create connections between related drugs
        if (relatedDrugs.length > 1) {
            // Calculate centroid
            var centroid = {x: 0, y: 0, z: 0};
            relatedDrugs.forEach(function(drug) {
                centroid.x += drug.x;
                centroid.y += drug.y;
                centroid.z += drug.z;
            });
            centroid.x /= relatedDrugs.length;
            centroid.y /= relatedDrugs.length;
            centroid.z /= relatedDrugs.length;
            
            // Create lines from each drug to the centroid
            var lines = {
                type: 'scatter3d',
                mode: 'lines',
                name: moa + ' connections',
                line: {
                    color: 'rgba(100, 200, 100, 0.5)',
                    width: 2
                },
                x: [],
                y: [],
                z: []
            };
            
            relatedDrugs.forEach(function(drug) {
                // Add line from drug to centroid
                lines.x.push(drug.x, centroid.x, null);
                lines.y.push(drug.y, centroid.y, null);
                lines.z.push(drug.z, centroid.z, null);
            });
            
            // Add the lines to the plot
            newData.push(lines);
            
            // Add the centroid as a marker
            newData.push({
                type: 'scatter3d',
                mode: 'markers',
                name: moa + ' centroid',
                marker: {
                    size: 12,
                    color: 'rgba(100, 200, 100, 1)',
                    symbol: 'diamond'
                },
                x: [centroid.x],
                y: [centroid.y],
                z: [centroid.z],
                text: [moa + ' centroid'],
                hoverinfo: 'text'
            });
            
            // Update the plot
            Plotly.react('plot', newData, layout);
        }
    }
    
    // Function to reset the visualization to its original state
    function resetVisualization() {
        // Update the plot with the original data
        Plotly.react('plot', originalPlotData, layout);
        
        // Hide the highlight info box
        document.getElementById('highlight-info').style.display = 'none';
        
        // Reset the MoA dropdown
        document.getElementById('moa-select').value = '';
    }
    """

def get_css_styles():
    """Get CSS styles for the visualization.
    
    Returns:
        str: CSS styles for the visualization
    """
    return """
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
            border-radius: 5px;
        }
        h1, h2 {
            color: #333;
        }
        .plot-container {
            height: 600px;
            margin-bottom: 20px;
        }
        .controls {
            background-color: #f0f0f0;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 15px;
        }
        .control-group {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        select {
            padding: 8px;
            border-radius: 4px;
            border: 1px solid #ccc;
            min-width: 200px;
        }
        button {
            padding: 8px 15px;
            border-radius: 4px;
            border: none;
            background-color: #4CAF50;
            color: white;
            cursor: pointer;
            font-weight: bold;
        }
        button:hover {
            background-color: #45a049;
        }
        button.reset {
            background-color: #f44336;
        }
        button.reset:hover {
            background-color: #d32f2f;
        }
        .checkbox-container {
            display: flex;
            align-items: center;
            gap: 5px;
        }
        .slider-container {
            display: flex;
            align-items: center;
            gap: 10px;
            min-width: 250px;
        }
        .slider-container label {
            min-width: 120px;
        }
        input[type="range"] {
            width: 100%;
        }
        .stats-container, .moa-distribution {
            margin: 20px 0;
            padding: 15px;
            background-color: #f9f9f9;
            border-radius: 5px;
            border: 1px solid #ddd;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        th {
            background-color: #f2f2f2;
        }
        .highlight-info {
            margin-top: 10px;
            padding: 10px;
            background-color: #e8f5e9;
            border-radius: 4px;
            border-left: 4px solid #4CAF50;
            display: none;
        }
    """