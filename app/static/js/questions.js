// Complete questions.js file with quiz submission functionality

document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const generateForm = document.getElementById('generate-form');
    const documentSelect = document.getElementById('document-select');
    const questionCountInput = document.getElementById('question-count');
    const questionCountValue = document.getElementById('question-count-value');
    const savedQuestionsContainer = document.getElementById('saved-questions');
    const quizContainer = document.getElementById('quiz-container');
    const quizInfo = document.getElementById('quiz-info');
    const checkAnswersBtn = document.getElementById('check-answers-btn');
    const saveQuestionsBtn = document.getElementById('save-questions-btn');
    
    // State
    let documents = [];
    let currentQuestions = [];
    let savedQuestionSets = [];
    
    // Initialize
    loadDocuments();
    loadSavedQuestions();
    
    // Update question count display
    if (questionCountInput && questionCountValue) {
        questionCountInput.addEventListener('input', () => {
            questionCountValue.textContent = questionCountInput.value;
        });
    }
    
    // Event Listeners
    if (generateForm) {
        generateForm.addEventListener('submit', handleGenerateQuestions);
    }
    
    if (checkAnswersBtn) {
        checkAnswersBtn.addEventListener('click', checkAnswers);
    }
    
    if (saveQuestionsBtn) {
        saveQuestionsBtn.addEventListener('click', saveCurrentQuestions);
    }
    
    // Load documents for the select dropdown
    async function loadDocuments() {
        try {
            const response = await fetchAPI('/api/documents/');
            documents = response.documents || [];
            
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
            if (documentSelect) {
                documentSelect.innerHTML = '<option value="">Failed to load documents</option>';
            }
            showNotification('Failed to load documents', 'danger');
        }
    }
    
    // Load saved questions
    async function loadSavedQuestions() {
        if (!savedQuestionsContainer) return;
        
        try {
            const response = await fetchAPI('/api/questions/');
            
            // Group questions by document
            const groupedQuestions = {};
            (response.questions || []).forEach(question => {
                if (!groupedQuestions[question.document_id]) {
                    groupedQuestions[question.document_id] = [];
                }
                groupedQuestions[question.document_id].push(question);
            });
            
            // Transform into question sets
            savedQuestionSets = Object.keys(groupedQuestions).map(docId => {
                const questions = groupedQuestions[docId];
                const document = documents.find(d => d.id === parseInt(docId));
                return {
                    document_id: parseInt(docId),
                    document_name: document ? document.filename : 'Unknown Document',
                    questions: questions,
                    question_type: questions[0].question_type,
                    created_at: questions[0].created_at
                };
            });
            
            renderSavedQuestions();
        } catch (error) {
            console.error('Error loading saved questions:', error);
            savedQuestionsContainer.innerHTML = '<div class="error-message">Failed to load saved questions</div>';
        }
    }
    
    // Render saved questions
    function renderSavedQuestions() {
        if (!savedQuestionsContainer) return;
        
        if (savedQuestionSets.length === 0) {
            savedQuestionsContainer.innerHTML = '<div class="empty-state">No saved questions found</div>';
            return;
        }
        
        let html = '';
        savedQuestionSets.forEach((set, index) => {
            const questionType = set.question_type === 'mcq' ? 'Multiple Choice' : 'Short Answer';
            const date = new Date(set.created_at).toLocaleDateString();
            
            html += `
                <div class="question-set" data-index="${index}">
                    <div class="question-set-header">
                        <div class="question-set-title">${set.document_name}</div>
                        <div class="question-set-badge">${questionType}</div>
                    </div>
                    <div class="question-set-meta">
                        ${set.questions.length} questions • ${date}
                    </div>
                </div>
            `;
        });
        
        savedQuestionsContainer.innerHTML = html;
        
        // Add event listeners to question sets
        document.querySelectorAll('.question-set').forEach(set => {
            set.addEventListener('click', () => {
                const index = parseInt(set.dataset.index);
                loadSavedQuestionSet(index);
            });
        });
    }
    
    // Load a saved question set
    function loadSavedQuestionSet(index) {
        const set = savedQuestionSets[index];
        if (!set) return;
        
        currentQuestions = set.questions;
        renderQuiz(currentQuestions);
        
        // Update UI
        if (quizInfo) {
            quizInfo.innerHTML = `
                <span class="badge bg-primary">${set.document_name} - ${currentQuestions.length} questions</span>
            `;
        }
        
        if (checkAnswersBtn) checkAnswersBtn.disabled = false;
        if (saveQuestionsBtn) saveQuestionsBtn.disabled = true; // Already saved
    }
    
    // Handle generate questions form submission
    async function handleGenerateQuestions(e) {
        e.preventDefault();
        
        if (!documentSelect || !quizContainer) return;
        
        const documentId = documentSelect.value;
        if (!documentId) {
            showNotification('Please select a document', 'warning');
            return;
        }
        
        // Get form data
        const questionType = document.querySelector('input[name="question_type"]:checked').value;
        const count = parseInt(questionCountInput ? questionCountInput.value : 5);
        
        try {
            // Show loading state
            const submitBtn = generateForm.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
            submitBtn.disabled = true;
            
            // Clear quiz container and show loading
            quizContainer.innerHTML = `
                <div class="loading-indicator">
                    <i class="fas fa-spinner fa-spin"></i> Generating questions...
                </div>
            `;
            
            // Send request
            const response = await fetchAPI(`/api/questions/document/${documentId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    question_type: questionType,
                    count: count
                })
            });
            
            // Process response
            if (response.questions && response.questions.length > 0) {
                currentQuestions = response.questions;
                renderQuiz(currentQuestions);
                
                // Get document name
                const document = documents.find(d => d.id === parseInt(documentId));
                const documentName = document ? document.filename : 'Document';
                
                // Update UI
                if (quizInfo) {
                    quizInfo.innerHTML = `
                        <span class="badge bg-primary">${documentName} - ${currentQuestions.length} questions</span>
                    `;
                }
                
                if (checkAnswersBtn) checkAnswersBtn.disabled = false;
                if (saveQuestionsBtn) saveQuestionsBtn.disabled = false;
                
                showNotification(`Generated ${currentQuestions.length} questions successfully`, 'success');
            } else {
                quizContainer.innerHTML = `
                    <div class="quiz-welcome">
                        <div class="quiz-welcome-icon">
                            <i class="fas fa-exclamation-circle"></i>
                        </div>
                        <h3>Failed to generate questions</h3>
                        <p>Please try again with a different document or settings.</p>
                    </div>
                `;
                
                showNotification('No questions could be generated from this document', 'warning');
            }
        } catch (error) {
            console.error('Error generating questions:', error);
            quizContainer.innerHTML = `
                <div class="quiz-welcome">
                    <div class="quiz-welcome-icon">
                        <i class="fas fa-exclamation-circle"></i>
                    </div>
                    <h3>Error</h3>
                    <p>${error.message || 'Failed to generate questions. Please try again.'}</p>
                </div>
            `;
            
            showNotification(error.message || 'Failed to generate questions', 'danger');
        } finally {
            // Reset button
            const submitBtn = generateForm.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.innerHTML = 'Generate Questions';
                submitBtn.disabled = false;
            }
        }
    }
    
    // Render quiz with questions
    function renderQuiz(questions) {
        if (!quizContainer) return;
        
        if (!questions || questions.length === 0) {
            quizContainer.innerHTML = `
                <div class="quiz-welcome">
                    <div class="quiz-welcome-icon">
                        <i class="fas fa-question-circle"></i>
                    </div>
                    <h3>No questions to display</h3>
                    <p>Generate questions to start the quiz.</p>
                </div>
            `;
            return;
        }
        
        // Remove any existing score display
        const existingScore = document.getElementById('quiz-score-display');
        if (existingScore) existingScore.remove();
        
        let html = '';
        questions.forEach((question, index) => {
            html += `
                <div class="quiz-question ${question.question_type}" data-id="${question.id || index}" ${question.question_type === 'mcq' ? `data-answer="${question.answer}"` : ''}>
                    <h4>${index + 1}. ${question.question}</h4>
            `;
            
            if (question.question_type === 'mcq') {
                // Multiple choice question
                let options = question.options;
                if (typeof options === 'string') {
                    try {
                        options = JSON.parse(options);
                    } catch (e) {
                        console.error('Error parsing options:', e);
                        options = {};
                    }
                }
                
                html += '<div class="option-list">';
                Object.keys(options).forEach(key => {
                    const optionId = `question-${index}-option-${key}`;
                    html += `
                        <div class="option-item">
                            <input type="radio" id="${optionId}" name="question-${index}" value="${key}" class="option-input">
                            <label for="${optionId}">${key}. ${options[key]}</label>
                        </div>
                    `;
                });
                html += '</div>';
                
                // Add hidden result div for feedback
                html += '<div class="question-result mt-3" style="display: none;"></div>';
            } else {
                // Short answer question
                html += `
                    <div class="short-answer">
                        <textarea class="short-answer-input" placeholder="Type your answer here..."></textarea>
                    </div>
                    <div class="question-result mt-3" style="display: none;"></div>
                `;
            }
            
            html += '</div>';
        });
        
        quizContainer.innerHTML = html;
        
        // Add submit button
        addSubmitButton();
    }
    
    // Add submit button to quiz
    function addSubmitButton() {
        if (!quizContainer) return;
        
        // Create button if it doesn't exist
        if (!document.getElementById('submit-quiz-btn')) {
            const submitBtn = document.createElement('button');
            submitBtn.id = 'submit-quiz-btn';
            submitBtn.className = 'btn btn-primary mt-4';
            submitBtn.innerHTML = '<i class="fas fa-check-circle"></i> Submit Answers';
            submitBtn.addEventListener('click', evaluateQuiz);
            
            quizContainer.appendChild(submitBtn);
        }
    }
    
    // Evaluate quiz and display results
    function evaluateQuiz() {
        const questions = document.querySelectorAll('.quiz-question');
        let correctCount = 0;
        let totalQuestions = questions.length;
        
        questions.forEach((question, index) => {
            const questionId = question.dataset.id;
            const resultDiv = question.querySelector('.question-result');
            
            if (question.classList.contains('mcq')) {
                const selectedOption = question.querySelector('input[type="radio"]:checked');
                if (!selectedOption) {
                    resultDiv.innerHTML = '<div class="result-warning">No answer selected</div>';
                    resultDiv.style.display = 'block';
                    return;
                }
                
                const correctAnswer = question.dataset.answer;
                const isCorrect = selectedOption.value === correctAnswer;
                
                if (isCorrect) {
                    resultDiv.innerHTML = '<div class="result-correct"><i class="fas fa-check-circle"></i> Correct!</div>';
                    correctCount++;
                } else {
                    const correctOptionText = question.querySelector(`label[for="question-${index}-option-${correctAnswer}"]`).textContent;
                    resultDiv.innerHTML = `
                        <div class="result-incorrect"><i class="fas fa-times-circle"></i> Incorrect</div>
                        <div class="correct-answer">Correct answer: ${correctOptionText}</div>
                    `;
                }
                resultDiv.style.display = 'block';
            } else {
                // Short answer logic
                const answerInput = question.querySelector('.short-answer-input');
                if (!answerInput || !answerInput.value.trim()) {
                    resultDiv.innerHTML = '<div class="result-warning">No answer provided</div>';
                    resultDiv.style.display = 'block';
                    return;
                }
                
                // This would normally call the API to evaluate the answer
                // For now, we'll use a simplified approach
                const currentQuestion = currentQuestions[index];
                const userAnswer = answerInput.value.trim().toLowerCase();
                const correctAnswer = currentQuestion.answer.toLowerCase();
                
                // Basic similarity check
                const similarity = calculateSimilarity(userAnswer, correctAnswer);
                
                if (similarity > 0.7) {
                    resultDiv.innerHTML = '<div class="result-correct"><i class="fas fa-check-circle"></i> Correct!</div>';
                    correctCount++;
                } else if (similarity > 0.4) {
                    resultDiv.innerHTML = `
                        <div class="result-partial"><i class="fas fa-check-circle"></i> Partially Correct</div>
                        <div class="correct-answer">Correct answer: ${currentQuestion.answer}</div>
                    `;
                    correctCount += 0.5;
                } else {
                    resultDiv.innerHTML = `
                        <div class="result-incorrect"><i class="fas fa-times-circle"></i> Incorrect</div>
                        <div class="correct-answer">Correct answer: ${currentQuestion.answer}</div>
                    `;
                }
                resultDiv.style.display = 'block';
            }
        });
        
        // Display final score
        displayScore(correctCount, totalQuestions);
        
        // Disable the submit button
        const submitBtn = document.getElementById('submit-quiz-btn');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-check-double"></i> Quiz Submitted';
        }
    }
    
    // Calculate similarity between two strings (for short answer evaluation)
    function calculateSimilarity(str1, str2) {
        const words1 = str1.toLowerCase().split(/\s+/);
        const words2 = str2.toLowerCase().split(/\s+/);
        
        const intersection = words1.filter(word => words2.includes(word));
        return intersection.length / Math.max(words1.length, words2.length);
    }
    
    // Display the final score
    function displayScore(correct, total) {
        const scorePercentage = Math.round((correct / total) * 100);
        const scoreMessage = `<div class="quiz-score">
            <h4>Your Score: ${correct}/${total} (${scorePercentage}%)</h4>
            <p>${getScoreMessage(scorePercentage)}</p>
        </div>`;
        
        // Create or update score element
        let scoreElement = document.getElementById('quiz-score-display');
        if (!scoreElement) {
            scoreElement = document.createElement('div');
            scoreElement.id = 'quiz-score-display';
            quizContainer.insertBefore(scoreElement, quizContainer.firstChild);
        }
        
        scoreElement.innerHTML = scoreMessage;
        scoreElement.scrollIntoView({ behavior: 'smooth' });
    }
    
    // Get appropriate message based on score
    function getScoreMessage(percentage) {
        if (percentage >= 90) return "Excellent! You've mastered this material.";
        if (percentage >= 75) return "Good job! You have a solid understanding.";
        if (percentage >= 60) return "Not bad. You're on the right track.";
        return "Keep studying. You'll improve with practice.";
    }
    
    // Check answers (original method, now redirects to evaluateQuiz)
    async function checkAnswers() {
        evaluateQuiz();
    }
    
    // Save current questions
    async function saveCurrentQuestions() {
        // Questions are already saved on the server when generated
        // This button just provides visual feedback
        if (saveQuestionsBtn) {
            saveQuestionsBtn.disabled = true;
        }
        showNotification('Questions saved successfully', 'success');
        
        // Refresh saved questions list
        await loadSavedQuestions();
    }
    
    // Helper function to make API calls
    async function fetchAPI(url, options = {}) {
        try {
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
        } catch (error) {
            console.error('Fetch error:', error);
            throw error;
        }
    }
    
    // Helper function to show notifications
    function showNotification(message, type = 'info', duration = 5000) {
        console.log(`${type}: ${message}`); // Fallback if notification system not available
        
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
                if (notification.parentNode) {
                    notification.remove();
                }
                
                // Remove container if empty
                if (notificationsContainer.children.length === 0) {
                    notificationsContainer.remove();
                }
            }, 300);
        });
        
        // Auto dismiss after duration
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
});