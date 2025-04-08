// Enhanced documents.js file with improved document handling capabilities

document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const uploadForm = document.getElementById('upload-form');
    const documentList = document.getElementById('document-list');
    const chatContainer = document.getElementById('document-chat-container');
    const questionForm = document.getElementById('document-chat-form');
    const questionInput = document.getElementById('document-chat-input');
    const chatDocumentInfo = document.getElementById('chat-document-info');
    const activeSummaryDocument = document.getElementById('active-document-info');
    const summaryContainer = document.getElementById('summary-container');
    const summaryLoading = document.getElementById('summary-loading');
    const summaryContent = document.getElementById('summary-content');
    const regenerateSummaryBtn = document.getElementById('regenerate-summary-btn');
    const copySummaryBtn = document.getElementById('copy-summary-btn');
    const chatWithDocumentBtn = document.getElementById('chat-with-document-btn');
    const documentPreviewModal = document.getElementById('document-preview-modal');
    const documentPreviewContent = document.getElementById('document-preview-content');
    const modalCloseBtn = document.getElementById('modal-close-btn');
    const modalXBtn = document.querySelector('.modal-close');
    const useDocumentBtn = document.getElementById('use-document-btn');
    const chatPanel = document.getElementById('document-chat-panel');
    const clearChatBtn = document.getElementById('clear-chat-btn');
    const copyLastMessageBtn = document.getElementById('copy-last-message-btn');
    const uploadStatusContainer = document.createElement('div');
    
    // State
    let documentFiles = []; // Renamed from 'documents' to avoid conflict with DOM 'document'
    let activeDocumentId = null;
    let selectedDocumentId = null;
    let chatHistory = [];
    let processingDocument = false;
    
    // Initialize
    if (uploadForm) {
        uploadForm.parentNode.appendChild(uploadStatusContainer);
        uploadStatusContainer.className = 'upload-status mt-3';
    }
    
    loadDocuments();
    
    // Event Listeners
    if (uploadForm) {
        uploadForm.addEventListener('submit', handleDocumentUpload);
        
        // Add file size validation on file selection
        const fileInput = document.getElementById('document');
        if (fileInput) {
            fileInput.addEventListener('change', function() {
                validateFileSize(this);
            });
        }
    }
    
    if (questionForm) {
        questionForm.addEventListener('submit', handleQuestionSubmit);
    }
    
    if (modalCloseBtn) {
        modalCloseBtn.addEventListener('click', closeModal);
    }
    
    if (modalXBtn) {
        modalXBtn.addEventListener('click', closeModal);
    }
    
    if (useDocumentBtn) {
        useDocumentBtn.addEventListener('click', selectActiveDocument);
    }
    
    if (regenerateSummaryBtn) {
        regenerateSummaryBtn.addEventListener('click', regenerateSummary);
    }
    
    if (copySummaryBtn) {
        copySummaryBtn.addEventListener('click', copySummary);
    }
    
    if (chatWithDocumentBtn) {
        chatWithDocumentBtn.addEventListener('click', function() {
            if (activeDocumentId) {
                openDocumentChat(activeDocumentId);
            } else {
                showNotification('Please select a document first', 'warning');
            }
        });
    }
    
    if (clearChatBtn) {
        clearChatBtn.addEventListener('click', clearChat);
    }
    
    if (copyLastMessageBtn) {
        copyLastMessageBtn.addEventListener('click', copyLastMessage);
    }
    
    // Validate file size before upload
    function validateFileSize(fileInput) {
        if (!fileInput.files || fileInput.files.length === 0) return;
        
        const file = fileInput.files[0];
        const maxSize = 10 * 1024 * 1024; // 10MB max (increased from 5MB)
        
        if (file.size > maxSize) {
            showNotification('File is too large. Maximum size is 10MB', 'warning');
            fileInput.value = ''; // Clear the file input
        }
    }
    
    // Load user's documents
    async function loadDocuments() {
        try {
            showLoadingIndicator(documentList);
            const response = await fetchAPI('/api/documents/');
            documentFiles = response.documents || []; // Using documentFiles instead of documents
            renderDocumentList();
        } catch (error) {
            console.error('Error loading documents:', error);
            documentList.innerHTML = '<div class="error-message">Failed to load documents. Please try again.</div>';
        }
    }
    
    // Render document list
    function renderDocumentList() {
        if (documentFiles.length === 0) {
            documentList.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-file-alt"></i>
                    <p>No documents found. Upload a document to get started.</p>
                </div>
            `;
            return;
        }
        
        let html = '';
        documentFiles.forEach(doc => {
            const isActive = doc.id === activeDocumentId;
            const fileIcon = getFileIcon(doc.file_type);
            const fileSize = formatFileSize(doc.file_size);
            const date = new Date(doc.created_at).toLocaleDateString();
            
            html += `
                <div class="document-item ${isActive ? 'active' : ''}" data-id="${doc.id}">
                    <div class="document-icon">
                        <i class="${fileIcon}"></i>
                    </div>
                    <div class="document-info">
                        <div class="document-name">${doc.filename}</div>
                        <div class="document-meta">${fileSize} • ${date}</div>
                    </div>
                    <div class="document-actions">
                        <button class="document-action preview-document" data-id="${doc.id}" title="Preview">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="document-action summarize-document" data-id="${doc.id}" title="Summarize">
                            <i class="fas fa-compress-alt"></i>
                        </button>
                        <button class="document-action chat-document" data-id="${doc.id}" title="Chat with Document">
                            <i class="fas fa-comments"></i>
                        </button>
                        <button class="document-action delete-document" data-id="${doc.id}" title="Delete">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            `;
        });
        
        documentList.innerHTML = html;
        
        // Add event listeners to document items
        document.querySelectorAll('.document-item').forEach(item => {
            item.addEventListener('click', (e) => {
                if (!e.target.closest('.document-actions')) {
                    setActiveDocument(parseInt(item.dataset.id));
                }
            });
        });
        
        // Add event listeners to document actions
        document.querySelectorAll('.preview-document').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                previewDocument(parseInt(btn.dataset.id));
            });
        });
        
        document.querySelectorAll('.summarize-document').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                summarizeDocument(parseInt(btn.dataset.id));
            });
        });
        
        document.querySelectorAll('.chat-document').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                openDocumentChat(parseInt(btn.dataset.id));
            });
        });
        
        document.querySelectorAll('.delete-document').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                deleteDocument(parseInt(btn.dataset.id));
            });
        });
    }
    
    // Set active document
    function setActiveDocument(id) {
        activeDocumentId = id;
        
        // Update UI
        document.querySelectorAll('.document-item').forEach(item => {
            item.classList.toggle('active', parseInt(item.dataset.id) === id);
        });
        
        const activeDoc = documentFiles.find(doc => doc.id === id);
        if (activeDoc && activeSummaryDocument) {
            activeSummaryDocument.innerHTML = `<span class="badge bg-primary">${activeDoc.filename}</span>`;
            
            // Enable summary actions
            if (regenerateSummaryBtn) regenerateSummaryBtn.disabled = false;
            if (copySummaryBtn) copySummaryBtn.disabled = false;
            if (chatWithDocumentBtn) chatWithDocumentBtn.disabled = false;
            
            // Load document summary
            loadDocumentSummary(id);
        }
    }
    
    // Handle document upload
    async function handleDocumentUpload(e) {
        e.preventDefault();
        
        if (processingDocument) {
            showNotification('A document is already being processed. Please wait.', 'warning');
            return;
        }
        
        const formData = new FormData(uploadForm);
        const fileInput = document.getElementById('document');
        
        if (!fileInput.files || fileInput.files.length === 0) {
            showNotification('Please select a file to upload', 'warning');
            return;
        }
        
        const file = fileInput.files[0];
        
        try {
            // Show loading state
            processingDocument = true;
            const submitBtn = uploadForm.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Uploading...';
            submitBtn.disabled = true;
            
            // Show progress for large files
            uploadStatusContainer.innerHTML = `
                <div class="progress">
                    <div class="progress-bar progress-bar-striped progress-bar-animated bg-primary" 
                         role="progressbar" style="width: 0%" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100">
                        Processing document...
                    </div>
                </div>
            `;
            
            // Simulate progress for large files
            let progress = 0;
            const progressInterval = setInterval(() => {
                progress += 5;
                if (progress > 90) progress = 90; // Cap at 90% until complete
                
                const progressBar = uploadStatusContainer.querySelector('.progress-bar');
                if (progressBar) {
                    progressBar.style.width = `${progress}%`;
                    progressBar.setAttribute('aria-valuenow', progress);
                    
                    if (progress < 30) {
                        progressBar.innerText = 'Uploading file...';
                    } else if (progress < 60) {
                        progressBar.innerText = 'Processing content...';
                    } else {
                        progressBar.innerText = 'Extracting text...';
                    }
                }
            }, 500);
            
            const response = await fetch('/api/documents/', {
                method: 'POST',
                body: formData,
                credentials: 'same-origin'
            });
            
            clearInterval(progressInterval);
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Failed to upload document');
            }
            
            // Complete progress
            const progressBar = uploadStatusContainer.querySelector('.progress-bar');
            if (progressBar) {
                progressBar.style.width = '100%';
                progressBar.setAttribute('aria-valuenow', 100);
                progressBar.innerText = 'Complete!';
                progressBar.classList.remove('progress-bar-animated');
            }
            
            // Reset form
            uploadForm.reset();
            
            // Clear progress after a delay
            setTimeout(() => {
                uploadStatusContainer.innerHTML = '';
            }, 3000);
            
            // Add new document to list
            documentFiles.unshift(data.document);
            renderDocumentList();
            
            // Set as active document
            setActiveDocument(data.document.id);
            
            showNotification('Document uploaded successfully', 'success');
        } catch (error) {
            console.error('Error uploading document:', error);
            showNotification(error.message, 'danger');
            
            // Show error in progress
            const progressBar = uploadStatusContainer.querySelector('.progress-bar');
            if (progressBar) {
                progressBar.style.width = '100%';
                progressBar.classList.remove('bg-primary', 'progress-bar-animated');
                progressBar.classList.add('bg-danger');
                progressBar.innerText = 'Upload failed';
            }
            
            // Clear progress after a delay
            setTimeout(() => {
                uploadStatusContainer.innerHTML = '';
            }, 5000);
        } finally {
            // Reset button
            const submitBtn = uploadForm.querySelector('button[type="submit"]');
            submitBtn.innerHTML = 'Upload Document';
            submitBtn.disabled = false;
            processingDocument = false;
        }
    }
    
    // Load document summary
    async function loadDocumentSummary(documentId) {
        if (!summaryContainer || !summaryLoading || !summaryContent) return;
        
        // Properly update the summary container UI
        summaryContainer.innerHTML = ''; // Clear welcome message
        summaryLoading.style.display = 'flex';
        summaryContent.style.display = 'none';
        
        try {
            const response = await fetchAPI(`/api/documents/${documentId}/summarize`);
            
            // Hide loading, show content
            summaryLoading.style.display = 'none';
            summaryContent.style.display = 'block';
            
            // Format and display summary
            const formattedSummary = formatMessageContent(response.summary);
            summaryContent.innerHTML = formattedSummary;
            
        } catch (error) {
            console.error('Error loading summary:', error);
            summaryLoading.style.display = 'none';
            summaryContent.style.display = 'block';
            summaryContent.innerHTML = `<div class="error-message">Failed to load summary: ${error.message}</div>`;
        }
    }
    
    // Summarize document directly
    function summarizeDocument(id) {
        setActiveDocument(id);
    }
    
    // Regenerate summary
    async function regenerateSummary() {
        if (!activeDocumentId) return;
        loadDocumentSummary(activeDocumentId);
    }
    
    // Copy summary to clipboard
    function copySummary() {
        if (!summaryContent) return;
        
        const summaryText = summaryContent.innerText;
        navigator.clipboard.writeText(summaryText)
            .then(() => {
                showNotification('Summary copied to clipboard', 'success');
            })
            .catch(err => {
                console.error('Error copying text: ', err);
                showNotification('Failed to copy summary', 'danger');
            });
    }
    
    // Open document chat
    function openDocumentChat(documentId) {
        // Reset chat history
        chatHistory = [];
        
        // Get document info from our documents array
        const doc = documentFiles.find(d => d.id === documentId);
        if (!doc) {
            console.error("Document not found:", documentId);
            return;
        }
        
        // Set active document ID
        activeDocumentId = documentId;
        
        // Update active class on document items
        document.querySelectorAll('.document-item').forEach(item => {
            item.classList.toggle('active', parseInt(item.dataset.id) === documentId);
        });
        
        // Update chat panel header if it exists
        if (chatDocumentInfo) {
            chatDocumentInfo.innerHTML = `<span class="badge bg-primary">${doc.filename}</span>`;
        }
        
        // Clear and initialize chat container
        if (chatContainer) {
            chatContainer.innerHTML = `
                <div class="chat-welcome">
                    <div class="chat-welcome-icon">
                        <i class="fas fa-comments"></i>
                    </div>
                    <h3>Document Chat Assistant</h3>
                    <p>Ask questions about "${doc.filename}" to get AI-powered answers.</p>
                    <div class="chat-instructions mt-3">
                        <p><strong>Tips for better results:</strong></p>
                        <ul>
                            <li>Ask specific questions about the content</li>
                            <li>Refer to sections or concepts from the document</li>
                            <li>For long documents, try to be specific about which part you're asking about</li>
                        </ul>
                    </div>
                </div>
            `;
        }
        
        // Show chat panel
        if (chatPanel) {
            chatPanel.style.display = 'flex';
            
            // Focus input
            if (questionInput) {
                questionInput.disabled = false;
                questionInput.focus();
            }
            
            // Scroll to chat panel
            chatPanel.scrollIntoView({ behavior: 'smooth' });
        }
        
        showNotification('Document chat activated. Ask questions about the document content.', 'info');
    }
    
    // Handle question submission - Updated with improved formatting
    async function handleQuestionSubmit(e) {
        e.preventDefault();
        
        if (!questionInput || !chatContainer) return;
        
        const question = questionInput.value.trim();
        if (!question) return;
        
        if (!activeDocumentId) {
            showNotification('Please select a document first', 'warning');
            return;
        }
        
        // Add user message to chat
        addMessageToChat(question, 'user');
        
        // Clear input
        questionInput.value = '';
        
        // Add loading indicator
        const typingIndicator = document.createElement('div');
        typingIndicator.className = 'chat-bubble bot typing-indicator';
        typingIndicator.innerHTML = '<div class="typing-dots"><span></span><span></span><span></span></div>';
        chatContainer.appendChild(typingIndicator);
        
        // Scroll to bottom
        chatContainer.scrollTop = chatContainer.scrollHeight;
        
        try {
            // Send request to API
            const response = await fetchAPI(`/api/document-chat/${activeDocumentId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    question: question,
                    chat_history: chatHistory
                })
            });
            
            // Remove typing indicator
            const indicator = document.querySelector('.typing-indicator');
            if (indicator) indicator.remove();
            
            // Add response to chat
            if (response && response.response) {
                const messageEl = addMessageToChat(response.response, 'bot');
                
                // Mark if it's a fallback response
                if (response.is_fallback) {
                    messageEl.classList.add('fallback-response');
                    showFallbackWarning();
                }
                
                // Update chat history
                chatHistory = response.chat_history || [];
            } else {
                throw new Error('Invalid response from server');
            }
        } catch (error) {
            console.error('Error in document chat:', error);
            // Remove typing indicator
            const indicator = document.querySelector('.typing-indicator');
            if (indicator) indicator.remove();
            
            // Add error message
            addMessageToChat('Sorry, I encountered an error while processing your question. Please try again.', 'bot');
        }
    }
    
    // Add message to chat with better formatting
    function addMessageToChat(message, sender) {
        if (!chatContainer) return;
        
        // Remove welcome message if it exists
        const welcomeMessage = chatContainer.querySelector('.chat-welcome');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }
        
        // Create message element
        const messageEl = document.createElement('div');
        messageEl.className = `chat-bubble ${sender}`;
        
        // Format message with markdown-like processing
        message = formatMessageContent(message);
        
        // Use innerHTML with processed content
        messageEl.innerHTML = message;
        
        // Add message to chat
        chatContainer.appendChild(messageEl);
        
        // Scroll to bottom
        chatContainer.scrollTop = chatContainer.scrollHeight;
        
        // Make sure input doesn't get disabled after adding message
        if (questionInput) {
            questionInput.disabled = false;
        }
        
        return messageEl;
    }
    
    // Format message content with improved markdown-like processing
    function formatMessageContent(message) {
        // Replace URLs with clickable links
        message = message.replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank">$1</a>');
        
        // Format headings
        message = message.replace(/^### (.*?)$/gm, '<h5>$1</h5>');
        message = message.replace(/^## (.*?)$/gm, '<h4>$1</h4>');
        message = message.replace(/^# (.*?)$/gm, '<h3>$1</h3>');
        
        // Process ordered lists
        message = message.replace(/^\d+\.\s(.+)$/gm, '<li>$1</li>').replace(/(<li>.*<\/li>)/gs, '<ol>$1</ol>');
        
        // Process unordered lists
        message = message.replace(/^[*-]\s(.+)$/gm, '<li>$1</li>').replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>');
        
        // Process blockquotes
        message = message.replace(/^>\s(.+)$/gm, '<blockquote>$1</blockquote>');
        
        // Process code blocks
        message = message.replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre><code class="language-$1">$2</code></pre>');
        
        // Process inline code
        message = message.replace(/`([^`]+)`/g, '<code>$1</code>');
        
        // Process bold formatting
        message = message.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
        
        // Process italic formatting
        message = message.replace(/\*([^*]+)\*/g, '<em>$1</em>');
        
        // Ensure line breaks are preserved
        message = message.replace(/\n/g, '<br>');
        
        return message;
    }
    
    // Show fallback warning
    function showFallbackWarning() {
        const warningElement = document.createElement('div');
        warningElement.className = 'fallback-warning';
        warningElement.innerHTML = `
            <i class="fas fa-exclamation-triangle"></i>
            <span>AI service temporarily limited. You're receiving a fallback response.</span>
        `;
        
        // Add to chat container or as a notification
        const notificationsContainer = document.querySelector('.notifications-container') || 
            document.createElement('div');
        
        if (!document.querySelector('.notifications-container')) {
            notificationsContainer.className = 'notifications-container';
            document.body.appendChild(notificationsContainer);
        }
        
        notificationsContainer.appendChild(warningElement);
        
        // Auto dismiss after 10 seconds
        setTimeout(() => {
            warningElement.classList.add('fade-out');
            setTimeout(() => warningElement.remove(), 500);
        }, 10000);
    }
    
    // Copy last message
    function copyLastMessage() {
        const botMessages = chatContainer.querySelectorAll('.chat-bubble.bot');
        if (botMessages.length > 0) {
            const lastBotMessage = botMessages[botMessages.length - 1];
            
            // Copy message content (plain text)
            const messageText = lastBotMessage.innerText || lastBotMessage.textContent;
            
            navigator.clipboard.writeText(messageText)
                .then(() => {
                    showNotification('Message copied to clipboard', 'success');
                })
                .catch(err => {
                    console.error('Error copying text: ', err);
                    showNotification('Failed to copy message', 'danger');
                });
        } else {
            showNotification('No messages to copy', 'warning');
        }
    }
    
    // Clear chat
    function clearChat() {
        if (!chatContainer) return;
        
        // Reset chat history
        chatHistory = [];
        
        // Get active document
        const doc = documentFiles.find(d => d.id === activeDocumentId);
        
        // Clear chat container and show welcome message
        chatContainer.innerHTML = `
            <div class="chat-welcome">
                <div class="chat-welcome-icon">
                    <i class="fas fa-comments"></i>
                </div>
                <h3>Document Chat Assistant</h3>
                <p>Ask questions about "${doc ? doc.filename : 'your document'}" to get AI-powered answers.</p>
                <div class="chat-instructions mt-3">
                    <p><strong>Tips for better results:</strong></p>
                    <ul>
                        <li>Ask specific questions about the content</li>
                        <li>Refer to sections or concepts from the document</li>
                        <li>For long documents, try to be specific about which part you're asking about</li>
                    </ul>
                </div>
            </div>
        `;
        
        showNotification('Chat history cleared', 'info');
    }
    
    // Preview document with progress indicator for large files
    async function previewDocument(id) {
        if (!documentPreviewModal || !documentPreviewContent) return;
        
        selectedDocumentId = id;
        const doc = documentFiles.find(d => d.id === id);
        
        if (!doc) return;
        
        // Show modal
        documentPreviewModal.classList.add('show');
        documentPreviewContent.innerHTML = '<div class="loading-indicator"><i class="fas fa-spinner fa-spin"></i> Loading document text...</div>';
        
        try {
            // For larger documents, show a progress message
            const fileSize = doc.file_size;
            if (fileSize > 1024 * 1024) { // If > 1MB
                documentPreviewContent.innerHTML = `
                    <div class="loading-indicator">
                        <i class="fas fa-spinner fa-spin"></i> Loading large document (${formatFileSize(fileSize)})...
                        <div class="loading-progress mt-2">This may take several seconds for large documents.</div>
                    </div>
                `;
            }
            
            // Get document text
            const response = await fetchAPI(`/api/documents/${id}/text`);
            
            if (response.text) {
                // Process text for display
                let displayText = response.text;
                
                // For PDF files, keep the page markers
                if (doc.file_type === 'pdf') {
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
                
                // Add page navigation for long documents
                if (doc.file_type === 'pdf' && response.text.includes('--- Page')) {
                    addPageNavigation(documentPreviewContent);
                }
            } else {
                documentPreviewContent.innerHTML = '<div class="error-message">Failed to load document content.</div>';
            }
        } catch (error) {
            console.error('Error loading document text:', error);
            documentPreviewContent.innerHTML = '<div class="error-message">Failed to load document content. Please try again.</div>';
        }
    }
    
    // Add page navigation for PDF documents
    function addPageNavigation(container) {
        const pageMarkers = container.querySelectorAll('.page-marker');
        if (pageMarkers.length <= 1) return;
        
        // Create navigation
        const navDiv = document.createElement('div');
        navDiv.className = 'page-navigation';
        navDiv.innerHTML = '<span>Jump to page: </span>';
        
        // Add page buttons
        pageMarkers.forEach((marker, index) => {
            // Extract page number
            const pageNumMatch = marker.textContent.match(/--- Page (\d+) ---/);
            if (!pageNumMatch) return;
            
            const pageNum = pageNumMatch[1];
            const pageButton = document.createElement('button');
            pageButton.className = 'btn btn-sm btn-outline-primary m-1';
            pageButton.textContent = pageNum;
            pageButton.addEventListener('click', () => {
                marker.scrollIntoView({ behavior: 'smooth', block: 'start' });
            });
            
            navDiv.appendChild(pageButton);
        });
        
        // Insert at the top of the container
        container.insertBefore(navDiv, container.firstChild);
    }
    
    // Select active document from preview
    function selectActiveDocument() {
        if (selectedDocumentId) {
            setActiveDocument(selectedDocumentId);
            closeModal();
        }
    }
    
    // Close modal
    function closeModal() {
        if (documentPreviewModal) {
            documentPreviewModal.classList.remove('show');
        }
        selectedDocumentId = null;
    }
    
    // Delete document
    async function deleteDocument(id) {
        if (!confirm('Are you sure you want to delete this document?')) return;
        
        try {
            await fetchAPI(`/api/documents/${id}`, { method: 'DELETE' });
            
            // Remove from list
            documentFiles = documentFiles.filter(doc => doc.id !== id);
            
            // Reset active document if it was deleted
            if (activeDocumentId === id) {
                activeDocumentId = null;
                
                // Reset UI
                if (activeSummaryDocument) {
                    activeSummaryDocument.innerHTML = '<span class="badge bg-primary">No document selected</span>';
                }
                
                // Disable summary actions
                if (regenerateSummaryBtn) regenerateSummaryBtn.disabled = true;
                if (copySummaryBtn) copySummaryBtn.disabled = true;
                if (chatWithDocumentBtn) chatWithDocumentBtn.disabled = true;
                
                // Clear summary
                if (summaryContent) {
                    summaryContent.innerHTML = '';
                    summaryContent.style.display = 'none';
                }
                
                // Restore welcome message
                if (summaryContainer) {
                    summaryContainer.innerHTML = `
                        <div class="summary-welcome">
                            <div class="summary-welcome-icon">
                                <i class="fas fa-file-alt"></i>
                            </div>
                            <h3>Select a document to view summary</h3>
                            <p>Upload a document or select one from your library to get an AI-powered summary.</p>
                        </div>
                    `;
                }
                
                // Hide chat panel
                if (chatPanel) {
                    chatPanel.style.display = 'none';
                }
            }
            
            renderDocumentList();
            showNotification('Document deleted successfully', 'success');
        } catch (error) {
            console.error('Error deleting document:', error);
            showNotification('Failed to delete document', 'danger');
        }
    }
    
    // Helper function to show loading indicator
    function showLoadingIndicator(container) {
        container.innerHTML = `
            <div class="loading-indicator">
                <i class="fas fa-spinner fa-spin"></i> Loading...
            </div>
        `;
    }
    
    // Helper function to show notifications
    function showNotification(message, type) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `alert alert-${type}`;
        notification.innerHTML = `
            <i class="fas ${type === 'success' ? 'fa-check-circle' : 
                            type === 'warning' ? 'fa-exclamation-triangle' : 
                            type === 'danger' ? 'fa-times-circle' : 
                            'fa-info-circle'}"></i>
            <span>${message}</span>
            <button class="alert-close"><i class="fas fa-times"></i></button>
        `;
        
        // Add to notifications container or create one
        let notificationsContainer = document.querySelector('.notifications-container');
        if (!notificationsContainer) {
            notificationsContainer = document.createElement('div');
            notificationsContainer.className = 'notifications-container';
            document.body.appendChild(notificationsContainer);
        }
        
        // Add notification to container
        notificationsContainer.appendChild(notification);
        
        // Setup close button
        const closeBtn = notification.querySelector('.alert-close');
        closeBtn.addEventListener('click', () => {
            notification.style.animation = 'slideOut 0.3s ease forwards';
            setTimeout(() => {
                notification.remove();
                
                // Remove container if empty
                if (notificationsContainer.children.length === 0) {
                    notificationsContainer.remove();
                }
            }, 300);
        });
        
        // Auto dismiss after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.style.animation = 'slideOut 0.3s ease forwards';
                setTimeout(() => {
                    if (notification.parentNode) {
                        notification.remove();
                        
                        // Remove container if empty
                        if (notificationsContainer.children.length === 0) {
                            notificationsContainer.remove();
                        }
                    }
                }, 300);
            }
        }, 5000);
    }
    
    // Helper function to make API calls
    async function fetchAPI(url, options = {}) {
        const response = await fetch(url, {
            ...options,
            credentials: 'same-origin'
        });
        
        if (!response.ok) {
            const text = await response.text();
            try {
                const json = JSON.parse(text);
                throw new Error(json.error || `API Error: ${response.status}`);
            } catch (e) {
                throw new Error(`API Error: ${response.status}`);
            }
        }
        
        return response.json();
    }
    
    // Helper Functions
    function getFileIcon(fileType) {
        switch (fileType) {
            case 'pdf':
                return 'fas fa-file-pdf';
            case 'docx':
                return 'fas fa-file-word';
            case 'txt':
                return 'fas fa-file-alt';
            default:
                return 'fas fa-file';
        }
    }
    
    function formatFileSize(bytes) {
        if (bytes < 1024) return bytes + ' B';
        else if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
        else return (bytes / 1048576).toFixed(1) + ' MB';
    }
    
    // CSS styles for document preview
    const style = document.createElement('style');
    style.textContent = `
        .document-text-preview {
            white-space: pre-wrap;
            font-family: monospace;
            line-height: 1.5;
            padding: 10px;
            max-height: 500px;
            overflow-y: auto;
        }
        
        .page-marker {
            background-color: var(--primary-light);
            color: var(--primary-color);
            padding: 5px;
            margin: 10px 0;
            font-weight: bold;
            border-radius: 4px;
        }
        
        .page-navigation {
            position: sticky;
            top: 0;
            background-color: var(--bg-color);
            padding: 10px;
            margin-bottom: 15px;
            border-bottom: 1px solid var(--border-color);
            z-index: 1;
        }
        
        .loading-progress {
            font-size: 0.8rem;
            color: var(--text-secondary);
        }
        
        .upload-status {
            margin-top: 10px;
        }
        
        .progress {
            height: 20px;
            border-radius: var(--radius-md);
            overflow: hidden;
            background-color: var(--bg-secondary);
        }
        
        .progress-bar {
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 0.8rem;
            transition: width 0.3s ease;
        }
        
        .chat-instructions {
            text-align: left;
            background-color: var(--bg-secondary);
            border-radius: var(--radius-md);
            padding: 10px;
            font-size: 0.9rem;
        }
        
        .chat-instructions ul {
            margin-left: 20px;
            margin-bottom: 0;
        }
        
        .chat-instructions li {
            margin-bottom: 5px;
            list-style-type: disc;
        }
    `;
    document.head.appendChild(style);
});