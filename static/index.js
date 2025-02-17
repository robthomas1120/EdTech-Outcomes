document.addEventListener('DOMContentLoaded', function() {
    // Define currentFile in the outer scope so it's accessible to all event handlers
    let currentFile = null;
    let currentPreview = null;
    let allRows = [];
    const rowsPerPage = 10;
    let currentPage = 1;

    // Get DOM elements
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const fileName = document.getElementById('fileName');
    const fileInfo = document.getElementById('fileInfo');
    const downloadBtn = document.getElementById('downloadBtn');
    const previewArea = document.getElementById('previewArea');
    const headerRow = document.getElementById('headerRow');
    const dataRows = document.getElementById('dataRows');
    const uniqueValuesList = document.getElementById('uniqueValuesList');
    const uniqueValuesSection = document.getElementById('uniqueValuesSection');
    const formatInput = document.getElementById('formatInput');
    const validateBtn = document.getElementById('validateBtn');
    const fixFormatBtn = document.getElementById('fixFormatBtn');
    const formatErrors = document.getElementById('formatErrors');
    const errorsList = document.getElementById('errorsList');

    function displayPreview(preview) {
        if (!preview || !preview.display_columns || !preview.preview_rows) {
            console.error('Invalid preview data:', preview);
            return;
        }

        currentPreview = preview;  
        allRows = preview.preview_rows;
        
        headerRow.innerHTML = '<th class="row-number">#</th>';
        dataRows.innerHTML = '';

        preview.display_columns.forEach(header => {
            const th = document.createElement('th');
            th.textContent = header;
            headerRow.appendChild(th);
        });

        // Display all rows at once
        allRows.forEach((row, index) => {
            const tr = document.createElement('tr');
            
            // Check if this row has format errors
            const hasFormatError = preview.format_errors && 
                preview.format_errors.some(error => error.includes(`Row ${index + 1}:`));
            
            // Add error class to the entire row if it has errors
            if (hasFormatError) {
                tr.classList.add('format-error-row');
            }
            
            const tdRowNum = document.createElement('td');
            tdRowNum.className = 'row-number';
            tdRowNum.textContent = index + 1;
            tr.appendChild(tdRowNum);

            Object.values(row).forEach((cell) => {
                const td = document.createElement('td');
                td.textContent = cell || '';
                tr.appendChild(td);
            });

            dataRows.appendChild(tr);
        });

        previewArea.classList.remove('hidden');

        if (preview.unique_values) {
            uniqueValuesList.innerHTML = '';
            
            // Create container for two columns
            const container = document.createElement('div');
            container.className = 'unique-values-container';

            // Process Program Outcomes
            const poColumn = document.createElement('div');
            poColumn.className = 'unique-values-column';
            const poTitle = document.createElement('h5');
            poTitle.textContent = 'Program Outcomes';
            poColumn.appendChild(poTitle);

            const poList = document.createElement('div');
            poList.className = 'unique-values-list';

            // Sort and filter Program Outcomes
            if (preview.unique_values['Program Outcomes']) {
                const outcomes = preview.unique_values['Program Outcomes']
                    .filter(value => value) // Remove empty values
                    .flatMap(value => value.split(/,\s*/)) // Split by comma and trim
                    .map(value => value.trim())
                    .filter((value, index, self) => self.indexOf(value) === index) // Remove duplicates
                    .sort((a, b) => {
                        // Extract numbers and compare
                        const numA = parseInt(a.match(/\d+/)?.[0] || '0');
                        const numB = parseInt(b.match(/\d+/)?.[0] || '0');
                        return numA - numB;
                    });

                outcomes.forEach(value => {
                    const item = document.createElement('div');
                    item.className = 'p-2';
                    item.textContent = value || '(empty)';
                    poList.appendChild(item);
                });
            }
            poColumn.appendChild(poList);

            // Process Course Outcomes
            const coColumn = document.createElement('div');
            coColumn.className = 'unique-values-column';
            const coTitle = document.createElement('h5');
            coTitle.textContent = 'Course Outcomes';
            coColumn.appendChild(coTitle);

            const coList = document.createElement('div');
            coList.className = 'unique-values-list';

            if (preview.unique_values['Course Outcomes']) {
                preview.unique_values['Course Outcomes']
                    .filter(value => value) // Remove empty values
                    .forEach(value => {
                        const item = document.createElement('div');
                        item.className = 'p-2';
                        item.textContent = value || '(empty)';
                        coList.appendChild(item);
                    });
            }
            coColumn.appendChild(coList);

            // Add columns to container
            container.appendChild(poColumn);
            container.appendChild(coColumn);
            uniqueValuesList.appendChild(container);
            uniqueValuesSection.classList.remove('hidden');
        }
    }

    // Enable/disable format-related buttons based on input and file presence
    formatInput.addEventListener('input', () => {
        const hasValue = formatInput.value.trim() && currentFile;
        validateBtn.disabled = !hasValue;
        fixFormatBtn.disabled = !hasValue;
    });

    // Handle file selection
    function handleFile(file) {
        currentFile = file;
        fileName.textContent = file.name;
        fileInfo.classList.remove('hidden');
        
        // Update button states based on format input
        const hasFormatValue = formatInput.value.trim();
        validateBtn.disabled = !hasFormatValue;
        fixFormatBtn.disabled = !hasFormatValue;

        const formData = new FormData();
        formData.append('file', file);

        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayPreview(data.preview);
            } else {
                alert(data.error || 'Error uploading file');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error uploading file');
        });
    }

    validateBtn.addEventListener('click', () => {
        if (!currentFile) {
            alert('Please upload a file first');
            return;
        }

        const formData = new FormData();
        formData.append('file', currentFile);
        formData.append('format_pattern', formatInput.value.trim());

        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayPreview(data.preview);
                
                if (data.preview.format_errors && data.preview.format_errors.length > 0) {
                    errorsList.innerHTML = '';
                    data.preview.format_errors.forEach(error => {
                        const li = document.createElement('li');
                        li.textContent = error;
                        errorsList.appendChild(li);
                    });
                    formatErrors.classList.remove('hidden');
                } else {
                    formatErrors.classList.add('hidden');
                }
            } else {
                alert(data.error || 'Error validating format');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error validating format');
        });
    });

    // Fix format button handler
    fixFormatBtn.addEventListener('click', () => {
        if (!currentFile) {
            alert('Please upload a file first');
            return;
        }

        const formData = new FormData();
        formData.append('file', currentFile);
        formData.append('format_pattern', formatInput.value.trim());

        // Show loading state
        fixFormatBtn.disabled = true;
        fixFormatBtn.textContent = 'Fixing...';

        fetch('/fix-format', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update the preview with fixed data
                displayPreview(data.preview);
                
                // Update download button to point to fixed file
                downloadBtn.onclick = () => window.location.href = `/download/${data.filename}`;
                
                // Show success message
                alert('Format has been fixed! You can now download the corrected file.');
            } else {
                alert(data.error || 'Error fixing format');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error fixing format');
        })
        .finally(() => {
            // Reset button state
            fixFormatBtn.disabled = false;
            fixFormatBtn.textContent = 'Fix Format';
        });
    });

    // File drag and drop handlers
    dropZone.addEventListener('click', () => fileInput.click());
    
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = '#666';
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.style.borderColor = '#ccc';
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = '#ccc';
        const files = e.dataTransfer.files;
        if (files.length) handleFile(files[0]);
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length) handleFile(e.target.files[0]);
    });
});