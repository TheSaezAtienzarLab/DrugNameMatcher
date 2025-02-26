// Add this to the HTML template to enhance interactivity

document.addEventListener('DOMContentLoaded', function() {
    // Add a search box for MOAs
    const container = document.querySelector('.container');
    const plotContainer = document.getElementById('plot');
    
    // Exit early if required elements aren't found
    if (!container || !plotContainer) {
        console.error('Required DOM elements not found. Check if container and plot elements exist.');
        return;
    }
    
    const searchBox = document.createElement('div');
    searchBox.className = 'search-box';
    searchBox.innerHTML = `
        <input type="text" id="moa-search" placeholder="Search MOAs...">
        <button id="search-button">Search</button>
        <div id="search-status" style="margin-top: 5px; font-size: 0.9em;"></div>
    `;
    
    container.insertBefore(searchBox, plotContainer);
    
    // Style the search box
    const style = document.createElement('style');
    style.textContent = `
        .search-box {
            margin-bottom: 15px;
            text-align: center;
        }
        #moa-search {
            padding: 8px;
            width: 300px;
            border: 1px solid #ddd;
            border-radius: 4px;
            margin-right: 5px;
        }
        #search-button {
            padding: 8px 15px;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        #search-button:hover {
            background-color: #45a049;
        }
        #search-status {
            color: #666;
        }
        #search-status.error {
            color: #f44336;
        }
        #search-status.success {
            color: #4CAF50;
        }
    `;
    document.head.appendChild(style);
    
    // Add search functionality with improved error handling
    document.getElementById('search-button').addEventListener('click', performSearch);
    document.getElementById('moa-search').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            performSearch();
        }
    });
    
    function performSearch() {
        const searchTerm = document.getElementById('moa-search').value.toLowerCase().trim();
        const statusElement = document.getElementById('search-status');
        
        if (!searchTerm) {
            statusElement.textContent = 'Please enter a search term';
            statusElement.className = 'error';
            return;
        }
        
        statusElement.textContent = 'Searching...';
        statusElement.className = '';
        
        // Find the dropdown menu
        const dropdown = document.querySelector('.updatemenu-dropdown-button');
        if (!dropdown) {
            statusElement.textContent = 'Error: Dropdown menu not found. Visualization may not be fully loaded.';
            statusElement.className = 'error';
            return;
        }
        
        dropdown.click(); // Open the dropdown
        
        // Find matching MOA in the dropdown
        setTimeout(() => {
            const menuItems = document.querySelectorAll('.updatemenu-item');
            if (!menuItems || menuItems.length === 0) {
                statusElement.textContent = 'Error: No menu items found';
                statusElement.className = 'error';
                return;
            }
            
            let found = false;
            for (let item of menuItems) {
                if (item.textContent.toLowerCase().includes(searchTerm)) {
                    item.click();
                    found = true;
                    statusElement.textContent = `Found and selected: "${item.textContent.trim()}"`;
                    statusElement.className = 'success';
                    break;
                }
            }
            
            if (!found) {
                statusElement.textContent = `No MOA matching "${searchTerm}" found`;
                statusElement.className = 'error';
                // Close the dropdown if nothing was found
                dropdown.click();
            }
        }, 300); // Increased timeout for better reliability
    }
    
    // Add a message if the plot is empty
    if (!plotContainer.children.length) {
        const errorMessage = document.createElement('div');
        errorMessage.style.padding = '20px';
        errorMessage.style.color = '#f44336';
        errorMessage.style.textAlign = 'center';
        errorMessage.innerHTML = `
            <h3>Visualization not loaded</h3>
            <p>The plot appears to be empty. This could be because:</p>
            <ul style="text-align: left; display: inline-block;">
                <li>The visualization file path may be incorrect (check if it should be in /results/ instead of /output/)</li>
                <li>The visualization hasn't been generated yet</li>
                <li>There was an error during visualization generation</li>
            </ul>
            <p>Please check the console for any JavaScript errors.</p>
        `;
        plotContainer.appendChild(errorMessage);
    }
}); 