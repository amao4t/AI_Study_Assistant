// Complete questions.js file with improved quiz functionality

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
            const questionType = getQuestionTypeDisplay(set.question_type);
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
    
    // Get display name for question type
    function getQuestionTypeDisplay(type) {
        switch(type) {
            case 'mcq': return 'Multiple Choice';
            case 'qa': return 'Short Answer';
            case 'true_false': return 'True/False';
            case 'fill_in_blank': return 'Fill-in-the-blank';
            default: return 'Unknown';
        }
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
                submitBtn.innerHTML = originalText;
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
                    <h3>Generate questions to start</h3>
                    <p>Select a document and generate questions to test your knowledge.</p>
                </div>
            `;
            return;
        }
        
        // Remove any existing score display
        const existingScore = document.getElementById('quiz-score-display');
        if (existingScore) existingScore.remove();
        
        let html = '';
        questions.forEach((question, index) => {
            const questionType = question.question_type || 'qa';
            
            html += `
                <div class="quiz-question ${questionType}" data-id="${question.id || index}">
                    <h4>${index + 1}. ${question.question}</h4>
            `;
            
            // Render different question types
            if (questionType === 'mcq') {
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
                
            } else if (questionType === 'true_false') {
                // True/False question
                html += `
                    <div class="option-list">
                        <div class="option-item">
                            <input type="radio" id="question-${index}-true" name="question-${index}" value="True" class="option-input">
                            <label for="question-${index}-true">True</label>
                        </div>
                        <div class="option-item">
                            <input type="radio" id="question-${index}-false" name="question-${index}" value="False" class="option-input">
                            <label for="question-${index}-false">False</label>
                        </div>
                    </div>
                `;
                
            } else if (questionType === 'fill_in_blank') {
                // Fill-in-the-blank question
                html += `
                    <div class="fill-in-blank">
                        <input type="text" class="form-control fill-blank-input" placeholder="Your answer...">
                    </div>
                `;
                
                if (question.explanation) {
                    html += `<div class="explanation" style="display: none;">${question.explanation}</div>`;
                }
                
            } else {
                // Short answer question (qa)
                html += `
                    <div class="short-answer">
                        <textarea class="short-answer-input" placeholder="Type your answer here..."></textarea>
                    </div>
                `;
            }
            
            // Add hidden result div for feedback
            html += '<div class="question-result mt-3" style="display: none;"></div>';
            html += '</div>'; // close quiz-question div
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
    async function evaluateQuiz() {
        const questions = document.querySelectorAll('.quiz-question');
        let correctCount = 0;
        let totalQuestions = questions.length;
        let evaluatedCount = 0;
        let pendingEvaluations = [];
        
        // Process each question
        questions.forEach((question, index) => {
            const questionId = question.dataset.id;
            const resultDiv = question.querySelector('.question-result');
            const questionType = question.classList.contains('mcq') ? 'mcq' : 
                                question.classList.contains('true_false') ? 'true_false' :
                                question.classList.contains('fill_in_blank') ? 'fill_in_blank' : 'qa';
            
            // Handle MCQ and True/False (client-side evaluation)
            if (questionType === 'mcq' || questionType === 'true_false') {
                const selectedOption = question.querySelector('input[type="radio"]:checked');
                if (!selectedOption) {
                    resultDiv.innerHTML = '<div class="result-warning">No answer selected</div>';
                    resultDiv.style.display = 'block';
                    evaluatedCount++;
                    return;
                }
                
                // Get current question data
                const currentQuestion = currentQuestions[index];
                const correctAnswer = currentQuestion.answer;
                
                // Verify answer
                const isCorrect = selectedOption.value === correctAnswer;
                
                if (isCorrect) {
                    resultDiv.innerHTML = '<div class="result-correct"><i class="fas fa-check-circle"></i> Correct!</div>';
                    correctCount++;
                } else {
                    let correctOptionText;
                    if (questionType === 'mcq') {
                        correctOptionText = currentQuestion.options[correctAnswer];
                        resultDiv.innerHTML = `
                            <div class="result-incorrect"><i class="fas fa-times-circle"></i> Incorrect</div>
                            <div class="correct-answer">Correct answer: ${correctAnswer}. ${correctOptionText}</div>
                        `;
                    } else {
                        resultDiv.innerHTML = `
                            <div class="result-incorrect"><i class="fas fa-times-circle"></i> Incorrect</div>
                            <div class="correct-answer">Correct answer: ${correctAnswer}</div>
                        `;
                    }
                }
                resultDiv.style.display = 'block';
                evaluatedCount++;
                
            } else if (questionType === 'fill_in_blank') {
                const answerInput = question.querySelector('.fill-blank-input');
                if (!answerInput || !answerInput.value.trim()) {
                    resultDiv.innerHTML = '<div class="result-warning">No answer provided</div>';
                    resultDiv.style.display = 'block';
                    evaluatedCount++;
                    return;
                }
                
                // Get current question data
                const currentQuestion = currentQuestions[index];
                const userAnswer = answerInput.value.trim();
                
                // Add to pending evaluations
                pendingEvaluations.push({
                    questionElement: question,
                    resultDiv: resultDiv,
                    questionData: currentQuestion,
                    userAnswer: userAnswer,
                    index: index
                });
                
            } else {
                // Short answer (QA) evaluation
                const answerInput = question.querySelector('.short-answer-input');
                if (!answerInput || !answerInput.value.trim()) {
                    resultDiv.innerHTML = '<div class="result-warning">No answer provided</div>';
                    resultDiv.style.display = 'block';
                    evaluatedCount++;
                    return;
                }
                
                // Get current question data
                const currentQuestion = currentQuestions[index];
                const userAnswer = answerInput.value.trim();
                
                // Add to pending evaluations
                pendingEvaluations.push({
                    questionElement: question,
                    resultDiv: resultDiv,
                    questionData: currentQuestion,
                    userAnswer: userAnswer,
                    index: index
                });
            }
        });
        
        // Process server-side evaluations
        if (pendingEvaluations.length > 0) {
            // Disable submit button while processing
            const submitBtn = document.getElementById('submit-quiz-btn');
            if (submitBtn) {
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Evaluating...';
                submitBtn.disabled = true;
            }
            
            // Process each evaluation sequentially to avoid overwhelming the server
            for (const evaluation of pendingEvaluations) {
                try {
                    const result = await evaluateAnswer(
                        evaluation.questionData.id, 
                        evaluation.userAnswer,
                        evaluation.questionData.question_type
                    );
                    
                    // Process result
                    if (result) {
                        if (result.is_correct) {
                            evaluation.resultDiv.innerHTML = '<div class="result-correct"><i class="fas fa-check-circle"></i> Correct!</div>';
                            correctCount++;
                        } else if (result.score && result.score > 0.5) {
                            // Partial credit for similarity > 0.5
                            evaluation.resultDiv.innerHTML = `
                                <div class="result-partial"><i class="fas fa-check-circle"></i> Partially Correct (${Math.round(result.score * 100)}%)</div>
                                <div class="correct-answer">Correct answer: ${result.correct_answer}</div>
                            `;
                            correctCount += result.score;
                        } else {
                            evaluation.resultDiv.innerHTML = `
                                <div class="result-incorrect"><i class="fas fa-times-circle"></i> Incorrect</div>
                                <div class="correct-answer">Correct answer: ${result.correct_answer}</div>
                            `;
                        }
                        
                        evaluation.resultDiv.style.display = 'block';
                        
                        // Show explanation if available for fill-in-blank
                        if (evaluation.questionData.question_type === 'fill_in_blank') {
                            const explanation = evaluation.questionElement.querySelector('.explanation');
                            if (explanation) {
                                explanation.style.display = 'block';
                                explanation.classList.add('mt-2');
                                explanation.innerHTML = `<strong>Explanation:</strong> ${explanation.innerHTML}`;
                            }
                        }
                    }
                } catch (error) {
                    console.error('Error evaluating answer:', error);
                    evaluation.resultDiv.innerHTML = `
                        <div class="result-warning">Error evaluating answer</div>
                    `;
                    evaluation.resultDiv.style.display = 'block';
                }
                
                evaluatedCount++;
            }
            
            // Re-enable submit button
            if (submitBtn) {
                submitBtn.innerHTML = '<i class="fas fa-check-circle"></i> Submit Answers';
                submitBtn.disabled = true; // Keep disabled after submission
            }
        }
        
        // Only display score when all questions are evaluated
        if (evaluatedCount === totalQuestions) {
            // Display final score
            displayScore(correctCount, totalQuestions);
            
            // Disable the submit button
            const submitBtn = document.getElementById('submit-quiz-btn');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fas fa-check-double"></i> Quiz Submitted';
            }
        }
    }
    
    // Evaluate answer with server API
    async function evaluateAnswer(questionId, userAnswer, questionType) {
        if (!questionId) return null;
        
        try {
            const response = await fetchAPI(`/api/questions/${questionId}/evaluate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    answer: userAnswer
                })
            });
            
            return response;
        } catch (error) {
            console.error('Error evaluating answer:', error);
            return null;
        }
    }
    
    // Display the final score
    function displayScore(correct, total) {
        const scorePercentage = Math.round((correct / total) * 100);
        const scoreMessage = `<div class="quiz-score">
            <h4>Your Score: ${correct.toFixed(1)}/${total} (${scorePercentage}%)</h4>
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
    function checkAnswers() {
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