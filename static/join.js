// DOM Elements
const fileInputs = document.getElementById('fileInputs');
const addFileButton = document.getElementById('addFile');
const preview = document.getElementById('preview');
const totalRows = document.getElementById('totalRows');
const totalColumns = document.getElementById('totalColumns');
const downloadCsvBtn = document.getElementById('downloadCsvBtn');

// Initialize drag and drop for the first upload area
initializeDragAndDrop('dropZone1', 'fileInput1');

// Function to initialize drag and drop functionality
function initializeDragAndDrop(dropZoneId, fileInputId) {
    const dropZone = document.getElementById(dropZoneId);
    const fileInput = document.getElementById(fileInputId);
    
    // Open file dialog when clicking on the drop zone
    dropZone.addEventListener('click', () => {
        fileInput.click();
    });
    
    // Display file name when a file is selected
    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            const fileName = fileInput.files[0].name;
            dropZone.querySelector('p').textContent = `Selected: ${fileName}`;
            dropZone.style.borderColor = 'var(--success-color)';
        }
    });
    
    // Handle drag and drop events
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = 'var(--primary-color)';
        dropZone.style.backgroundColor = 'rgba(67, 97, 238, 0.05)';
    });
    
    dropZone.addEventListener('dragleave', () => {
        dropZone.style.borderColor = 'var(--medium-gray)';
        dropZone.style.backgroundColor = 'var(--secondary-color)';
    });
    
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = 'var(--success-color)';
        dropZone.style.backgroundColor = 'var(--secondary-color)';
        
        if (e.dataTransfer.files.length > 0) {
            fileInput.files = e.dataTransfer.files;
            const fileName = fileInput.files[0].name;
            dropZone.querySelector('p').textContent = `Selected: ${fileName}`;
            
            // Trigger change event
            const event = new Event('change');
            fileInput.dispatchEvent(event);
        }
    });
}

// Add new file input with drag and drop functionality
let fileCounter = 2;
addFileButton.addEventListener('click', () => {
    const fileInputGroup = document.createElement('div');
    fileInputGroup.classList.add('file-input-group');
    
    const dropZoneId = `dropZone${fileCounter}`;
    const fileInputId = `fileInput${fileCounter}`;
    
    fileInputGroup.innerHTML = `
        <div class="upload-area" id="${dropZoneId}">
            <div class="upload-icon">
                <i class="fas fa-cloud-upload-alt"></i>
            </div>
            <p>Drag and drop CSV file here or click to select</p>
            <p class="small text-muted">File ${fileCounter}</p>
            <input type="file" id="${fileInputId}" name="files[]" accept=".csv" class="hidden" required>
        </div>
        <button type="button" class="remove-file">
            <i class="fas fa-trash-alt"></i> Remove
        </button>
    `;
    fileInputs.appendChild(fileInputGroup);

    // Initialize drag and drop for the new upload area
    initializeDragAndDrop(dropZoneId, fileInputId);
    
    const removeButton = fileInputGroup.querySelector('.remove-file');
    removeButton.classList.remove('hidden');
    removeButton.addEventListener('click', () => {
        fileInputGroup.remove();
    });
    
    fileCounter++;
});

// Function to display table data
function displayPreviewTable(result) {
    const tableHeaders = document.getElementById('tableHeaders');
    const tableBody = document.getElementById('tableBody');
    
    // Clear existing content
    tableHeaders.innerHTML = '';
    tableBody.innerHTML = '';
    
    // Add headers
    if (result.columns && result.columns.length > 0) {
        result.columns.forEach(column => {
            const th = document.createElement('th');
            th.textContent = column;
            tableHeaders.appendChild(th);
        });
    }
    
    // Add rows
    if (result.preview && Array.isArray(result.preview)) {
        result.preview.forEach(row => {
            const tr = document.createElement('tr');
            
            // Add a cell for each column
            result.columns.forEach(column => {
                const td = document.createElement('td');
                td.textContent = row[column] !== null && row[column] !== undefined ? row[column] : '';
                tr.appendChild(td);
            });
            
            tableBody.appendChild(tr);
        });
    }
}

// Handle form submission
const form = document.getElementById('uploadForm');
form.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    // Show loading state
    const submitButton = form.querySelector('button[type="submit"]');
    const originalText = submitButton.innerHTML;
    submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
    submitButton.disabled = true;

    try {
        // Create FormData from the form
        const formData = new FormData(form);
        
        // Check if any files are selected
        let hasFiles = false;
        for (const [key, value] of formData.entries()) {
            if (key === 'files[]' && value.name) {
                hasFiles = true;
                break;
            }
        }
        
        if (!hasFiles) {
            alert('Please select at least one file.');
            submitButton.innerHTML = originalText;
            submitButton.disabled = false;
            return;
        }
        
        // Send the form data to the server
        const response = await fetch(form.action, {
            method: 'POST',
            body: formData
        });
        
        // Parse the JSON response
        const result = await response.json();
        
        // Reset button
        submitButton.innerHTML = originalText;
        submitButton.disabled = false;

        // Handle success
        if (result.success) {
            // Show preview section
            preview.classList.remove('hidden');
            
            // Update stats
            totalRows.textContent = result.total_rows;
            totalColumns.textContent = result.columns.length;
            
            // Display table
            displayPreviewTable(result);
            
            // Setup download button
            downloadCsvBtn.href = `/download/${result.filename}`;
            downloadCsvBtn.classList.remove('hidden');
            
            // Scroll to preview
            preview.scrollIntoView({ behavior: 'smooth' });
            
            // Show success message with file details
            const fileCount = result.processed_files ? result.processed_files.length : 0;
            const message = `Successfully joined ${fileCount} files. Total rows: ${result.total_rows}`;
            alert(message);
        } else {
            // Show error message
            alert(`Error: ${result.error || 'Unknown error occurred'}`);
        }
    } catch (error) {
        // Reset button
        submitButton.innerHTML = originalText;
        submitButton.disabled = false;
        
        // Show error
        console.error('Error:', error);
        alert(`Error: ${error.message}`);
    }
});