document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('upload-form');
    const fileInput = document.getElementById('file-input');
    const radioContainer = document.getElementById('radio-options');
    const step3Container = document.getElementById('step3');
    const outcomesFileInput = document.getElementById('outcomes-file-input');
    const mappingResults = document.getElementById('mapping-results');
    const loadingSpinner = document.getElementById('loading-spinner');
    const downloadButton = document.getElementById('download-button');
    
    let mappingTemplate = null;
    let selectedMappingType = null;
    let outcomesFile = null;
    
    // Handle mapping template file selection
    fileInput.addEventListener('change', async function(e) {
        mappingTemplate = e.target.files[0];
        if (mappingTemplate) {
            console.log('Mapping template selected:', mappingTemplate.name);
            loadingSpinner.style.display = 'block';
            radioContainer.innerHTML = ''; // Clear existing options
            mappingResults.innerHTML = ''; // Clear previous results
            step3Container.style.display = 'none';
            downloadButton.style.display = 'none';
            
            // Create FormData and send request
            const formData = new FormData();
            formData.append('file', mappingTemplate);
            
            try {
                console.log('Sending request to get columns...');
                const response = await fetch('/mapping/api/get-columns', {
                    method: 'POST',
                    body: formData
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const data = await response.json();
                console.log('Response:', data);
                
                if (data.success) {
                    // Create radio buttons for mapping types
                    const mappingTypes = ['Institutional Outcomes', 'SEAL of THOMASIAN EDUCATION', 'Program Outcomes'];
                    
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
                        radioContainer.appendChild(div);
                    });
                    
                    radioContainer.style.display = 'block';
                } else {
                    throw new Error(data.error || 'Unknown error occurred');
                }
            } catch (error) {
                console.error('Error:', error);
                showError(error.message);
            } finally {
                loadingSpinner.style.display = 'none';
            }
        }
    });
    
    // Handle radio button selection
    radioContainer.addEventListener('change', async function(e) {
        if (e.target.type === 'radio') {
            selectedMappingType = e.target.value;
            step3Container.style.display = 'block';
            
            // Only process if we have both files
            if (mappingTemplate && outcomesFileInput.files[0]) {
                loadingSpinner.style.display = 'block';
                mappingResults.innerHTML = '';
                
                const formData = new FormData();
                formData.append('mapping_template', mappingTemplate);
                formData.append('outcomes_file', outcomesFileInput.files[0]);
                formData.append('mapping_type', selectedMappingType);
                
                try {
                    console.log('Sending request to process mapping...');
                    const response = await fetch('/mapping/api/process-mapping', {
                        method: 'POST',
                        body: formData
                    });
                    
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    
                    const data = await response.json();
                    console.log('Response:', data);
                    
                    if (data.success) {
                        displayResults(data.results);
                        downloadButton.style.display = 'block';
                    } else {
                        throw new Error(data.error || 'Unknown error occurred');
                    }
                } catch (error) {
                    console.error('Error:', error);
                    showError(error.message);
                } finally {
                    loadingSpinner.style.display = 'none';
                }
            }
        }
    });
    
    // Handle outcomes file selection
    outcomesFileInput.addEventListener('change', async function(e) {
        outcomesFile = e.target.files[0];
        if (outcomesFile && mappingTemplate && selectedMappingType) {
            console.log('Outcomes file selected:', outcomesFile.name);
            loadingSpinner.style.display = 'block';
            mappingResults.innerHTML = '';
            downloadButton.style.display = 'none';
            
            const formData = new FormData();
            formData.append('mapping_template', mappingTemplate);
            formData.append('outcomes_file', outcomesFile);
            formData.append('mapping_type', selectedMappingType);
            
            try {
                console.log('Sending request to process mapping...');
                const response = await fetch('/mapping/api/process-mapping', {
                    method: 'POST',
                    body: formData
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const data = await response.json();
                console.log('Response:', data);
                
                if (data.success) {
                    displayResults(data.results);
                    downloadButton.style.display = 'block';
                } else {
                    throw new Error(data.error || 'Unknown error occurred');
                }
            } catch (error) {
                console.error('Error:', error);
                showError(error.message);
            } finally {
                loadingSpinner.style.display = 'none';
            }
        }
    });
    
    // Handle download button click
    downloadButton.addEventListener('click', function() {
        window.location.href = '/mapping/api/download-results';
    });
    
    function displayResults(results) {
        mappingResults.innerHTML = '';
        
        if (!results || results.length === 0) {
            showError('No results found.');
            return;
        }
        
        const table = document.createElement('table');
        table.border = '1';
        
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
    }
    
    function showError(message) {
        console.error('Error message:', message);
        const errorDiv = document.createElement('div');
        errorDiv.style.color = 'red';
        errorDiv.textContent = message;
        mappingResults.innerHTML = '';
        mappingResults.appendChild(errorDiv);
    }
});