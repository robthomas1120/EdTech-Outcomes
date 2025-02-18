let currentFile = null;

document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('uploadForm');
    const calculationOptions = document.getElementById('calculationOptions');
    const calculateBtn = document.getElementById('calculateBtn');
    const previewSection = document.getElementById('previewSection');
    const appendBtn = document.getElementById('appendBtn');
    const statusMessage = document.getElementById('statusMessage');

    uploadForm.addEventListener('submit', handleFileUpload);
    calculateBtn.addEventListener('click', handleCalculation);
    appendBtn.addEventListener('click', handleAppend);
});

function showStatus(message, isError = false) {
    const statusMessage = document.getElementById('statusMessage');
    statusMessage.textContent = message;
    statusMessage.className = `alert ${isError ? 'alert-danger' : 'alert-success'}`;
    statusMessage.classList.remove('hidden');
}

async function handleFileUpload(event) {
    event.preventDefault();
    
    const fileInput = document.getElementById('csvFile');
    const file = fileInput.files[0];
    
    if (!file) {
        showStatus('Please select a file', true);
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch('/get-calculation-options', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentFile = data.filename;
            document.getElementById('calculationOptions').classList.remove('hidden');
            showStatus('File uploaded successfully');
        } else {
            showStatus(data.error, true);
        }
    } catch (error) {
        showStatus('Error uploading file: ' + error.message, true);
    }
}

async function handleCalculation() {
    if (!currentFile) {
        showStatus('Please upload a file first', true);
        return;
    }
    
    const selectedCalculations = Array.from(document.querySelectorAll('.calc-option:checked'))
        .map(checkbox => checkbox.value);
    
    if (selectedCalculations.length === 0) {
        showStatus('Please select at least one calculation', true);
        return;
    }
    
    try {
        const response = await fetch('/calculate-preview', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                filename: currentFile,
                calculations: selectedCalculations
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayPreview(data.preview);
            document.getElementById('previewSection').classList.remove('hidden');
        } else {
            showStatus(data.error, true);
        }
    } catch (error) {
        showStatus('Error calculating preview: ' + error.message, true);
    }
}

function displayPreview(preview) {
    const previewContent = document.getElementById('previewContent');
    previewContent.innerHTML = '';
    
    const table = document.createElement('table');
    table.className = 'table table-bordered';
    
    // Create table header
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    const columns = Object.keys(preview);
    
    // Add header cells
    columns.forEach(column => {
        const th = document.createElement('th');
        th.textContent = column;
        headerRow.appendChild(th);
    });
    thead.appendChild(headerRow);
    table.appendChild(thead);
    
    // Create table body
    const tbody = document.createElement('tbody');
    
    // Find the maximum number of rows needed
    const maxRows = Math.max(...Object.values(preview).map(arr => 
        Array.isArray(arr) ? arr.length : 1
    ));
    
    // Create rows
    for (let i = 0; i < maxRows; i++) {
        const row = document.createElement('tr');
        
        columns.forEach(column => {
            const cell = document.createElement('td');
            const values = preview[column];
            
            if (Array.isArray(values)) {
                cell.textContent = i < values.length ? values[i] : '';
            } else {
                cell.textContent = i === 0 ? values : '';
            }
            
            row.appendChild(cell);
        });
        
        tbody.appendChild(row);
    }
    
    table.appendChild(tbody);
    previewContent.appendChild(table);
}

async function handleAppend() {
    if (!currentFile) {
        showStatus('Please upload a file first', true);
        return;
    }
    
    const selectedCalculations = Array.from(document.querySelectorAll('.calc-option:checked'))
        .map(checkbox => checkbox.value);
    
    try {
        const response = await fetch('/append-calculations', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                filename: currentFile,
                calculations: selectedCalculations
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showStatus('Calculations appended successfully! New file: ' + data.filename);
            // Trigger download of new file
            window.location.href = `/download/${data.filename}`;
        } else {
            showStatus(data.error, true);
        }
    } catch (error) {
        showStatus('Error appending calculations: ' + error.message, true);
    }
}