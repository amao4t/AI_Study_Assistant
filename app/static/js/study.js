// Fixed study.js file with improved handling for techniques and resources

document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const toolItems = document.querySelectorAll('.tool-item');
    const toolPanels = document.querySelectorAll('.tool-panel');
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
    const clearAllSessionsBtn = document.getElementById('clear-all-sessions-btn');
    const plansList = document.getElementById('plans-list');
    const clearAllPlansBtn = document.getElementById('clear-all-plans-btn');
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
    
    // State
    let activeSessionId = null;
    let timerInterval = null;
    let sessionStartTime = null;
    let currentPlanData = null;
    
    // Initialize
    loadSessions();
    loadDocuments();
    loadSavedPlans();
    
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
    
    // Techniques Functionality - Fixed issue with form submission
    if (techniquesForm) {
        techniquesForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Get form data
            const subject = document.getElementById('techniques-subject').value;
            const learningStyle = document.getElementById('learning-style').value;
            
            // Show loading state
            const submitBtn = techniquesForm.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Searching...';
            submitBtn.disabled = true;
            
            // Get techniques with proper error handling
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
    
    // Render study plan with improved visual structure
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
                
                // Check if technique is string or object
                if (typeof technique === 'string') {
                    techElement.innerHTML = `<h6>${technique}</h6>`;
                } else if (typeof technique === 'object') {
                    const title = technique.name || technique.title || technique.toString();
                    let techniqueContent = `<h6>${title}</h6>`;
                    
                    if (technique.description) {
                        techniqueContent += `<p>${technique.description}</p>`;
                    }
                    
                    techElement.innerHTML = techniqueContent;
                } else {
                    techElement.innerHTML = `<h6>${technique}</h6>`;
                }
                
                planTechniques.appendChild(techElement);
            });
        } else {
            planTechniques.innerHTML = '<p>No techniques available</p>';
        }
        
        // Milestones
        planMilestones.innerHTML = '';
        if (plan.milestones && plan.milestones.length > 0) {
            plan.milestones.forEach((milestone, index) => {
                const milestoneElement = document.createElement('div');
                milestoneElement.className = 'milestone-item';
                
                // Handle different milestone formats (string or object)
                if (typeof milestone === 'string') {
                    milestoneElement.innerHTML = `<h6>${milestone}</h6>`;
                } else if (typeof milestone === 'object') {
                    // Check if milestone is just [object Object] and apply better handling
                    let milestoneText = '';
                    
                    if (milestone.text || milestone.description || milestone.name) {
                        milestoneText = milestone.text || milestone.description || milestone.name;
                    } else if (milestone.toString() === '[object Object]') {
                        milestoneText = `Milestone ${index + 1}`;
                    } else {
                        milestoneText = milestone.toString();
                    }
                    
                    milestoneElement.innerHTML = `<h6>${milestoneText}</h6>`;
                } else {
                    milestoneElement.innerHTML = `<h6>${milestone.toString()}</h6>`;
                }
                
                planMilestones.appendChild(milestoneElement);
            });
        } else {
            planMilestones.innerHTML = '<p>No milestones available</p>';
        }
    }
    
    // Get resources - FIXED to properly create clickable links
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
    
   // Completely rewritten renderResources function with forced links
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
        
        // Get resource info
        const title = resource.title || 'Resource';
        const type = resource.type || 'resource';
        const description = resource.description || '';
        const level = resource.level || 'All levels';
        
        // Create search URL based on resource type
        let searchUrl = '';
        if (type.toLowerCase().includes('book')) {
            searchUrl = `https://www.amazon.com/s?k=${encodeURIComponent(title)}`;
        } 
        else if (type.toLowerCase().includes('course')) {
            searchUrl = `https://www.coursera.org/search?query=${encodeURIComponent(title)}`;
        }
        else if (type.toLowerCase().includes('video')) {
            searchUrl = `https://www.youtube.com/results?search_query=${encodeURIComponent(title)}`;
        }
        else if (title.includes('Khan Academy')) {
            searchUrl = 'https://www.khanacademy.org/';
        }
        else if (title.includes('Coursera')) {
            searchUrl = 'https://www.coursera.org/';
        }
        else {
            searchUrl = `https://www.google.com/search?q=${encodeURIComponent(title)}`;
        }
        
        // Create HTML with forced link
        resourceElement.innerHTML = `
            <h6 class="resource-title">
                <a href="${searchUrl}" target="_blank" class="resource-link">${title}</a>
            </h6>
            <div class="resource-meta">
                <span><i class="fas fa-tag"></i> ${type}</span>
                <span><i class="fas fa-level-up-alt"></i> ${level}</span>
            </div>
            <p>${description}</p>
        `;
        
        resourcesList.appendChild(resourceElement);
    });
    
    // Add CSS to make resource links more visible
    const style = document.createElement('style');
    style.textContent = `
        .resource-link {
            color: var(--primary-color);
            text-decoration: none;
            font-weight: bold;
        }
        
        .resource-link:hover {
            text-decoration: underline;
        }
    `;
    document.head.appendChild(style);
}

    // Get techniques - FIXED to properly handle errors and form submission
    async function getTechniques(subject, learningStyle) {
        if (!techniquesForm || !techniquesResult || !techniquesList) return;
        
        // Show loading state
        const submitBtn = techniquesForm.querySelector('button[type="submit"]');
        const originalText = submitBtn.innerHTML || 'Suggest Techniques';
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Searching...';
        submitBtn.disabled = true;
        techniquesResult.style.display = 'none';
        
        try {
            console.log('Fetching techniques for:', subject, learningStyle);
            
            // Show immediate feedback to user
            techniquesList.innerHTML = `
                <div class="loading-indicator">
                    <i class="fas fa-spinner fa-spin"></i> Finding study techniques for ${subject}...
                </div>
            `;
            techniquesResult.style.display = 'block';
            
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
            
            // Handle different types of errors
            if (!response.ok) {
                let errorMessage = 'Failed to fetch study techniques.';
                
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.error || errorMessage;
                } catch (e) {
                    // If we can't parse the JSON, use the status text
                    errorMessage = response.statusText || errorMessage;
                }
                
                // For 500 errors, provide more helpful message
                if (response.status === 500) {
                    errorMessage = "The server encountered an error processing your request. This feature may be temporarily unavailable.";
                    
                    // Fallback to generating generic techniques (client-side fallback)
                    const fallbackTechniques = generateFallbackTechniques(subject, learningStyle);
                    renderTechniques(fallbackTechniques);
                    
                    // Show warning to user
                    showNotification("Using generated techniques due to server error. These are general suggestions only.", 'warning');
                    return;
                }
                
                throw new Error(errorMessage);
            }
            
            const data = await response.json();
            console.log('Techniques response:', data);
            
            // Display techniques
            renderTechniques(data.techniques || []);
            techniquesResult.style.display = 'block';
            showNotification('Study techniques found successfully', 'success');
        } catch (error) {
            console.error('Error fetching techniques:', error);
            techniquesList.innerHTML = `
                <div class="error-message">
                    <p>Error: ${error.message}</p>
                    <p class="mt-3">Please try again later or try another feature.</p>
                </div>
            `;
            techniquesResult.style.display = 'block';
            showNotification('Failed to find techniques: ' + error.message, 'danger');
        } finally {
            // Reset button
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        }
    }

    // Client-side fallback for when the server fails
