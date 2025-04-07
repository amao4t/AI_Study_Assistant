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
    let currentTool = 'summarize';
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
        
        try {
            // Get selected options based on current tool
            let endpoint = `/api/text/${currentTool}`;
            let body = { text };
            
            // Add tool-specific options
            if (currentTool === 'summarize') {
                const lengthBtn = document.querySelector('#summarize-options .option-buttons:first-child .option-button.active');
                const formatBtn = document.querySelector('#summarize-options .option-buttons:last-child .option-button.active');
                
                body.length = lengthBtn ? lengthBtn.dataset.value : 'medium';
                body.format = formatBtn ? formatBtn.dataset.value : 'paragraph';
            } else if (currentTool === 'rephrase') {
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
            
            // Display result
            let result = '';
            
            if (currentTool === 'summarize') {
                result = response.summary;
            } else if (currentTool === 'correct') {
                result = response.corrected_text;
            } else if (currentTool === 'rephrase') {
                result = response.rephrased_text;
            } else if (currentTool === 'explain') {
                result = response.explanation;
            }
            
            if (result) {
                resultText.textContent = result;
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
                        <div class="history-tool">${item.toolName}</div>
                    </div>
                    <div class="history-preview">${preview}</div>
                </div>
            `;
        });
        
        textHistory.innerHTML = html;
        
        // Add event listeners to history items
        document.querySelectorAll('.history-item').forEach(item => {
            item.addEventListener('click', function() {
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
    }
    
    // Initialize history
    renderHistory();
});