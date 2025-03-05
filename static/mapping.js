document.addEventListener('DOMContentLoaded', function() {
    // Debug helper
    function debug(message) {
        console.log(`[DEBUG] ${message}`);
    }

    debug("DOM fully loaded, initializing script");
    
    // Get all DOM elements
    const uploadForm = document.getElementById('upload-form');
    const fileInput = document.getElementById('file-input');
    const radioContainer = document.getElementById('radio-options');
    const step3Container = document.getElementById('step3');
    const outcomesFileInput = document.getElementById('outcomes-file-input');
    const mappingResults = document.getElementById('mapping-results');
    const loadingSpinner = document.getElementById('loading-spinner');
    const downloadButton = document.getElementById('download-button');
    
    // Check if all elements are found
    debug(`Elements found: fileInput=${!!fileInput}, radioContainer=${!!radioContainer}, step3Container=${!!step3Container}`);
    
    let mappingTemplate = null;
    let selectedMappingType = null;
    let outcomesFile = null;
    
    // Handle mapping template file selection
    fileInput.addEventListener('change', async function(e) {
        debug("File input change event triggered");
        mappingTemplate = e.target.files[0];
        
        if (mappingTemplate) {
            debug(`Mapping template selected: ${mappingTemplate.name}`);
            
            // Show loading spinner
            loadingSpinner.classList.remove('hidden');
            
            // Clear previous content
            radioContainer.innerHTML = ''; 
            mappingResults.innerHTML = ''; 
            
            // Create section title
            const sectionTitle = document.createElement('h3');
            sectionTitle.className = 'section-title';
            sectionTitle.innerHTML = '<i class="fas fa-list-alt me-2"></i>Step 2: Select Mapping Type';
            
            // Create options container
            const optionsContainer = document.createElement('div');
            optionsContainer.className = 'radio-options-container';
            
            // Add elements to the DOM
            radioContainer.appendChild(sectionTitle);
            radioContainer.appendChild(optionsContainer);
            
            // Hide step 3 and download button
            step3Container.classList.add('hidden');
            downloadButton.style.display = 'none';
            
            // Create FormData for the API request
            const formData = new FormData();
            formData.append('file', mappingTemplate);
            
            try {
                debug('Sending request to get columns...');
                const response = await fetch('/mapping/api/get-columns', {
                    method: 'POST',
                    body: formData
                });
                
                debug(`Response status: ${response.status}`);
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const data = await response.json();
                debug(`Response data: ${JSON.stringify(data)}`);
                
                if (data.success) {
                    // Create radio buttons for mapping types
                    const mappingTypes = ['Institutional Outcomes', 'SEAL of THOMASIAN EDUCATION', 'Program Outcomes'];
                    
                    debug(`Creating ${mappingTypes.length} radio options`);
                    
                    mappingTypes.forEach(type => {
                        const div = document.createElement('div');
                        div.className = 'radio-option';
                        
                        const input = document.createElement('input');
                        input.type = 'radio';
                        input.name = 'mapping-option';
                        input.value = type;
                        input.id = type.replace(/\s+/g, '-').toLowerCase();
                        
                        const label = document.createElement('label');
                        label.htmlFor = input.id;
                        label.textContent = type;
                        
                        div.appendChild(input);
                        div.appendChild(label);
                        optionsContainer.appendChild(div);
                    });
                    
                    // Show the radio container by removing the hidden class
                    debug('Showing radio options container');
                    radioContainer.classList.remove('hidden');
                } else {
                    throw new Error(data.error || 'Unknown error occurred');
                }
            } catch (error) {
                debug(`Error: ${error.message}`);
                showError(error.message);
            } finally {
                // Hide loading spinner
                loadingSpinner.classList.add('hidden');
            }
        }
    });
    
    // Handle radio button selection
    radioContainer.addEventListener('change', function(e) {
        if (e.target.type === 'radio') {
            selectedMappingType = e.target.value;
            debug(`Selected mapping type: ${selectedMappingType}`);
            
            // Show step 3
            debug('Showing step 3 container');
            step3Container.classList.remove('hidden');
            
            // Only process if we have both files
            if (mappingTemplate && outcomesFileInput.files[0]) {
                debug('Both files are available, processing mapping');
                processMapping(mappingTemplate, outcomesFileInput.files[0], selectedMappingType);
            }
        }
    });
    
    // Handle outcomes file selection
    outcomesFileInput.addEventListener('change', function(e) {
        debug('Outcomes file input change event triggered');
        outcomesFile = e.target.files[0];
        
        if (outcomesFile && mappingTemplate && selectedMappingType) {
            debug(`Outcomes file selected: ${outcomesFile.name}`);
            processMapping(mappingTemplate, outcomesFile, selectedMappingType);
        }
    });
    
    async function processMapping(mappingTemplate, outcomesFile, mappingType) {
        debug('Processing mapping with files and type');
        
        // Show loading spinner
        loadingSpinner.classList.remove('hidden');
        
        // Clear results and hide download button
        mappingResults.innerHTML = '';
        mappingResults.style.display = 'none';
        downloadButton.style.display = 'none';
        
        const formData = new FormData();
        formData.append('mapping_template', mappingTemplate);
        formData.append('outcomes_file', outcomesFile);
        formData.append('mapping_type', mappingType);
        
        try {
            debug('Sending request to process mapping...');
            const response = await fetch('/mapping/api/process-mapping', {
                method: 'POST',
                body: formData
            });
            
            debug(`Response status: ${response.status}`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            debug(`Response data received, success: ${data.success}`);
            
            if (data.success) {
                displayResults(data.results);
                downloadButton.style.display = 'block';
            } else {
                throw new Error(data.error || 'Unknown error occurred');
            }
        } catch (error) {
            debug(`Error: ${error.message}`);
            showError(error.message);
        } finally {
            // Hide loading spinner
            loadingSpinner.classList.add('hidden');
        }
    }
    
    // Handle download button click
    downloadButton.addEventListener('click', function() {
        debug('Download button clicked');
        window.location.href = '/mapping/api/download-results';
    });
    
    function displayResults(results) {
        debug('Displaying results');
        mappingResults.innerHTML = '';
        
        if (!results || results.length === 0) {
            debug('No results found');
            showError('No results found.');
            return;
        }
        
        const table = document.createElement('table');
        table.className = 'table table-bordered table-hover';
        
        // Create header
        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');
        Object.keys(results[0]).forEach(column => {
            const th = document.createElement('th');
            th.textContent = column;
            headerRow.appendChild(th);
        });
        thead.appendChild(headerRow);
        table.appendChild(thead);
        
        // Create body
        const tbody = document.createElement('tbody');
        results.forEach(row => {
            const tr = document.createElement('tr');
            Object.values(row).forEach(value => {
                const td = document.createElement('td');
                td.textContent = value || '';
                tr.appendChild(td);
            });
            tbody.appendChild(tr);
        });
        
        table.appendChild(tbody);
        mappingResults.appendChild(table);
        
        // Show results container
        debug('Making results visible');
        mappingResults.style.display = 'block';
    }
    
    function showError(message) {
        debug(`Showing error: ${message}`);
        const errorDiv = document.createElement('div');
        errorDiv.className = 'alert alert-danger';
        errorDiv.innerHTML = `<i class="fas fa-exclamation-circle me-2"></i>${message}`;
        mappingResults.innerHTML = '';
        mappingResults.appendChild(errorDiv);
        mappingResults.style.display = 'block';
    }
});