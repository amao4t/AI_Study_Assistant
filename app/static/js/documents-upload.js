/**
 * Document upload handling functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    // Handle the file drag and drop interface
    const unifiedFileInput = document.getElementById('unified-file-input');
    const uploadSection = document.querySelector('.unified-upload-section');
    const browseFilesBtn = document.getElementById('browse-files-btn');
    const uploadOptions = document.getElementById('upload-options');
    const uploadTypeSelect = document.getElementById('upload-type');
    const uploadBtn = document.getElementById('upload-btn');
    
    // Browse files button
    browseFilesBtn.addEventListener('click', function() {
        unifiedFileInput.click();
    });
    
    // Handle file selection
    unifiedFileInput.addEventListener('change', function() {
        if (this.files && this.files.length > 0) {
            const file = this.files[0];
            handleFileSelected(file);
        }
    });
    
    // Drag and drop functionality
    uploadSection.addEventListener('dragover', function(e) {
        e.preventDefault();
        uploadSection.classList.add('drag-over');
    });
    
    uploadSection.addEventListener('dragleave', function() {
        uploadSection.classList.remove('drag-over');
    });
    
    uploadSection.addEventListener('drop', function(e) {
        e.preventDefault();
        uploadSection.classList.remove('drag-over');
        
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            const file = e.dataTransfer.files[0];
            unifiedFileInput.files = e.dataTransfer.files;
            handleFileSelected(file);
        }
    });
    
    // Handle file selected (either by browse or drag-drop)
    function handleFileSelected(file) {
        // Show selected file name
        uploadSection.querySelector('.unified-upload-label').textContent = file.name;
        
        // Detect file type
        const fileExtension = file.name.split('.').pop().toLowerCase();
        const isImage = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'].includes(fileExtension);
        
        // Update upload type
        uploadTypeSelect.value = isImage ? 'image' : 'document';
        
        // Show upload options
        uploadOptions.style.display = 'block';
        
        // Update button text
        uploadBtn.textContent = isImage ? 'Process Image' : 'Upload Document';
    }
}); 