function generateFallbackTechniques(subject, learningStyle) {
    const fallbackTechniques = [
        {
            name: "Active Recall",
            description: `Test yourself on ${subject} concepts by writing questions and answering them without looking at your notes.`,
            benefits: "Strengthens memory pathways and identifies knowledge gaps."
        },
        {
            name: "Spaced Repetition",
            description: `Review ${subject} material at increasing intervals over time.`,
            benefits: "Optimizes memorization and retention."
        },
        {
            name: "Pomodoro Technique",
            description: "Study in focused 25-minute intervals with 5-minute breaks between them.",
            benefits: "Improves focus and prevents burnout during long study sessions."
        }
    ];
    
    // Add learning style specific technique if provided
    if (learningStyle) {
        if (learningStyle.toLowerCase().includes("visual")) {
            fallbackTechniques.push({
                name: "Mind Mapping",
                description: `Create diagrams that connect ${subject} concepts visually.`,
                benefits: "Excellent for visual learners, creating spatial memory connections."
            });
        } else if (learningStyle.toLowerCase().includes("auditory")) {
            fallbackTechniques.push({
                name: "Verbal Repetition",
                description: `Read ${subject} material aloud and record yourself for later review.`,
                benefits: "Leverages auditory learning preferences for better retention."
            });
        }
    }
    
    return fallbackTechniques;
}
    
    // Render techniques - FIXED to handle different data formats with improved visual structure
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
            
            // Handle different formats of technique data
            if (typeof technique === 'string') {
                // Simple string format - create a more structured display
                const title = technique;
                techniqueElement.innerHTML = `
                    <h6 class="technique-title">${title}</h6>
                    <p>Apply this technique to improve your study effectiveness.</p>
                `;
            } else {
                // Object format with potentially more details
                const title = technique.name || technique.title || 'Study Technique';
                const description = technique.description || '';
                const benefits = technique.benefits || '';
                
                let techniqueContent = `<h6 class="technique-title">${title}</h6>`;
                
                if (description) {
                    techniqueContent += `<p>${description}</p>`;
                }
                
                // Add steps if available
                if (technique.steps && technique.steps.length > 0) {
                    techniqueContent += '<p><strong>Steps:</strong></p><ol>';
                    technique.steps.forEach(step => {
                        techniqueContent += `<li>${step}</li>`;
                    });
                    techniqueContent += '</ol>';
                }
                
                if (benefits) {
                    techniqueContent += `<p><strong>Benefits:</strong> ${benefits}</p>`;
                }
                
                techniqueElement.innerHTML = techniqueContent;
            }
            
            techniquesList.appendChild(techniqueElement);
        });
        
        // If techniques is an object but not an array, handle that case
        if (!Array.isArray(techniques) && typeof techniques === 'object') {
            techniquesList.innerHTML = '<p>Received data in unexpected format. Please try again.</p>';
        }
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
        
        if (!sessions || sessions.length === 0) {
            sessionsList.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-clock"></i>
                    <p>No study sessions recorded yet. Start a session to track your progress.</p>
                </div>
            `;
            return;
        }
        
        let html = '';
        
        sessions.forEach(session => {
            const date = new Date(session.start_time).toLocaleString();
            const active = session.end_time ? false : true;
            
            // Calculate duration
            let duration = '...';
            if (session.end_time) {
                const start = new Date(session.start_time);
                const end = new Date(session.end_time);
                const durationMs = end - start;
                const hours = Math.floor(durationMs / (1000 * 60 * 60));
                const minutes = Math.floor((durationMs % (1000 * 60 * 60)) / (1000 * 60));
                duration = `${hours}h ${minutes}m`;
            }
            
            html += `
                <div class="session-item" data-id="${session.id}">
                    <div class="session-header">
                        <div class="session-title">${session.session_type}</div>
                        <div class="session-duration">${duration}</div>
                    </div>
                    <div class="session-meta">
                        ${date}
                        ${session.paused ? '<span class="badge bg-warning">Paused</span>' : ''}
                        ${active && !session.paused ? '<span class="badge bg-success">Active</span>' : ''}
                    </div>
                    ${session.notes ? `<div class="session-notes">${session.notes}</div>` : ''}
                    <div class="session-actions">
                        ${active && !session.paused ? `
                            <button class="session-action-btn pause" data-id="${session.id}" title="Pause">
                                <i class="fas fa-pause"></i> Pause
                            </button>
                        ` : ''}
                        ${session.paused ? `
                            <button class="session-action-btn resume" data-id="${session.id}" title="Resume">
                                <i class="fas fa-play"></i> Resume
                            </button>
                        ` : ''}
                        <button class="session-action-btn delete" data-id="${session.id}" title="Delete">
                            <i class="fas fa-trash"></i> Delete
                        </button>
                    </div>
                </div>
            `;
        });
        
        sessionsList.innerHTML = html;
        
        // Add event listeners for action buttons
        document.querySelectorAll('.session-action-btn.pause').forEach(btn => {
            btn.addEventListener('click', function() {
                const sessionId = this.dataset.id;
                pauseStudySession(sessionId);
            });
        });
        
        document.querySelectorAll('.session-action-btn.resume').forEach(btn => {
            btn.addEventListener('click', function() {
                const sessionId = this.dataset.id;
                resumeStudySession(sessionId);
            });
        });
        
        document.querySelectorAll('.session-action-btn.delete').forEach(btn => {
            btn.addEventListener('click', function() {
                const sessionId = this.dataset.id;
                deleteStudySession(sessionId);
            });
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
        savePlanBtn.addEventListener('click', function(e) {
            e.preventDefault();
            savePlan();
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
    
    // Pause a study session
    async function pauseStudySession(sessionId) {
        try {
            const response = await fetch(`/api/study/sessions/${sessionId}/pause`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'same-origin'
            });
            
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            
            // Check if this is the active session
            if (activeSessionId === parseInt(sessionId)) {
                // Stop the timer
                stopTimer();
                // Close the modal
                closeSessionModal();
                // Reset active session
                activeSessionId = null;
            }
            
            // Reload sessions
            await loadSessions();
            
            showNotification('Session paused', 'success');
        } catch (error) {
            console.error('Error pausing session:', error);
            showNotification('Failed to pause session', 'danger');
        }
    }
    
    // Resume a study session
    async function resumeStudySession(sessionId) {
        try {
            const response = await fetch(`/api/study/sessions/${sessionId}/resume`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'same-origin'
            });
            
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            
            // Set as active session
            activeSessionId = parseInt(sessionId);
            
            // Get session data
            const sessionsResponse = await fetch('/api/study/sessions');
            const sessions = await sessionsResponse.json();
            const session = sessions.find(s => s.id === parseInt(sessionId));
            
            if (session) {
                // Show modal with active session
                sessionModal.classList.add('show');
                sessionFormContainer.style.display = 'none';
                activeSessionContainer.style.display = 'block';
                
                // Set session info
                activeSessionType.textContent = session.session_type;
                activeSessionStart.textContent = new Date(session.start_time).toLocaleString();
                if (session.notes) {
                    activeSessionNotes.value = session.notes;
                }
                
                // Start timer
                sessionStartTime = new Date(session.start_time);
                startTimer();
            }
            
            // Reload sessions
            await loadSessions();
            
            showNotification('Session resumed', 'success');
        } catch (error) {
            console.error('Error resuming session:', error);
            showNotification('Failed to resume session', 'danger');
        }
    }
    
    // Delete a study session
    async function deleteStudySession(sessionId) {
        if (!confirm('Are you sure you want to delete this study session?')) {
            return;
        }
        
        try {
            const response = await fetch(`/api/study/sessions/${sessionId}`, {
                method: 'DELETE',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'same-origin'
            });
            
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            
            // Check if this is the active session
            if (activeSessionId === parseInt(sessionId)) {
                // Stop the timer
                stopTimer();
                // Close the modal
                closeSessionModal();
                // Reset active session
                activeSessionId = null;
            }
            
            // Reload sessions
            await loadSessions();
            
            showNotification('Session deleted', 'success');
        } catch (error) {
            console.error('Error deleting session:', error);
            showNotification('Failed to delete session', 'danger');
        }
    }
    
    // Clear all study sessions
    async function clearAllSessions() {
        if (!confirm('Are you sure you want to delete ALL study sessions? This cannot be undone.')) {
            return;
        }
        
        try {
            const response = await fetch('/api/study/sessions/clear', {
                method: 'DELETE',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'same-origin'
            });
            
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            
            // Stop any active session
            if (activeSessionId) {
                stopTimer();
                closeSessionModal();
                activeSessionId = null;
            }
            
            // Reload sessions
            await loadSessions();
            
            showNotification('All sessions cleared', 'success');
        } catch (error) {
            console.error('Error clearing sessions:', error);
            showNotification('Failed to clear sessions', 'danger');
        }
    }

    // Save study plan
    async function savePlan() {
        if (!planResult || !planResult.style.display || planResult.style.display === 'none') {
            showNotification('No plan to save. Please generate a plan first.', 'warning');
            return;
        }
        
        try {
            // Get current plan data
            const subject = document.getElementById('subject').value;
            const planData = {
                subject: subject,
                overview: planOverview ? planOverview.innerHTML : '',
                weeks: planWeeks ? planWeeks.innerHTML : '',
                techniques: planTechniques ? planTechniques.innerHTML : '',
                milestones: planMilestones ? planMilestones.innerHTML : '',
                created_at: new Date().toISOString()
            };
            
            const response = await fetch('/api/study/plans', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'same-origin',
                body: JSON.stringify(planData)
            });
            
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            
            // Reload saved plans to update the UI
            await loadSavedPlans();
            
            showNotification('Study plan saved successfully', 'success');
        } catch (error) {
            console.error('Error saving study plan:', error);
            showNotification('Failed to save study plan', 'danger');
        }
    }

    // Clear all plans button
    if (clearAllPlansBtn) {
        clearAllPlansBtn.addEventListener('click', function() {
            clearAllPlans();
        });
    }

    // Load saved plans
    async function loadSavedPlans() {
        if (!plansList) return;
        
        try {
            const response = await fetch('/api/study/plans', {
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
            renderSavedPlans(data.plans || []);
        } catch (error) {
            console.error('Error loading saved plans:', error);
            if (plansList) {
                plansList.innerHTML = '<div class="error-message">Failed to load saved plans</div>';
            }
        }
    }

    // Render saved plans
    function renderSavedPlans(plans) {
        if (!plansList) return;
        
        if (!plans || plans.length === 0) {
            plansList.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-clock"></i>
                    <p>No saved plans found.</p>
                </div>
            `;
            return;
        }
        
        let html = '';
        
        plans.forEach(plan => {
            const date = new Date(plan.created_at).toLocaleString();
            
            html += `
                <div class="plan-item" data-id="${plan.id}">
                    <div class="plan-header">
                        <div class="plan-title">${plan.subject}</div>
                        <div class="plan-date">${date}</div>
                    </div>
                    <div class="plan-actions">
                        <button class="plan-action-btn view" data-id="${plan.id}" title="View">
                            <i class="fas fa-eye"></i> View
                        </button>
                        <button class="plan-action-btn delete" data-id="${plan.id}" title="Delete">
                            <i class="fas fa-trash"></i> Delete
                        </button>
                    </div>
                </div>
            `;
        });
        
        plansList.innerHTML = html;
        
        // Add event listeners for action buttons
        document.querySelectorAll('.plan-action-btn.view').forEach(btn => {
            btn.addEventListener('click', function() {
                const planId = this.dataset.id;
                viewPlan(planId);
            });
        });
        
        document.querySelectorAll('.plan-action-btn.delete').forEach(btn => {
            btn.addEventListener('click', function() {
                const planId = this.dataset.id;
                deletePlan(planId);
            });
        });
    }

    // View a plan
    async function viewPlan(planId) {
        if (!planId) return;
        
        try {
            const response = await fetch(`/api/study/plans/${planId}`, {
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
            
            // Display plan directly from saved HTML strings
            if (!planOverview || !planWeeks || !planTechniques || !planMilestones) return;
            
            // Set content directly from saved HTML
            planOverview.innerHTML = data.overview || '<p>No overview available</p>';
            planWeeks.innerHTML = data.weeks || '<p>No weekly schedule available</p>';
            planTechniques.innerHTML = data.techniques || '<p>No techniques available</p>';
            planMilestones.innerHTML = data.milestones || '<p>No milestones available</p>';
            
            // Show the plan result container
            planResult.style.display = 'block';
            showNotification('Plan loaded successfully', 'success');
        } catch (error) {
            console.error('Error loading plan:', error);
            showNotification('Failed to load plan', 'danger');
        }
    }

    // Delete a plan
    async function deletePlan(planId) {
        if (!confirm('Are you sure you want to delete this plan? This cannot be undone.')) {
            return;
        }
        
        try {
            const response = await fetch(`/api/study/plans/${planId}`, {
                method: 'DELETE',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'same-origin'
            });
            
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            
            // Reload saved plans
            await loadSavedPlans();
            
            showNotification('Plan deleted', 'success');
        } catch (error) {
            console.error('Error deleting plan:', error);
            showNotification('Failed to delete plan', 'danger');
        }
    }

    // Clear all plans
    async function clearAllPlans() {
        if (!confirm('Are you sure you want to delete ALL saved plans? This cannot be undone.')) {
            return;
        }
        
        try {
            const response = await fetch('/api/study/plans/clear', {
                method: 'DELETE',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'same-origin'
            });
            
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            
            // Reload saved plans
            await loadSavedPlans();
            
            showNotification('All plans cleared', 'success');
        } catch (error) {
            console.error('Error clearing plans:', error);
            showNotification('Failed to clear plans', 'danger');
        }
    }
});