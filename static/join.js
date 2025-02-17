document.getElementById('addFile').addEventListener('click', function() {
    const fileInputs = document.getElementById('fileInputs');
    const newGroup = document.createElement('div');
    newGroup.className = 'file-input-group flex items-center space-x-4';
    
    newGroup.innerHTML = `
        <input type="file" name="files[]" accept=".csv" class="p-2 border rounded" required>
        <button type="button" class="remove-file text-red-500 hover:text-red-700">
            Remove
        </button>
    `;
    
    fileInputs.appendChild(newGroup);
    
    // Show all remove buttons when there's more than one file input
    const removeButtons = document.querySelectorAll('.remove-file');
    removeButtons.forEach(button => button.style.display = 'block');
});

document.getElementById('fileInputs').addEventListener('click', function(e) {
    if (e.target.classList.contains('remove-file')) {
        e.target.parentElement.remove();
        
        // Hide remove button if only one file input remains
        const fileInputs = document.querySelectorAll('.file-input-group');
        if (fileInputs.length === 1) {
            fileInputs[0].querySelector('.remove-file').style.display = 'none';
        }
    }
});

document.getElementById('uploadForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const formData = new FormData(this);
    
    try {
        const response = await fetch('/process-join', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            document.getElementById('preview').classList.remove('hidden');
            
            // Update stats
            document.getElementById('totalRows').textContent = result.total_rows;
            document.getElementById('totalColumns').textContent = result.columns.length;
            
            // Update table headers
            const headerRow = document.getElementById('tableHeaders');
            headerRow.innerHTML = result.columns.map(col => `<th>${col}</th>`).join('');
            
            // Update table body with preview data
            const tableBody = document.getElementById('tableBody');
            const previewData = result.preview.split('\n').slice(1); // Skip header row
            tableBody.innerHTML = previewData.map(row => {
                const cells = row.trim().split(/\s+/);
                return `<tr>${cells.map(cell => `<td>${cell}</td>`).join('')}</tr>`;
            }).join('');
            
            // Setup download buttons
            const downloadCsvBtn = document.getElementById('downloadCsvBtn');
            downloadCsvBtn.onclick = () => window.location.href = `/download/${result.filename}`;
            
            const downloadPdfBtn = document.getElementById('downloadPdfBtn');
            if (result.pdf_filename) {
                downloadPdfBtn.onclick = () => window.location.href = `/download/${result.pdf_filename}`;
                downloadPdfBtn.classList.remove('hidden');
            } else {
                downloadPdfBtn.classList.add('hidden');
            }
        } else {
            alert('Error: ' + result.error);
        }
    } catch (error) {
        alert('Error processing files: ' + error);
    }
});