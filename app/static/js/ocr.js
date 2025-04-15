/**
 * OCR and Image Processing functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const imageForm = document.getElementById('image-form');
    const pdfOcrForm = document.getElementById('pdf-ocr-form');
    const documentSelect = document.getElementById('document-select');
    const resultsContainer = document.getElementById('results-container');
    const analysisCard = document.getElementById('analysis-card');
    const analysisContainer = document.getElementById('analysis-container');
    const copyTextBtn = document.getElementById('copy-text-btn');
    
    // Event Listeners
    if (imageForm) {
        imageForm.addEventListener('submit', handleImageUpload);
    }
    
    if (pdfOcrForm) {
        pdfOcrForm.addEventListener('submit', handlePdfOcr);
    }
    
    if (copyTextBtn) {
        copyTextBtn.addEventListener('click', copyExtractedText);
    }
    
    // Load documents
    loadDocuments();
    
    // Functions
    async function loadDocuments() {
        try {
            const response = await fetch('/api/documents/');
            const data = await response.json();
            const documents = data.documents || [];
            
            if (!documentSelect) return;
            
            if (documents.length === 0) {
                documentSelect.innerHTML = '<option value="">No documents available</option>';
                return;
            }
            
            let options = '<option value="">Select a document</option>';
            documents.forEach(doc => {
                options += `<option value="${doc.id}">${doc.filename}</option>`;
            });
            
            documentSelect.innerHTML = options;
        } catch (error) {
            console.error('Error loading documents:', error);
            showNotification('Failed to load documents', 'danger');
        }
    }
    
    async function handleImageUpload(e) {
        e.preventDefault();
        
        const formData = new FormData(imageForm);
        const analyzeImage = document.getElementById('analyze-image').checked;
        const saveAsDocument = document.getElementById('save-as-document').checked;
        
        formData.append('analyze', analyzeImage ? 'true' : 'false');
        formData.append('save', saveAsDocument ? 'true' : 'false');
        
        try {
            // Update UI to loading state
            resultsContainer.innerHTML = `
                <div class="text-center py-4">
                    <div class="spinner-border text-primary" role="status"></div>
                    <p class="mt-2">Processing image...</p>
                </div>
            `;
            
            copyTextBtn.disabled = true;
            
            // Show analysis card if needed
            if (analyzeImage) {
                analysisCard.style.display = 'block';
                analysisContainer.innerHTML = `
                    <div class="d-flex align-items-center">
                        <div class="spinner-border text-primary" role="status"></div>
                        <span class="ms-2">Analyzing image...</span>
                    </div>
                `;
            } else {
                analysisCard.style.display = 'none';
            }
            
            // Submit the form
            const response = await fetch('/api/documents/process-image', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error('Failed to process image');
            }
            
            const data = await response.json();
            
            // Display text results
            if (data.text) {
                resultsContainer.innerHTML = `
                    <div class="card">
                        <div class="card-header">Extracted Text</div>
                        <div class="card-body">
                            <pre id="extracted-text" class="bg-light p-3 rounded" style="white-space: pre-wrap;">${data.text}</pre>
                        </div>
                    </div>
                `;
                copyTextBtn.disabled = false;
                
                // Show notification
                showNotification('Text extracted successfully', 'success');
                
                // If saved as document, show link
                if (data.document_id) {
                    resultsContainer.innerHTML += `
                        <div class="alert alert-success mt-3">
                            <i class="fas fa-check-circle"></i> 
                            Saved as document. 
                            <a href="/document/${data.document_id}" class="alert-link">View document</a>
                        </div>
                    `;
                }
            } else {
                resultsContainer.innerHTML = `
                    <div class="alert alert-warning">
                        <i class="fas fa-exclamation-triangle"></i> 
                        No text was found in this image
                    </div>
                `;
            }
            
            // Display analysis results if requested
            if (analyzeImage && data.analysis) {
                analysisContainer.innerHTML = `
                    <div class="card">
                        <div class="card-body">
                            <p>${data.analysis.replace(/\n/g, '<br>')}</p>
                        </div>
                    </div>
                `;
            } else if (analyzeImage) {
                analysisContainer.innerHTML = `
                    <div class="alert alert-warning">
                        <i class="fas fa-exclamation-triangle"></i> 
                        Could not analyze image
                    </div>
                `;
            }
            
        } catch (error) {
            console.error('Error processing image:', error);
            resultsContainer.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-times-circle"></i> 
                    Error processing image: ${error.message || 'Unknown error'}
                </div>
            `;
            showNotification('Failed to process image', 'danger');
        }
    }
    
    async function handlePdfOcr(e) {
        e.preventDefault();
        
        const documentId = documentSelect.value;
        if (!documentId) {
            showNotification('Please select a document', 'warning');
            return;
        }
        
        try {
            // Update UI to loading state
            resultsContainer.innerHTML = `
                <div class="text-center py-4">
                    <div class="spinner-border text-primary" role="status"></div>
                    <p class="mt-2">Processing PDF with OCR...</p>
                    <p class="text-muted small">This may take some time for large documents</p>
                </div>
            `;
            
            copyTextBtn.disabled = true;
            analysisCard.style.display = 'none';
            
            // Submit request
            const response = await fetch(`/api/documents/${documentId}/process-with-ocr`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error('Failed to process PDF with OCR');
            }
            
            const data = await response.json();
            
            // Show success message
            resultsContainer.innerHTML = `
                <div class="alert alert-success">
                    <i class="fas fa-check-circle"></i> 
                    Document processed successfully with OCR.
                    <a href="/document/${documentId}" class="alert-link">View document</a>
                </div>
            `;
            
            showNotification('PDF processed successfully with OCR', 'success');
            
        } catch (error) {
            console.error('Error processing PDF with OCR:', error);
            resultsContainer.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-times-circle"></i> 
                    Error processing PDF: ${error.message || 'Unknown error'}
                </div>
            `;
            showNotification('Failed to process PDF with OCR', 'danger');
        }
    }
    
    function copyExtractedText() {
        const textElement = document.getElementById('extracted-text');
        if (!textElement) return;
        
        const text = textElement.textContent;
        navigator.clipboard.writeText(text)
            .then(() => {
                showNotification('Text copied to clipboard', 'success');
            })
            .catch(err => {
                console.error('Failed to copy text:', err);
                showNotification('Failed to copy text', 'danger');
            });
    }
    
    function showNotification(message, type = 'info', duration = 5000) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `toast show bg-${type} text-white`;
        notification.style.position = 'fixed';
        notification.style.bottom = '20px';
        notification.style.right = '20px';
        notification.style.minWidth = '250px';
        notification.style.zIndex = '1050';
        
        notification.innerHTML = `
            <div class="toast-header bg-${type} text-white">
                <strong class="me-auto">Notification</strong>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        `;
        
        // Add to document
        document.body.appendChild(notification);
        
        // Auto dismiss
        setTimeout(() => {
            notification.remove();
        }, duration);
        
        // Add dismiss button functionality
        const closeBtn = notification.querySelector('.btn-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                notification.remove();
            });
        }
    }
}); 