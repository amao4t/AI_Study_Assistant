// Updated study.js file with improved chat formatting and error handling

document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const toolItems = document.querySelectorAll('.tool-item');
    const toolPanels = document.querySelectorAll('.tool-panel');
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const chatContainer = document.getElementById('chat-container');
    const planForm = document.getElementById('plan-form');
    const planResult = document.getElementById('plan-result');
    const planOverview = document.getElementById('plan-overview');
    const planWeeks = document.getElementById('plan-weeks');
    const planTechniques = document.getElementById('plan-techniques');
    const planMilestones = document.getElementById('plan-milestones');
    const savePlanBtn = document.getElementById('save-plan-btn');
    const printPlanBtn = document.getElementById('print-plan-btn');
    const resourcesForm = document.getElementById('resources-form');
    const resourcesResult = document.getElementById('resources-result');
    const resourcesList = document.getElementById('resources-list');
    const techniquesForm = document.getElementById('techniques-form');
    const techniquesResult = document.getElementById('techniques-result');
    const techniquesList = document.getElementById('techniques-list');
    const sessionsList = document.getElementById('sessions-list');
    const startSessionBtn = document.getElementById('start-session-btn');
    const sessionModal = document.getElementById('session-modal');
    const sessionForm = document.getElementById('session-form');
    const sessionFormContainer = document.getElementById('session-form-container');
    const activeSessionContainer = document.getElementById('active-session-container');
    const activeSessionType = document.getElementById('active-session-type');
    const activeSessionStart = document.getElementById('active-session-start');
    const activeSessionNotes = document.getElementById('active-session-notes');
    const endSessionBtn = document.getElementById('end-session-btn');
    const timerHours = document.getElementById('timer-hours');
    const timerMinutes = document.getElementById('timer-minutes');
    const timerSeconds = document.getElementById('timer-seconds');
    const modalCloseBtn = document.querySelector('.modal-close');
    const sessionDocument = document.getElementById('session-document');
    const copyLastMessageBtn = document.getElementById('copy-last-message-btn');
    
    // State
    let chatHistory = [];
    let activeSessionId = null;
    let timerInterval = null;
    let sessionStartTime = null;
    
    // Initialize
    loadSessions();
    loadDocuments();
    
    // Tool Selection
    toolItems.forEach(item => {
        item.addEventListener('click', function() {
            const tool = this.dataset.tool;
            
            // Update UI
            toolItems.forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            
            // Show selected tool panel
            toolPanels.forEach(panel => {
                panel.style.display = 'none';
            });
            
            const activePanel = document.getElementById(`${tool}-tool`);
            if (activePanel) {
                activePanel.style.display = 'block';
            }
        });
    });
    
    // Chat Functionality
    if (chatForm && chatInput && chatContainer) {
        chatForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const message = chatInput.value.trim();
            if (!message) return;
            
            // Add user message to chat
            addMessageToChat(message, 'user');
            
            // Clear input
            chatInput.value = '';
            
            // Handle chat submission (improved)
            handleChatSubmit(message);
        });
    }
    
    // Copy last message button
    if (copyLastMessageBtn) {
        copyLastMessageBtn.addEventListener('click', copyLastMessage);
    }
    
    // Plan Functionality
    if (planForm) {
        planForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Get form data
            const subject = document.getElementById('subject').value;
            const goal = document.getElementById('goal').value;
            const timeframe = document.getElementById('timeframe').value;
            const hoursPerWeek = document.getElementById('hours-per-week').value;
            
            // Generate study plan
            generateStudyPlan(subject, goal, timeframe, hoursPerWeek);
        });
    }
    
    // Resources Functionality
    if (resourcesForm) {
        resourcesForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Get form data
            const subject = document.getElementById('resources-subject').value;
            const level = document.getElementById('level').value;
            const resourceType = document.querySelector('input[name="resource_type"]:checked').value;
            
            // Get resources
            getResources(subject, level, resourceType);
        });
    }
    
    // Techniques Functionality
    if (techniquesForm) {
        techniquesForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Get form data
            const subject = document.getElementById('techniques-subject').value;
            const learningStyle = document.getElementById('learning-style').value;
            
            // Get techniques
            getTechniques(subject, learningStyle);
        });
    }
    
    // Study Session Modal
    if (startSessionBtn) {
        startSessionBtn.addEventListener('click', function() {
            // Show modal
            if (sessionModal) {
                sessionModal.classList.add('show');
                
                // Show form, hide active session
                if (sessionFormContainer) sessionFormContainer.style.display = 'block';
                if (activeSessionContainer) activeSessionContainer.style.display = 'none';
            }
        });
    }
    
    if (modalCloseBtn) {
        modalCloseBtn.addEventListener('click', closeSessionModal);
    }
    
    function closeSessionModal() {
        if (sessionModal) {
            sessionModal.classList.remove('show');
        }
    }
    
    // Session Form Submission
    if (sessionForm) {
        sessionForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Get form data
            const sessionType = document.getElementById('session-type').value;
            const documentId = sessionDocument ? sessionDocument.value : null;
            const notes = document.getElementById('session-notes').value;
            
            // Start session
            startStudySession(sessionType, documentId, notes);
        });
    }
    
    // End Session
    if (endSessionBtn) {
        endSessionBtn.addEventListener('click', endStudySession);
    }
    
    // Handle chat submission with improved error handling
    async function handleChatSubmit(message) {
        // Show typing indicator
        const typingIndicator = document.createElement('div');
        typingIndicator.className = 'chat-bubble bot typing-indicator';
        typingIndicator.innerHTML = '<div class="typing-dots"><span></span><span></span><span></span></div>';
        chatContainer.appendChild(typingIndicator);
        chatContainer.scrollTop = chatContainer.scrollHeight;
        
        try {
            // Call API
            const response = await fetch('/api/study/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'same-origin',
                body: JSON.stringify({
                    message: message,
                    chat_history: chatHistory
                })
            });
            
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            
            const data = await response.json();
            
            // Remove typing indicator
            const indicator = document.querySelector('.typing-indicator');
            if (indicator) indicator.remove();
            
            // Add bot message
            if (data && data.response) {
                const messageEl = addMessageToChat(data.response, 'bot');
                
                // Show fallback warning if this is a fallback response
                if (data.is_fallback) {
                    messageEl.classList.add('fallback-response');
                    showFallbackWarning();
                }
                
                chatHistory = data.chat_history || [];
            } else {
                throw new Error('Invalid response from server');
            }
        } catch (error) {
            console.error('Error sending message:', error);
            
            // Remove typing indicator
            const indicator = document.querySelector('.typing-indicator');
            if (indicator) indicator.remove();
            
            // Add error message
            addMessageToChat('Sorry, I encountered an error. Please check your internet connection and try again.', 'bot');
            
            // Show error notification
            showNotification('Connection error. Please check your internet connection and try again.', 'danger');
        }
    }
    
    // Add message to chat - Improved for better formatting
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
        
        // Format message with simple Markdown
        message = formatMessageContent(message);
        
        // Use innerHTML with processed content
        messageEl.innerHTML = message;
        
        // Add message to chat
        chatContainer.appendChild(messageEl);
        
        // Scroll to bottom
        chatContainer.scrollTop = chatContainer.scrollHeight;
        
        return messageEl;
    }
    
    // Format message content with simple Markdown
    function formatMessageContent(message) {
        // Replace URLs with clickable links
        message = message.replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank">$1</a>');
        
        // Process ordered lists
        message = message.replace(/^\d+\.\s(.+)$/gm, '<li>$1</li>').replace(/(<li>.*<\/li>)/gs, '<ol>$1</ol>');
        
        // Process unordered lists
        message = message.replace(/^-\s(.+)$/gm, '<li>$1</li>').replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>');
        
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
    
    // Generate study plan
    async function generateStudyPlan(subject, goal, timeframe, hoursPerWeek) {
        if (!planForm || !planResult) return;
        
        // Show loading state
        const submitBtn = planForm.querySelector('button[type="submit"]');
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
        submitBtn.disabled = true;
        planResult.style.display = 'none';
        
        try {
            const response = await fetch('/api/study/plan', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'same-origin',
                body: JSON.stringify({
                    subject: subject,
                    goal: goal,
                    timeframe: timeframe,
                    hours_per_week: parseInt(hoursPerWeek)
                })
            });
            
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            
            const data = await response.json();
            
            // Check if this is a fallback response
            if (data.is_fallback) {
                showFallbackWarning();
            }
            
            // Display plan
            renderStudyPlan(data);
            planResult.style.display = 'block';
            showNotification('Study plan generated successfully', 'success');
        } catch (error) {
            console.error('Error generating study plan:', error);
            showNotification('Failed to generate study plan', 'danger');
        } finally {
            // Reset button
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        }
    }
    
    // Render study plan
    function renderStudyPlan(plan) {
        if (!planOverview || !planWeeks || !planTechniques || !planMilestones) return;
        
        // Overview
        planOverview.innerHTML = `<p>${plan.overview || 'No overview available'}</p>`;
        
        // Weeks
        planWeeks.innerHTML = '';
        if (plan.weeks && plan.weeks.length > 0) {
            plan.weeks.forEach(week => {
                const weekElement = document.createElement('div');
                weekElement.className = 'plan-week';
                
                let weekContent = `
                    <div class="plan-week-header">
                        <h6>Week ${week.week_number}</h6>
                        <span>${week.hours} hours</span>
                    </div>
                    <p><strong>Focus:</strong> ${week.focus_areas}</p>
                `;
                
                if (week.activities && week.activities.length > 0) {
                    weekContent += '<ul>';
                    week.activities.forEach(activity => {
                        weekContent += `<li>${activity}</li>`;
                    });
                    weekContent += '</ul>';
                }
                
                if (week.resources) {
                    weekContent += `<p><strong>Resources:</strong> ${week.resources}</p>`;
                }
                
                weekElement.innerHTML = weekContent;
                planWeeks.appendChild(weekElement);
            });
        } else {
            planWeeks.innerHTML = '<p>No weekly schedule available</p>';
        }
        
        // Techniques
        planTechniques.innerHTML = '';
        if (plan.techniques && plan.techniques.length > 0) {
            plan.techniques.forEach(technique => {
                const techElement = document.createElement('div');
                techElement.className = 'technique-item';
                techElement.innerHTML = `<h6>${technique}</h6>`;
                planTechniques.appendChild(techElement);
            });
        } else {
            planTechniques.innerHTML = '<p>No techniques available</p>';
        }
        
        // Milestones
        planMilestones.innerHTML = '';
        if (plan.milestones && plan.milestones.length > 0) {
            plan.milestones.forEach(milestone => {
                const milestoneElement = document.createElement('div');
                milestoneElement.className = 'milestone-item';
                milestoneElement.innerHTML = `<h6>${milestone}</h6>`;
                planMilestones.appendChild(milestoneElement);
            });
        } else {
            planMilestones.innerHTML = '<p>No milestones available</p>';
        }
    }
    
    // Get resources
    async function getResources(subject, level, resourceType) {
        if (!resourcesForm || !resourcesResult || !resourcesList) return;
        
        // Show loading state
        const submitBtn = resourcesForm.querySelector('button[type="submit"]');
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Searching...';
        submitBtn.disabled = true;
        resourcesResult.style.display = 'none';
        
        try {
            const response = await fetch('/api/study/resources', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'same-origin',
                body: JSON.stringify({
                    subject: subject,
                    level: level,
                    resource_type: resourceType
                })
            });
            
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            
            const data = await response.json();
            
            // Check if this is a fallback response
            if (data.is_fallback) {
                showFallbackWarning();
            }
            
            // Display resources
            renderResources(data.resources || []);
            resourcesResult.style.display = 'block';
            showNotification('Resources found successfully', 'success');
        } catch (error) {
            console.error('Error fetching resources:', error);
            showNotification('Failed to find resources', 'danger');
        } finally {
            // Reset button
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        }
    }
    
    // Render resources
    function renderResources(resources) {
        if (!resourcesList) return;
        
        resourcesList.innerHTML = '';
        
        if (resources.length === 0) {
            resourcesList.innerHTML = '<p>No resources found</p>';
            return;
        }
        
        resources.forEach(resource => {
            const resourceElement = document.createElement('div');
            resourceElement.className = 'resource-item';
            
            resourceElement.innerHTML = `
                <h6 class="resource-title">${resource.title}</h6>
                <div class="resource-meta">
                    <span><i class="fas fa-tag"></i> ${resource.type}</span>
                    <span><i class="fas fa-level-up-alt"></i> ${resource.level}</span>
                </div>
                <p>${resource.description}</p>
            `;
            
            resourcesList.appendChild(resourceElement);
        });
    }
    
    // Get techniques
    async function getTechniques(subject, learningStyle) {
        if (!techniquesForm || !techniquesResult || !techniquesList) return;
        
        // Show loading state
        const submitBtn = techniquesForm.querySelector('button[type="submit"]');
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Searching...';
        submitBtn.disabled = true;
        techniquesResult.style.display = 'none';
        
        try {
            const response = await fetch('/api/study/techniques', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'same-origin',
                body: JSON.stringify({
                    subject: subject,
                    learning_style: learningStyle
                })
            });
            
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            
            const data = await response.json();
            
            // Check if this is a fallback response
            if (data.is_fallback) {
                showFallbackWarning();
            }
            
            // Display techniques
            renderTechniques(data.techniques || []);
            techniquesResult.style.display = 'block';
            showNotification('Techniques found successfully', 'success');
        } catch (error) {
            console.error('Error fetching techniques:', error);
            showNotification('Failed to find techniques', 'danger');
        } finally {
            // Reset button
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        }
    }
    
    // Render techniques
    function renderTechniques(techniques) {
        if (!techniquesList) return;
        
        techniquesList.innerHTML = '';
        
        if (techniques.length === 0) {
            techniquesList.innerHTML = '<p>No techniques found</p>';
            return;
        }
        
        techniques.forEach(technique => {
            const techniqueElement = document.createElement('div');
            techniqueElement.className = 'technique-item';
            
            let techniqueContent = `
                <h6 class="technique-title">${technique.name}</h6>
                <p>${technique.description}</p>
            `;
            
            // Add steps if available
            if (technique.steps && technique.steps.length > 0) {
                techniqueContent += '<p><strong>Steps:</strong></p><ol>';
                technique.steps.forEach(step => {
                    techniqueContent += `<li>${step}</li>`;
                });
                techniqueContent += '</ol>';
            }
            
            if (technique.benefits) {
                techniqueContent += `<p><strong>Benefits:</strong> ${technique.benefits}</p>`;
            }
            
            techniqueElement.innerHTML = techniqueContent;
            techniquesList.appendChild(techniqueElement);
        });
    }
    
    // Load study sessions
    async function loadSessions() {
        if (!sessionsList) return;
        
        try {
            const response = await fetch('/api/study/sessions', {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'same-origin'
            });
            
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            
            const data = await response.json();
            renderSessions(data.sessions || []);
        } catch (error) {
            console.error('Error loading sessions:', error);
            if (sessionsList) {
                sessionsList.innerHTML = '<div class="error-message">Failed to load sessions</div>';
            }
        }
    }
    
    // Render sessions
    function renderSessions(sessions) {
        if (!sessionsList) return;
        
        if (sessions.length === 0) {
            sessionsList.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-clock"></i>
                    <p>No study sessions recorded yet. Start a session to track your progress.</p>
                </div>
            `;
            return;
        }
        
        sessionsList.innerHTML = '';
        sessions.forEach(session => {
            const sessionElement = document.createElement('div');
            sessionElement.className = 'session-item';
            
            // Calculate duration
            let durationText = 'In progress';
            if (session.end_time) {
                const duration = session.duration_minutes || 0;
                const hours = Math.floor(duration / 60);
                const minutes = Math.round(duration % 60);
                durationText = hours > 0 ? `${hours}h ${minutes}m` : `${minutes}m`;
            }
            
            // Format date
            const date = new Date(session.start_time).toLocaleDateString();
            const time = new Date(session.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            
            sessionElement.innerHTML = `
                <div class="session-header">
                    <div class="session-title">${session.session_type.charAt(0).toUpperCase() + session.session_type.slice(1)}</div>
                    <div class="session-duration">${durationText}</div>
                </div>
                <div class="session-meta">
                    ${date} at ${time}
                </div>
            `;
            
            sessionsList.appendChild(sessionElement);
        });
    }
    
    // Load documents for session form
    async function loadDocuments() {
        if (!sessionDocument) return;
        
        try {
            const response = await fetch('/api/documents/', {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'same-origin'
            });
            
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            
            const data = await response.json();
            
            if (data.documents && data.documents.length > 0) {
                let options = '<option value="">None</option>';
                data.documents.forEach(doc => {
                    options += `<option value="${doc.id}">${doc.filename}</option>`;
                });
                
                sessionDocument.innerHTML = options;
            }
        } catch (error) {
            console.error('Error loading documents:', error);
        }
    }
    
    // Start study session
    async function startStudySession(sessionType, documentId, notes) {
        if (!sessionModal) return;
        
        try {
            const response = await fetch('/api/study/session/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'same-origin',
                body: JSON.stringify({
                    session_type: sessionType,
                    document_id: documentId,
                    notes: notes
                })
            });
            
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            
            const data = await response.json();
            
            if (data && data.session_id) {
                // Set active session ID
                activeSessionId = data.session_id;
                
                // Show active session UI
                if (sessionFormContainer) sessionFormContainer.style.display = 'none';
                if (activeSessionContainer) activeSessionContainer.style.display = 'block';
                
                // Set session details
                if (activeSessionType) activeSessionType.textContent = sessionType.charAt(0).toUpperCase() + sessionType.slice(1);
                if (activeSessionStart) activeSessionStart.textContent = new Date().toLocaleString();
                if (activeSessionNotes) activeSessionNotes.value = notes;
                
                // Start timer
                sessionStartTime = new Date();
                startTimer();
                
                showNotification('Study session started', 'success');
            } else {
                throw new Error('Failed to start session');
            }
        } catch (error) {
            console.error('Error starting session:', error);
            showNotification('Failed to start session', 'danger');
            closeSessionModal();
        }
    }
    
    // End study session
    async function endStudySession() {
        if (!activeSessionId) {
            showNotification('No active session to end', 'warning');
            closeSessionModal();
            return;
        }
        
        try {
            const response = await fetch(`/api/study/session/${activeSessionId}/end`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'same-origin',
                body: JSON.stringify({
                    notes: activeSessionNotes ? activeSessionNotes.value : ''
                })
            });
            
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            
            // Stop timer
            stopTimer();
            
            // Reset active session
            activeSessionId = null;
            
            // Close modal
            closeSessionModal();
            
            // Reload sessions
            loadSessions();
            
            showNotification('Study session ended', 'success');
        } catch (error) {
            console.error('Error ending session:', error);
            showNotification('Failed to end session', 'danger');
        }
    }
    
    // Timer functions
    function startTimer() {
        // Clear existing timer
        stopTimer();
        
        // Start new timer
        timerInterval = setInterval(updateTimer, 1000);
        updateTimer(); // Update immediately
    }
    
    function stopTimer() {
        if (timerInterval) {
            clearInterval(timerInterval);
            timerInterval = null;
        }
    }
    
    function updateTimer() {
        if (!sessionStartTime || !timerHours || !timerMinutes || !timerSeconds) return;
        
        const now = new Date();
        const diffSeconds = Math.floor((now - sessionStartTime) / 1000);
        
        const hours = Math.floor(diffSeconds / 3600);
        const minutes = Math.floor((diffSeconds % 3600) / 60);
        const seconds = diffSeconds % 60;
        
        timerHours.textContent = hours.toString().padStart(2, '0');
        timerMinutes.textContent = minutes.toString().padStart(2, '0');
        timerSeconds.textContent = seconds.toString().padStart(2, '0');
    }
    
    // Save plan button
    if (savePlanBtn) {
        savePlanBtn.addEventListener('click', function() {
            showNotification('Study plan saved successfully', 'success');
        });
    }
    
    // Print plan button
    if (printPlanBtn) {
        printPlanBtn.addEventListener('click', function() {
            const printWindow = window.open('', '_blank');
            
            if (!printWindow) {
                showNotification('Pop-up blocked. Please allow pop-ups for this site.', 'warning');
                return;
            }
            
            if (!planOverview || !planWeeks || !planTechniques || !planMilestones) {
                showNotification('Plan content not available', 'warning');
                return;
            }
            
            const planContent = `
            <!DOCTYPE html>
            <html>
            <head>
                <title>Study Plan</title>
                <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; }
                    h1 { color: #0E8388; }
                    .section { margin-bottom: 20px; }
                    .week { border: 1px solid #ccc; padding: 10px; margin-bottom: 10px; }
                    .technique, .milestone { margin-bottom: 10px; }
                </style>
            </head>
            <body>
                <h1>Your Study Plan</h1>
                <div class="section">
                    <h2>Overview</h2>
                    ${planOverview.innerHTML}
                </div>
                <div class="section">
                    <h2>Weekly Schedule</h2>
                    ${planWeeks.innerHTML}
                </div>
                <div class="section">
                    <h2>Recommended Study Techniques</h2>
                    ${planTechniques.innerHTML}
                </div>
                <div class="section">
                    <h2>Milestones & Progress Tracking</h2>
                    ${planMilestones.innerHTML}
                </div>
            </body>
            </html>
            `;
            
            printWindow.document.open();
            printWindow.document.write(planContent);
            printWindow.document.close();
            printWindow.print();
        });
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
            dismissNotification(notification);
        });
        
        // Auto dismiss after duration
        if (duration > 0) {
            setTimeout(() => {
                dismissNotification(notification);
            }, duration);
        }
        
        function dismissNotification(notification) {
            notification.style.animation = 'slideOut 0.3s ease forwards';
            setTimeout(() => {
                notification.remove();
                
                // Remove container if empty
                if (notificationsContainer.children.length === 0) {
                    notificationsContainer.remove();
                }
            }, 300);
        }
    }
});