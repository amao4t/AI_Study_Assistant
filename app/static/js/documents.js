// Enhanced documents.js file for the unified ChatGPT-like interface

document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    const documentPreviewContent = document.getElementById('document-preview-content');
    const documentChatForm = document.getElementById('document-chat-form');
    const documentChatInput = document.getElementById('document-chat-input');
    const chatContainer = document.getElementById('document-chat-container');
    const viewDocumentBtn = document.getElementById('view-document-btn');
    const regenerateSummaryBtn = document.getElementById('regenerate-summary-btn');
    const summarizeBtn = document.getElementById('summarize-btn');
    const uploadForm = document.getElementById('upload-form');
    const documentType = document.getElementById('document-type');
    const documentUploadSection = document.getElementById('document-upload-section');
    const ocrUploadSection = document.getElementById('ocr-upload-section');
    const ocrResult = document.getElementById('ocr-result');
    const ocrText = document.getElementById('ocr-text');
    const useOcrTextBtn = document.getElementById('use-ocr-text');
    const saveOcrTextBtn = document.getElementById('save-ocr-text');
    const uploadBtn = document.getElementById('upload-btn');
    
    // DOM Elements for modal
    const documentPreviewModal = document.getElementById('document-preview-modal');
    const modalPreviewContent = document.querySelector('#document-preview-modal .document-preview-content');
    const modalCloseBtn = document.getElementById('modal-close-btn');
    const modalClose = document.querySelector('#document-preview-modal .modal-close');
    
    // State
    let activeDocumentId = null;
    let activeDocumentName = '';
    let currentUploadType = 'document';
    
    // Toggle upload type
    window.toggleUploadType = function() {
        currentUploadType = documentType.value;
        
        if (currentUploadType === 'document') {
            documentUploadSection.style.display = 'block';
            ocrUploadSection.style.display = 'none';
            uploadBtn.textContent = 'Upload Document';
            ocrResult.style.display = 'none';
        } else {
            documentUploadSection.style.display = 'none';
            ocrUploadSection.style.display = 'block';
            uploadBtn.textContent = 'Process Image';
            ocrResult.style.display = 'none';
        }
    };
    
    // Tab functionality
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // Remove active class from all buttons and contents
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            
            // Add active class to clicked button and corresponding content
            btn.classList.add('active');
            document.getElementById(btn.dataset.tab).classList.add('active');
        });
    });
    
    // Set active document
    window.setActiveDocument = function(id, filename) {
        activeDocumentId = id;
        activeDocumentName = filename;
        
        // Update active document info
        document.getElementById('active-document-info').innerHTML = `
            <span class="badge bg-primary">${filename}</span>
        `;
        
        // Update document items in the list
        document.querySelectorAll('.document-item').forEach(item => {
            if (parseInt(item.dataset.id) === id) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });
        
        // Enable buttons
        documentChatInput.disabled = false;
        viewDocumentBtn.disabled = false;
        regenerateSummaryBtn.disabled = false;
        summarizeBtn.disabled = false;
        document.querySelector('.chat-send-btn').disabled = false;
        
        // Enable clear selection button
        const clearSelectionBtn = document.getElementById('clear-selection-btn');
        if (clearSelectionBtn) {
            clearSelectionBtn.disabled = false;
        }
        
        // Clear chat if it's a different document
        clearChat();
        
        // Add welcome message
        addMessageToChat(`I'm ready to help you with "${filename}". You can ask me questions about the document or request a summary.`, 'bot');
        
        // Load document preview in the background (even though the view is hidden)
        loadDocumentPreview(id);
    };
    
    // Clear chat
    window.clearChat = function() {
        chatContainer.innerHTML = '';
    };
    
    // Add message to chat
    window.addMessageToChat = function(message, type) {
        const bubble = document.createElement('div');
        bubble.className = `chat-bubble ${type}`;
        bubble.innerHTML = message;
        
        chatContainer.appendChild(bubble);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    };
    
    // Add typing indicator
    window.addTypingIndicator = function() {
        const indicator = document.createElement('div');
        indicator.className = 'typing-indicator';
        indicator.innerHTML = '<span></span><span></span><span></span>';
        
        chatContainer.appendChild(indicator);
        chatContainer.scrollTop = chatContainer.scrollHeight;
        
        return indicator;
    };
    
    // Remove typing indicator
    window.removeTypingIndicator = function(indicator) {
        if (indicator && indicator.parentNode) {
            indicator.parentNode.removeChild(indicator);
        }
    };
    
    // Load document preview
    async function loadDocumentPreview(id) {
        if (!id) return;
        
        // Show loading
        documentPreviewContent.innerHTML = '<div class="loading-indicator"><i class="fas fa-spinner fa-spin"></i> Loading document preview...</div>';
        
        try {
            const response = await fetchAPI(`/api/documents/${id}/content`);
            
            if (response.text) {
                let displayText = response.text;
                
                // For PDF files, keep the page markers
                if (activeDocumentName.toLowerCase().endsWith('.pdf')) {
                    // Highlight page markers for better navigation
                    displayText = displayText.replace(/--- Page (\d+) ---/g, 
                        '<div class="page-marker">--- Page $1 ---</div>');
                }
                
                // Show preview with proper styling
                documentPreviewContent.innerHTML = `
                    <div class="document-text-preview">
                        ${displayText}
                    </div>
                `;
            } else {
                documentPreviewContent.innerHTML = '<div class="error-message">Failed to load document content.</div>';
            }
        } catch (error) {
            console.error('Error loading document text:', error);
            documentPreviewContent.innerHTML = '<div class="error-message">Failed to load document content. Please try again.</div>';
        }
    }
    
    // Send message
    async function sendMessage(message) {
        if (!message.trim()) return;
        
        // Add user message to chat
        addMessageToChat(message, 'user');
        
        // Clear input
        documentChatInput.value = '';
        
        // Show typing indicator
        const typingIndicator = addTypingIndicator();
        
        try {
            let response;
            
            // Use different API endpoints based on whether a document is selected
            if (activeDocumentId) {
                // Document-specific chat
                response = await fetchAPI('/api/documents/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        document_id: activeDocumentId,
                        query: message 
                    })
                });
                
                // Add response to chat
                if (response.response) {
                    addMessageToChat(response.response, 'bot');
                } else {
                    addMessageToChat("I'm sorry, I couldn't process your question. Please try again.", 'bot');
                }
            } else {
                // General AI chat (without document)
                response = await fetchAPI('/api/general_chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        query: message 
                    })
                });
                
                // Add response to chat
                if (response.response) {
                    addMessageToChat(response.response, 'bot');
                } else {
                    addMessageToChat("I'm sorry, I couldn't process your question. Please try again.", 'bot');
                }
            }
            
            // Remove typing indicator
            removeTypingIndicator(typingIndicator);
            
        } catch (error) {
            console.error('Error chatting with AI:', error);
            removeTypingIndicator(typingIndicator);
            addMessageToChat("I'm sorry, an error occurred while processing your question.", 'bot');
        }
    }
    
    // Summarize document
    async function summarizeDocument() {
        if (!activeDocumentId) {
            showNotification('Please select a document first', 'warning');
            return;
        }
        
        try {
            // Add user message
            addMessageToChat("Summarize this document", 'user');
            
            // Show typing indicator
            const typingIndicator = addTypingIndicator();
            
            // Get summary from API
            const response = await fetchAPI('/api/documents/summarize', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    document_id: activeDocumentId 
                })
            });
            
            // Remove typing indicator
            removeTypingIndicator(typingIndicator);
            
            // Add response to chat
            if (response.summary) {
                addMessageToChat(response.summary, 'bot');
            } else {
                addMessageToChat("Sorry, I couldn't generate a summary for this document.", 'bot');
            }
            
        } catch (error) {
            console.error('Error summarizing document:', error);
            addMessageToChat("I'm sorry, an error occurred while generating the summary.", 'bot');
        }
    }
    
    // Handle upload form submission
    if (uploadForm) {
        uploadForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(uploadForm);
            const fileInput = document.getElementById('unified-file-input');
            const uploadType = document.getElementById('upload-type').value;
            const uploadBtn = document.getElementById('upload-btn');
            
            if (!fileInput.files || fileInput.files.length === 0) {
                showNotification('Please select a file to upload', 'warning');
                return;
            }
            
            // Get the file
            const file = fileInput.files[0];
            
            // Update upload button text and disable
            uploadBtn.disabled = true;
            uploadBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
            
            if (uploadType === 'document') {
                try {
                    // Document upload
                    const response = await fetch('/api/documents/', {
                        method: 'POST',
                        body: formData
                    });
                    
                    if (!response.ok) {
                        throw new Error('Upload failed');
                    }
                    
                    const data = await response.json();
                    
                    // Reset button
                    uploadBtn.disabled = false;
                    uploadBtn.textContent = 'Upload Document';
                    
                    // Reset file input and upload section
                    fileInput.value = '';
                    document.querySelector('.unified-upload-label').textContent = 'Drop any file or image here';
                    document.getElementById('upload-options').style.display = 'none';
                    
                    // Reload documents
                    await window.loadDocuments();
                    
                    // Select the newly uploaded document
                    if (data.document_id) {
                        const newDoc = window.documentFiles?.find(doc => doc.id === data.document_id);
                        if (newDoc) {
                            window.setActiveDocument(data.document_id, newDoc.filename);
                        }
                    }
                    
                    // Show notification
                    showNotification('Document uploaded successfully', 'success');
                    
                    // Switch to library tab
                    const libraryTabBtn = document.querySelector('[data-tab="library-tab"]');
                    if (libraryTabBtn) {
                        libraryTabBtn.click();
                    }
                    
                } catch (error) {
                    console.error('Error uploading document:', error);
                    uploadBtn.disabled = false;
                    uploadBtn.textContent = 'Upload Document';
                    showNotification('Failed to upload document. Please try again.', 'error');
                }
            } else {
                // OCR image processing
                try {
                    const ocrResult = document.getElementById('ocr-result');
                    const ocrText = document.getElementById('ocr-text');
                    
                    // Show OCR result area with loading
                    ocrResult.style.display = 'block';
                    ocrText.innerHTML = '<div class="loading-indicator"><i class="fas fa-spinner fa-spin"></i> Processing image...</div>';
                    
                    // Send OCR request
                    const response = await fetch('/api/documents/ocr', {
                        method: 'POST',
                        body: formData
                    });
                    
                    if (!response.ok) {
                        throw new Error('OCR processing failed');
                    }
                    
                    const data = await response.json();
                    
                    // Reset button
                    uploadBtn.disabled = false;
                    uploadBtn.textContent = 'Process Image';
                    
                    // Display result
                    ocrText.innerHTML = data.text.replace(/\n/g, '<br>');
                    
                    // Reset file input display but keep the file for potential saving
                    document.querySelector('.unified-upload-label').textContent = 'Drop any file or image here';
                    document.getElementById('upload-options').style.display = 'none';
                    
                } catch (error) {
                    console.error('Error processing OCR:', error);
                    uploadBtn.disabled = false;
                    uploadBtn.textContent = 'Process Image';
                    document.getElementById('ocr-text').innerHTML = '<div class="error-message">Failed to process image. Please try again.</div>';
                    document.getElementById('ocr-result').style.display = 'block';
                }
            }
        });
    }
    
    // Use OCR text in chat
    if (useOcrTextBtn) {
        useOcrTextBtn.addEventListener('click', function() {
            if (ocrText.innerText) {
                // Add the text to chat
                addMessageToChat(ocrText.innerText, 'user');
                
                // Switch to chat view if not already there
                const chatViewBtn = document.querySelector('[data-view="chat-view"]');
                if (chatViewBtn) {
                    chatViewBtn.click();
                }
                
                // Clear the OCR result
                ocrResult.style.display = 'none';
            }
        });
    }
    
    // Save OCR text as document
    if (saveOcrTextBtn) {
        saveOcrTextBtn.addEventListener('click', async function() {
            if (!ocrText.innerText) return;
            
            try {
                // Show loading
                saveOcrTextBtn.disabled = true;
                saveOcrTextBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
                
                // Create a new document from OCR text
                const response = await fetch('/api/documents/from_text', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        text: ocrText.innerText,
                        filename: 'OCR_Document_' + new Date().toISOString().slice(0, 10) + '.txt'
                    })
                });
                
                if (!response.ok) {
                    throw new Error('Failed to save OCR text as document');
                }
                
                const data = await response.json();
                
                // Reset button
                saveOcrTextBtn.disabled = false;
                saveOcrTextBtn.textContent = 'Save as Document';
                
                // Hide OCR result
                ocrResult.style.display = 'none';
                
                // Reload documents
                if (window.loadDocuments) {
                    await window.loadDocuments();
                }
                
                // Select the newly created document
                if (data.document_id) {
                    const newDoc = window.documentFiles?.find(doc => doc.id === data.document_id);
                    if (newDoc) {
                        window.setActiveDocument(data.document_id, newDoc.filename);
                    }
                }
                
                // Switch to library tab
                const libraryTabBtn = document.querySelector('[data-tab="library-tab"]');
                if (libraryTabBtn) {
                    libraryTabBtn.click();
                }
                
                // Show notification
                showNotification('OCR text saved as document', 'success');
                
            } catch (error) {
                console.error('Error saving OCR text:', error);
                saveOcrTextBtn.disabled = false;
                saveOcrTextBtn.textContent = 'Save as Document';
                showNotification('Failed to save OCR text as document', 'error');
            }
        });
    }
    
    // Event listeners
    if (documentChatForm) {
        documentChatForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const message = documentChatInput.value.trim();
            if (message) {
                sendMessage(message);
            }
        });
    }
    
    if (viewDocumentBtn) {
        viewDocumentBtn.addEventListener('click', () => {
            if (!activeDocumentId) return;
            
            // Show modal
            documentPreviewModal.classList.add('show');
            
            // Load content in modal
            modalPreviewContent.innerHTML = '<div class="loading-indicator"><i class="fas fa-spinner fa-spin"></i> Loading document...</div>';
            
            // Load document content
            fetchAPI(`/api/documents/${activeDocumentId}/content`)
                .then(response => {
                    if (response.text) {
                        let displayText = response.text;
                        
                        // For PDF files, keep the page markers
                        if (activeDocumentName.toLowerCase().endsWith('.pdf')) {
                            // Highlight page markers for better navigation
                            displayText = displayText.replace(/--- Page (\d+) ---/g, 
                                '<div class="page-marker">--- Page $1 ---</div>');
                        }
                        
                        // Show preview with proper styling
                        modalPreviewContent.innerHTML = `
                            <div class="document-text-preview">
                                ${displayText}
                            </div>
                        `;
                    } else {
                        modalPreviewContent.innerHTML = '<div class="error-message">Failed to load document content.</div>';
                    }
                })
                .catch(error => {
                    console.error('Error loading document text:', error);
                    modalPreviewContent.innerHTML = '<div class="error-message">Failed to load document content. Please try again.</div>';
                });
        });
    }
    
    if (regenerateSummaryBtn) {
        regenerateSummaryBtn.addEventListener('click', summarizeDocument);
    }
    
    if (summarizeBtn) {
        summarizeBtn.addEventListener('click', summarizeDocument);
    }
    
    // Close modal
    if (modalCloseBtn) {
        modalCloseBtn.addEventListener('click', () => {
            documentPreviewModal.classList.remove('show');
        });
    }
    
    if (modalClose) {
        modalClose.addEventListener('click', () => {
            documentPreviewModal.classList.remove('show');
        });
    }
    
    // Close modal on outside click
    document.addEventListener('click', (e) => {
        if (e.target === documentPreviewModal) {
            documentPreviewModal.classList.remove('show');
        }
    });
    
    // Clear document selection
    function clearDocumentSelection() {
        if (!activeDocumentId) return;
        
        // Reset active document
        activeDocumentId = null;
        activeDocumentName = '';
        
        // Update UI
        document.getElementById('active-document-info').innerHTML = `
            <span class="badge bg-primary">No document selected</span>
        `;
        
        // Remove active class from document items
        document.querySelectorAll('.document-item').forEach(item => {
            item.classList.remove('active');
        });
        
        // Disable document-specific buttons
        viewDocumentBtn.disabled = true;
        regenerateSummaryBtn.disabled = true;
        summarizeBtn.disabled = true;
        
        // Clear chat
        clearChat();
        
        // Add default message
        addMessageToChat('You can ask me anything or select a document for document-specific assistance.', 'bot');
        
        // Clear document preview
        documentPreviewContent.innerHTML = `
            <div class="document-placeholder">
                <div class="document-placeholder-icon">
                    <i class="fas fa-file-alt"></i>
                </div>
                <h3>Document Preview</h3>
                <p>Select a document from the library to view its contents.</p>
            </div>
        `;
    }
    
    // Clear all documents
    const clearAllBtn = document.getElementById('clear-all-btn');
    if (clearAllBtn) {
        clearAllBtn.addEventListener('click', async function() {
            if (!window.documentFiles || window.documentFiles.length === 0) {
                showNotification('No documents to clear', 'info');
                return;
            }
            
            // Confirm deletion
            if (!confirm('Are you sure you want to clear all documents? All associated questions will also be deleted. This action cannot be undone.')) {
                return;
            }
            
            try {
                // Show loading
                clearAllBtn.disabled = true;
                clearAllBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Clearing...';
                
                let successCount = 0;
                let errorCount = 0;
                
                // Delete each document
                for (const doc of window.documentFiles) {
                    try {
                        const response = await fetch(`/api/documents/${doc.id}`, {
                            method: 'DELETE',
                            headers: {
                                'Accept': 'application/json'
                            }
                        });
                        
                        if (!response.ok) {
                            const result = await response.json();
                            throw new Error(result.error || 'Failed to delete document');
                        }
                        
                        successCount++;
                    } catch (error) {
                        console.error(`Error deleting document ${doc.id}:`, error);
                        errorCount++;
                    }
                }
                
                // Reset button
                clearAllBtn.disabled = false;
                clearAllBtn.innerHTML = '<i class="fas fa-trash-alt"></i> Clear All Documents';
                
                // Show notification
                showNotification(`Successfully cleared ${successCount} documents${errorCount > 0 ? `, failed to clear ${errorCount}` : ''}`, errorCount > 0 ? 'warning' : 'success');
                
                // Reset active document if it was deleted
                if (activeDocumentId) {
                    clearDocumentSelection();
                }
                
                // Reload documents
                await window.loadDocuments();
                
            } catch (error) {
                console.error('Error clearing documents:', error);
                clearAllBtn.disabled = false;
                clearAllBtn.innerHTML = '<i class="fas fa-trash-alt"></i> Clear All Documents';
                showNotification('Failed to clear documents', 'error');
            }
        });
    }
    
    // Load documents list
    window.loadDocuments = async function() {
        const documentList = document.getElementById('document-list');
        
        if (!documentList) return;
        
        // Show loading
        documentList.innerHTML = '<div class="loading-indicator"><i class="fas fa-spinner fa-spin"></i> Loading documents...</div>';
        
        try {
            const response = await fetchAPI('/api/documents/');
            
            if (response.documents && Array.isArray(response.documents)) {
                // Store documents in window for later use
                window.documentFiles = response.documents;
                
                if (response.documents.length === 0) {
                    documentList.innerHTML = '<div class="empty-state">No documents found. Upload your first document to get started.</div>';
                    return;
                }
                
                // Render document list
                documentList.innerHTML = '';
                
                response.documents.forEach(doc => {
                    const docEl = document.createElement('div');
                    docEl.className = 'document-item';
                    docEl.dataset.id = doc.id;
                    
                    // Set icon based on file type
                    let icon = 'fas fa-file-alt';
                    const fileExt = doc.filename.split('.').pop().toLowerCase();
                    
                    if (fileExt === 'pdf') {
                        icon = 'fas fa-file-pdf';
                    } else if (['doc', 'docx'].includes(fileExt)) {
                        icon = 'fas fa-file-word';
                    } else if (['jpg', 'jpeg', 'png', 'gif'].includes(fileExt)) {
                        icon = 'fas fa-file-image';
                    }
                    
                    docEl.innerHTML = `
                        <div class="document-icon">
                            <i class="${icon}"></i>
                        </div>
                        <div class="document-info">
                            <div class="document-name">${doc.filename}</div>
                            <div class="document-meta">
                                <span class="document-date">${new Date(doc.created_at).toLocaleDateString()}</span>
                            </div>
                        </div>
                        <div class="document-actions">
                            <button class="btn btn-sm delete-document-btn" data-id="${doc.id}" title="Delete document">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    `;
                    
                    docEl.addEventListener('click', (e) => {
                        // Don't trigger selection if delete button was clicked
                        if (e.target.closest('.delete-document-btn')) {
                            return;
                        }
                        window.setActiveDocument(doc.id, doc.filename);
                    });
                    
                    documentList.appendChild(docEl);
                });
                
                // Add delete document event listeners
                document.querySelectorAll('.delete-document-btn').forEach(btn => {
                    btn.addEventListener('click', async (e) => {
                        e.stopPropagation(); // Prevent selection
                        const docId = parseInt(btn.dataset.id);
                        
                        // Confirm deletion
                        if (!confirm('Are you sure you want to delete this document? All associated questions will also be deleted. This action cannot be undone.')) {
                            return;
                        }
                        
                        try {
                            // Delete the document
                            const response = await fetch(`/api/documents/${docId}`, {
                                method: 'DELETE',
                                headers: {
                                    'Accept': 'application/json'
                                }
                            });
                            
                            const result = await response.json();
                            
                            if (!response.ok) {
                                throw new Error(result.error || 'Failed to delete document');
                            }
                            
                            // Show notification
                            showNotification('Document deleted successfully', 'success');
                            
                            // Reset active document if it was deleted
                            if (activeDocumentId === docId) {
                                clearDocumentSelection();
                            }
                            
                            // Reload documents
                            await window.loadDocuments();
                            
                        } catch (error) {
                            console.error('Error deleting document:', error);
                            showNotification(`Failed to delete document: ${error.message}`, 'error');
                        }
                    });
                });
                
            } else {
                documentList.innerHTML = '<div class="error-message">Error loading documents</div>';
            }
            
        } catch (error) {
            console.error('Error loading documents:', error);
            documentList.innerHTML = '<div class="error-message">Failed to load documents. Please try again.</div>';
        }
    };
    
    // Helper function: Show notification
    function showNotification(message, type = 'info') {
        // Create notification container if it doesn't exist
        let notificationContainer = document.querySelector('.notification-container');
        if (!notificationContainer) {
            notificationContainer = document.createElement('div');
            notificationContainer.className = 'notification-container';
            document.body.appendChild(notificationContainer);
        }
        
        // Create notification
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <i class="${getNotificationIcon(type)}"></i>
            <span>${message}</span>
            <button class="notification-close"><i class="fas fa-times"></i></button>
        `;
        
        // Add to container
        notificationContainer.appendChild(notification);
        
        // Add close event
        notification.querySelector('.notification-close').addEventListener('click', function() {
            notification.remove();
        });
        
        // Auto remove after 5s
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }
    
    // Helper function: Get notification icon
    function getNotificationIcon(type) {
        switch (type) {
            case 'success': return 'fas fa-check-circle';
            case 'warning': return 'fas fa-exclamation-triangle';
            case 'error': return 'fas fa-times-circle';
            default: return 'fas fa-info-circle';
        }
    }
    
    // Helper function: API fetch with error handling
    async function fetchAPI(url, options = {}) {
        try {
            const response = await fetch(url, {
                ...options,
                headers: {
                    ...options.headers,
                    'Accept': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error(`API error: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }
    
    // Initialize
    window.loadDocuments();

    // Add initial welcome message to the chat
    if (chatContainer) {
        clearChat();
        addMessageToChat('Hello! I\'m your AI assistant. Ask me anything or select a document for document-specific help.', 'bot');
    }
});