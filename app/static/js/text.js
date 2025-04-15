document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const toolItems = document.querySelectorAll('.tool-item');
    const toolTitle = document.getElementById('tool-title');
    const toolBadge = document.getElementById('tool-badge');
    const toolOptions = document.querySelectorAll('.tool-option-group');
    const optionButtons = document.querySelectorAll('.option-button');
    const textForm = document.getElementById('text-form');
    const inputText = document.getElementById('input-text');
    const processBtn = document.getElementById('process-btn');
    const resultContainer = document.getElementById('result-container');
    const resultText = document.getElementById('result-text');
    const copyBtn = document.getElementById('copy-btn');
    const saveBtn = document.getElementById('save-btn');
    const textHistory = document.getElementById('text-history');
    
    // State
    let currentTool = 'correct'; // Changed default from 'summarize' to 'correct'
    let history = [];
    
    // Initialize option buttons
    optionButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Remove active class from siblings
            const siblings = button.parentElement.querySelectorAll('.option-button');
            siblings.forEach(sibling => sibling.classList.remove('active'));
            
            // Add active class to clicked button
            button.classList.add('active');
        });
    });
    
    // Tool selection
    toolItems.forEach(item => {
        item.addEventListener('click', function() {
            const tool = this.dataset.tool;
            
            // Update UI
            toolItems.forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            
            // Update tool options
            toolOptions.forEach(options => {
                options.style.display = 'none';
            });
            
            const activeOptions = document.getElementById(`${tool}-options`);
            if (activeOptions) {
                activeOptions.style.display = 'block';
            }
            
            // Update tool title and badge
            const toolName = this.querySelector('h4').textContent;
            toolTitle.textContent = `${toolName} Text`;
            toolBadge.textContent = toolName;
            
            // Set current tool
            currentTool = tool;
            
            // Hide result container
            resultContainer.style.display = 'none';
        });
    });
    
    // Process text form submission
    textForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const text = inputText.value.trim();
        if (!text) {
            showNotification('Please enter some text to process', 'warning');
            return;
        }
        
        processText(text);
    });
    
    // Copy button
    copyBtn.addEventListener('click', function() {
        const text = resultText.textContent;
        navigator.clipboard.writeText(text)
            .then(() => {
                showNotification('Text copied to clipboard', 'success');
            })
            .catch(err => {
                console.error('Error copying text: ', err);
                showNotification('Failed to copy text', 'danger');
            });
    });
    
    // Save button
    saveBtn.addEventListener('click', function() {
        const text = resultText.textContent;
        const originalText = inputText.value.trim();
        
        // Add to history
        const historyItem = {
            id: Date.now(),
            tool: currentTool,
            toolName: toolBadge.textContent,
            originalText: originalText,
            processedText: text,
            timestamp: new Date().toISOString()
        };
        
        history.unshift(historyItem);
        
        // Update history UI
        renderHistory();
        
        showNotification('Text saved to history', 'success');
    });
    
    // Process text based on selected tool
    async function processText(text) {
        // Show loading state
        processBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
        processBtn.disabled = true;
        resultContainer.style.display = 'none';
        
        // Hide corrections panel
        const correctionsPanel = document.getElementById('corrections-panel');
        if (correctionsPanel) {
            correctionsPanel.style.display = 'none';
        }
        
        try {
            // Get selected options based on current tool
            let endpoint = `/api/text/${currentTool}`;
            let body = { text };
            
            // Add tool-specific options
            if (currentTool === 'rephrase') {
                const styleBtn = document.querySelector('#rephrase-options .option-button.active');
                body.style = styleBtn ? styleBtn.dataset.value : 'academic';
            } else if (currentTool === 'explain') {
                const levelBtn = document.querySelector('#explain-options .option-button.active');
                body.level = levelBtn ? levelBtn.dataset.value : 'high_school';
            }
            
            // Send request
            const response = await fetchAPI(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(body)
            });
            
            // Debug log the response
            console.log('API Response:', response);
            
            // Display result
            let result = '';
            
            if (currentTool === 'correct') {
                result = response.corrected_text;
                
                // Clean up any prefixes or explanations that might be in the corrected text
                result = cleanupCorrectedText(result);
                
                // Handle corrections if available
                if (response.corrections && response.corrections.length > 0) {
                    console.log('Corrections found:', response.corrections);
                    displayCorrections(result, response.corrections, response.original_text);
                } else {
                    console.log('No corrections found in response');
                    // Just display the corrected text normally
                    resultText.textContent = result;
                }
            } else if (currentTool === 'rephrase') {
                result = response.rephrased_text;
                resultText.textContent = result;
            } else if (currentTool === 'explain') {
                result = response.explanation;
                resultText.textContent = result;
            }
            
            if (result) {
                resultContainer.style.display = 'block';
            } else {
                throw new Error('No result returned from the server');
            }
        } catch (error) {
            console.error(`Error processing text with ${currentTool}:`, error);
            showNotification(error.message || `Failed to process text with ${currentTool}`, 'danger');
        } finally {
            // Reset button
            processBtn.innerHTML = 'Process Text';
            processBtn.disabled = false;
        }
    }
    
    // Display corrections with highlights
    function displayCorrections(correctedText, corrections, originalText) {
        const correctionsPanel = document.getElementById('corrections-panel');
        const correctionsList = document.getElementById('corrections-list');
        
        if (!correctionsPanel || !correctionsList) return;
        
        // Update the heading with count
        const heading = correctionsPanel.querySelector('h5');
        if (heading) {
            heading.textContent = `Corrections Made (${corrections.length})`;
        }
        
        // Display complete corrected text (without any highlights first)
        resultText.textContent = correctedText;
        
        // Sort corrections to process longer phrases first
        corrections.sort((a, b) => b.corrected.length - a.corrected.length);
        
        // Create simpler solution that uses a one-time replacement approach
        let processedHTML = escapeHtml(correctedText);
        let placeholders = [];
        
        // First pass: replace all corrections with placeholder markers
        corrections.forEach((correction, index) => {
            const correctedText = correction.corrected;
            // Simple text replacement (not using regex)
            const placeholder = `___CORRECTION_${index}___`;
            let position = processedHTML.indexOf(escapeHtml(correctedText));
            
            if (position !== -1) {
                // Store the data we'll need to restore
                placeholders.push({
                    placeholder: placeholder,
                    html: `<span class="highlight highlight-corrected" data-correction="${index}">${escapeHtml(correctedText)}</span>`,
                    position: position
                });
                // Replace just the first occurrence
                processedHTML = 
                    processedHTML.substring(0, position) + 
                    placeholder + 
                    processedHTML.substring(position + escapeHtml(correctedText).length);
            }
        });
        
        // Second pass: replace placeholders with actual HTML
        placeholders.forEach(item => {
            processedHTML = processedHTML.replace(item.placeholder, item.html);
        });
        
        // Set the HTML
        resultText.innerHTML = processedHTML;
        
        // Build the corrections list
        let correctionsHtml = '';
        corrections.forEach((correction, index) => {
            correctionsHtml += `
                <div class="correction-item" data-correction="${index}">
                    <div>
                        <span class="correction-original">${escapeHtml(correction.original)}</span>
                        <span class="correction-arrow">→</span>
                        <span class="correction-corrected">${escapeHtml(correction.corrected)}</span>
                    </div>
                    <div class="correction-explanation">${escapeHtml(correction.explanation)}</div>
                </div>
            `;
        });
        
        correctionsList.innerHTML = correctionsHtml;
        correctionsPanel.style.display = 'block';
        
        // Add event listeners to all interactive elements
        addCorrectionEventListeners();
    }
    
    // Add event listeners for correction elements
    function addCorrectionEventListeners() {
        // Add event listeners for correction items in the list
        document.querySelectorAll('.correction-item').forEach(item => {
            item.addEventListener('click', function() {
                const index = this.dataset.correction;
                highlightCorrection(index);
                
                // Add active class to this item
                document.querySelectorAll('.correction-item').forEach(el => el.classList.remove('active'));
                this.classList.add('active');
            });
        });
        
        // Add event listeners for highlight spans in the text
        document.querySelectorAll('.highlight').forEach(span => {
            span.addEventListener('click', function() {
                const index = this.dataset.correction;
                highlightCorrection(index);
                
                // Scroll to and activate the corresponding correction item
                const correctionItem = document.querySelector(`.correction-item[data-correction="${index}"]`);
                if (correctionItem) {
                    document.querySelectorAll('.correction-item').forEach(el => el.classList.remove('active'));
                    correctionItem.classList.add('active');
                    correctionItem.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                }
            });
        });
    }
    
    // Highlight a specific correction in the text
    function highlightCorrection(index) {
        // Remove active highlight from all spans
        document.querySelectorAll('.highlight').forEach(span => {
            span.classList.remove('highlight-active');
        });
        
        // Add active highlight to the selected span
        const span = document.querySelector(`.highlight[data-correction="${index}"]`);
        if (span) {
            span.classList.add('highlight-active');
            // Scroll to the span
            span.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }
    
    // Helper function to safely escape HTML
    function escapeHtml(text) {
        if (!text) return '';
        return text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }
    
    // Render history items
    function renderHistory() {
        if (history.length === 0) {
            textHistory.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-history"></i>
                    <p>No history yet. Process some text to see it here.</p>
                </div>
            `;
            return;
        }
        
        let html = '';
        
        history.forEach(item => {
            const preview = item.processedText.length > 100 
                ? item.processedText.substring(0, 100) + '...' 
                : item.processedText;
                
            const date = new Date(item.timestamp).toLocaleString();
            
            html += `
                <div class="history-item" data-id="${item.id}">
                    <div class="history-header">
                        <div class="history-title">${date}</div>
                        <div class="history-actions">
                            <div class="history-tool">${item.toolName}</div>
                            <button class="delete-history-item" data-id="${item.id}" title="Delete">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                    <div class="history-preview">${preview}</div>
                </div>
            `;
        });
        
        textHistory.innerHTML = html;
        
        // Add event listeners to history items
        document.querySelectorAll('.history-item').forEach(item => {
            item.addEventListener('click', function(e) {
                // Don't trigger if the delete button was clicked
                if (e.target.closest('.delete-history-item')) {
                    return;
                }
                
                const id = parseInt(this.dataset.id);
                const historyItem = history.find(h => h.id === id);
                
                if (historyItem) {
                    // Set input text
                    inputText.value = historyItem.originalText;
                    
                    // Set tool
                    const toolItem = document.querySelector(`.tool-item[data-tool="${historyItem.tool}"]`);
                    if (toolItem) {
                        toolItem.click();
                    }
                    
                    // Show result
                    resultText.textContent = historyItem.processedText;
                    resultContainer.style.display = 'block';
                    
                    // Scroll to form
                    textForm.scrollIntoView({ behavior: 'smooth' });
                }
            });
        });
        
        // Add event listeners for delete buttons
        document.querySelectorAll('.delete-history-item').forEach(button => {
            button.addEventListener('click', function(e) {
                e.stopPropagation(); // Prevent item selection
                const id = parseInt(this.dataset.id);
                deleteHistoryItem(id);
            });
        });
    }
    
    // Delete a single history item
    function deleteHistoryItem(id) {
        const index = history.findIndex(item => item.id === id);
        if (index !== -1) {
            history.splice(index, 1);
            renderHistory();
            showNotification('Item removed from history', 'info');
        }
    }
    
    // Initialize history
    renderHistory();
    
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
    
    // Helper function to show notifications
    function showNotification(message, type = 'info', duration = 5000) {
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
        
        // Auto dismiss after duration
        if (duration > 0) {
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.style.animation = 'slideOut 0.3s ease forwards';
                    setTimeout(() => {
                        if (notification.parentNode) {
                            notification.remove();
                        }
                        
                        // Remove container if empty
                        if (notificationsContainer.children.length === 0) {
                            notificationsContainer.remove();
                        }
                    }, 300);
                }
            }, duration);
        }
    }
    
    // Add 'Clear All' button functionality
    const clearHistoryBtn = document.getElementById('clear-history-btn');
    if (clearHistoryBtn) {
        clearHistoryBtn.addEventListener('click', function() {
            if (confirm('Are you sure you want to clear all history items?')) {
                history = [];
                renderHistory();
                showNotification('History cleared', 'info');
            }
        });
    }
    
    // Helper function to clean up any explanatory text that Claude might include
    function cleanupCorrectedText(text) {
        // Remove any explanatory prefixes that Claude sometimes adds
        const prefixesToRemove = [
            "Here is the corrected text:",
            "Corrected text:",
            "Here's the corrected text:",
            "The corrected text is:"
        ];
        
        let cleanedText = text;
        for (const prefix of prefixesToRemove) {
            if (cleanedText.startsWith(prefix)) {
                cleanedText = cleanedText.substring(prefix.length).trim();
            }
        }
        
        // Remove any JSON-like content or markers that might have leaked through
        if (cleanedText.includes("===CORRECTIONS_JSON===")) {
            cleanedText = cleanedText.split("===CORRECTIONS_JSON===")[0].trim();
        }
        
        if (cleanedText.includes("[{")) {
            cleanedText = cleanedText.split("[{")[0].trim();
        }
        
        return cleanedText;
    }
});