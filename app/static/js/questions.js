// Complete questions.js file with improved quiz functionality

document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const generateForm = document.getElementById('generate-form');
    const documentSelect = document.getElementById('document-select');
    const difficultyCheckboxes = document.querySelectorAll('input[name="difficulty[]"]');
    const savedQuestionsContainer = document.getElementById('saved-questions');
    const quizContainer = document.getElementById('quiz-container');
    const quizInfo = document.getElementById('quiz-info');
    const checkAnswersBtn = document.getElementById('check-answers-btn');
    const saveQuestionsBtn = document.getElementById('save-questions-btn');
    const clearHistoryBtn = document.getElementById('clear-history-btn');
    
    // Add study stats section before the dashboard content
    const dashboardContent = document.querySelector('.dashboard-content');
    if (dashboardContent) {
        const statsSection = document.createElement('div');
        statsSection.className = 'study-stats';
        statsSection.innerHTML = `
            <div class="stat-card">
                <div class="stat-card-value" id="total-questions-stat">0</div>
                <div class="stat-card-label">Total Questions</div>
            </div>
            <div class="stat-card">
                <div class="stat-card-value" id="questions-due-stat">0</div>
                <div class="stat-card-label">Due for Review</div>
            </div>
            <div class="stat-card">
                <div class="stat-card-value" id="success-rate-stat">0%</div>
                <div class="stat-card-label">Success Rate</div>
            </div>
            <div class="stat-card">
                <div class="stat-card-value" id="documents-with-questions-stat">0</div>
                <div class="stat-card-label">Documents with Questions</div>
            </div>
        `;
        dashboardContent.insertBefore(statsSection, dashboardContent.firstChild);
    }
    
    // State
    let documents = [];
    let currentQuestions = [];
    let savedQuestionSets = [];
    let studyStats = {
        totalQuestions: 0,
        questionsDue: 0,
        successRate: 0,
        documentsWithQuestions: 0
    };
    
    // Initialize
    loadDocuments();
    loadSavedQuestions();
    loadStudyStatistics();
    
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
    
    if (clearHistoryBtn) {
        // Remove old handler if exists
        clearHistoryBtn.removeEventListener('click', clearQuizHistory);
        // Add new handler with logging 
        clearHistoryBtn.addEventListener('click', function(e) {
            console.log("Clear history button clicked");
            clearQuizHistory();
        });
        console.log("Clear history button event listener added");
    } else {
        console.log("Clear history button not found in the DOM", document.getElementById('clear-history-btn'));
    }
    
    // Load study statistics
    async function loadStudyStatistics() {
        try {
            // Get all questions for statistics
            const response = await fetchAPI('/api/questions/');
            const questions = response.questions || [];
            
            // Calculate statistics
            studyStats.totalQuestions = questions.length;
            
            // Get due questions
            const dueResponse = await fetchAPI('/api/questions/due-for-review?limit=1000');
            studyStats.questionsDue = (dueResponse.questions || []).length;
            
            // Calculate success rate
            let totalAnswered = 0;
            let totalCorrect = 0;
            
            questions.forEach(question => {
                if (question.times_answered > 0) {
                    totalAnswered += question.times_answered;
                    totalCorrect += question.times_correct;
                }
            });
            
            studyStats.successRate = totalAnswered > 0 
                ? Math.round((totalCorrect / totalAnswered) * 100) 
                : 0;
            
            // Count unique documents with questions
            const documentIds = new Set();
            questions.forEach(question => {
                if (question.document_id) {
                    documentIds.add(question.document_id);
                }
            });
            
            studyStats.documentsWithQuestions = documentIds.size;
            
            // Update stats display
            updateStatsDisplay();
            
        } catch (error) {
            console.error('Error loading study statistics:', error);
        }
    }
    
    // Update stats display
    function updateStatsDisplay() {
        document.getElementById('total-questions-stat').textContent = studyStats.totalQuestions;
        document.getElementById('questions-due-stat').textContent = studyStats.questionsDue;
        document.getElementById('success-rate-stat').textContent = `${studyStats.successRate}%`;
        document.getElementById('documents-with-questions-stat').textContent = studyStats.documentsWithQuestions;
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
            // Get ALL saved questions instead of just those due for review
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
            
            // Sort by most recently created
            savedQuestionSets.sort((a, b) => {
                return new Date(b.created_at) - new Date(a.created_at);
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
            savedQuestionsContainer.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">
                        <i class="fas fa-folder-open"></i>
                    </div>
                    <p>No saved questions found</p>
                </div>
            `;
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
        
        // Get selected difficulty levels
        const selectedDifficulties = [];
        document.querySelectorAll('input[name="difficulty[]"]:checked').forEach(checkbox => {
            selectedDifficulties.push(checkbox.value);
        });
        
        if (selectedDifficulties.length === 0) {
            showNotification('Please select at least one difficulty level', 'warning');
            return;
        }
        
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
            
            // Use the same endpoint for backward compatibility
            const response = await fetchAPI(`/api/questions/document/${documentId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    question_type: questionType,
                    difficulty_levels: selectedDifficulties
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
        
        // Progress indicator
        let progress = `
            <div class="progress-indicator">
                <div class="progress-bar" style="width: 0%"></div>
            </div>
        `;
        
        // Remove any existing score display
        const existingScore = document.getElementById('quiz-score-display');
        if (existingScore) existingScore.remove();
        
        let html = progress;
        questions.forEach((question, index) => {
            const questionType = question.question_type || 'mcq';
            const difficulty = question.difficulty || 'medium';
            const difficultyClass = `difficulty-${difficulty.toLowerCase()}`;
            const questionText = question.question_text || question.question;
            
            html += `
                <div class="quiz-question ${questionType}" data-id="${question.id || index}">
                    <h4>
                        ${index + 1}. ${questionText}
                        <span class="question-difficulty ${difficultyClass}">${difficulty}</span>
                    </h4>
            `;
            
            // Add SRS information if available
            if (question.times_answered > 0) {
                const successRate = Math.round((question.times_correct / question.times_answered) * 100);
                const nextReview = question.next_review ? new Date(question.next_review).toLocaleDateString() : 'Not set';
                
                html += `
                    <div class="spaced-repetition-info">
                        <div class="review-stats">
                            <div class="review-stat">
                                <div class="stat-value">${question.times_answered}</div>
                                <div class="stat-label">Times Answered</div>
                            </div>
                            <div class="review-stat">
                                <div class="stat-value">${successRate}%</div>
                                <div class="stat-label">Success Rate</div>
                            </div>
                            <div class="review-stat">
                                <div class="stat-value">${nextReview}</div>
                                <div class="stat-label">Next Review</div>
                            </div>
                        </div>
                    </div>
                `;
            }
            
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
        
        // Disable submit button during evaluation
        const submitBtn = document.getElementById('submit-quiz-btn');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Checking...';
        }
        
        // Process each question
        questions.forEach((question, index) => {
            const questionId = question.dataset.id;
            const resultDiv = question.querySelector('.question-result');
            const questionType = question.classList.contains('mcq') ? 'mcq' : 
                                question.classList.contains('true_false') ? 'true_false' :
                                question.classList.contains('fill_in_blank') ? 'fill_in_blank' : 'mcq';
            
            // Handle MCQ and True/False (client-side evaluation)
            if (questionType === 'mcq' || questionType === 'true_false') {
                const selectedOption = question.querySelector('input[type="radio"]:checked');
                if (!selectedOption) {
                    resultDiv.innerHTML = '<div class="result-warning">No answer selected</div>';
                    resultDiv.style.display = 'block';
                    evaluatedCount++;
                    updateProgressBar(evaluatedCount, totalQuestions);
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
                updateProgressBar(evaluatedCount, totalQuestions);
                
                // Add animation effect for feedback
                question.classList.add(isCorrect ? 'correct-highlight' : 'incorrect-highlight');
                setTimeout(() => {
                    question.classList.remove('correct-highlight', 'incorrect-highlight');
                }, 1000);
                
                // Submit for SRS tracking
                pendingEvaluations.push(
                    evaluateAnswer(questionId, selectedOption.value, questionType)
                );
                
            } else if (questionType === 'fill_in_blank') {
                const answerInput = question.querySelector('.fill-blank-input');
                if (!answerInput || !answerInput.value.trim()) {
                    resultDiv.innerHTML = '<div class="result-warning">No answer provided</div>';
                    resultDiv.style.display = 'block';
                    evaluatedCount++;
                    updateProgressBar(evaluatedCount, totalQuestions);
                    return;
                }
                
                // Get current question data
                const currentQuestion = currentQuestions[index];
                const correctAnswer = currentQuestion.answer;
                const userAnswer = answerInput.value.trim();
                
                // Basic verification (case-insensitive match)
                const isCorrect = userAnswer.toLowerCase() === correctAnswer.toLowerCase();
                
                if (isCorrect) {
                    resultDiv.innerHTML = '<div class="result-correct"><i class="fas fa-check-circle"></i> Correct!</div>';
                    correctCount++;
                } else {
                    resultDiv.innerHTML = `
                        <div class="result-incorrect"><i class="fas fa-times-circle"></i> Incorrect</div>
                        <div class="correct-answer">Correct answer: ${correctAnswer}</div>
                    `;
                }
                resultDiv.style.display = 'block';
                evaluatedCount++;
                updateProgressBar(evaluatedCount, totalQuestions);
                
                // Add animation effect for feedback
                question.classList.add(isCorrect ? 'correct-highlight' : 'incorrect-highlight');
                setTimeout(() => {
                    question.classList.remove('correct-highlight', 'incorrect-highlight');
                }, 1000);
                
                // Submit for SRS tracking
                pendingEvaluations.push(
                    evaluateAnswer(questionId, userAnswer, questionType)
                );
            }
        });
        
        // Wait for all evaluations to complete
        Promise.all(pendingEvaluations).then(() => {
            // Display score
            displayScore(correctCount, totalQuestions);
            
            // Reload saved questions to update SRS info
            loadSavedQuestions();
            
            // Reload stats
            loadStudyStatistics();
            
            // Re-enable submit button
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="fas fa-check-circle"></i> Submit Answers';
                
                // Change button to "Retry Quiz" if already submitted
                submitBtn.textContent = 'Retry Quiz';
                submitBtn.addEventListener('click', () => {
                    // Reload the current questions
                    renderQuiz(currentQuestions);
                }, { once: true });
            }
        });
    }
    
    // Update progress bar
    function updateProgressBar(current, total) {
        const progressBar = document.querySelector('.progress-bar');
        if (progressBar) {
            const percent = Math.round((current / total) * 100);
            progressBar.style.width = `${percent}%`;
        }
    }
    
    // Evaluate a single answer
    async function evaluateAnswer(questionId, userAnswer, questionType) {
        try {
            // Use the new evaluate endpoint
            const response = await fetchAPI(`/api/questions/evaluate/${questionId}`, {
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
            return { 
                is_correct: false,
                error: 'Failed to evaluate answer' 
            };
        }
    }
    
    // Display the final score with study recommendations
    function displayScore(correct, total) {
        const scorePercentage = Math.round((correct / total) * 100);
        
        // Get study recommendations based on score
        const recommendations = getStudyRecommendations(scorePercentage, currentQuestions);
        
        const scoreMessage = `
            <div class="quiz-score">
                <h4>Your Score: ${correct.toFixed(1)}/${total} (${scorePercentage}%)</h4>
                <p>${getScoreMessage(scorePercentage)}</p>
            </div>
            <div class="study-recommendations">
                <h5>Study Recommendations</h5>
                <div class="recommendations-list">
                    ${recommendations.map(rec => `
                        <div class="recommendation-item">
                            <i class="fas fa-lightbulb"></i>
                            <span>${rec}</span>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
        
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
    
    // Generate study recommendations based on quiz performance
    function getStudyRecommendations(scorePercentage, questions) {
        const recommendations = [];
        
        // Basic recommendations based on overall score
        if (scorePercentage < 60) {
            recommendations.push("Review the entire document thoroughly before attempting the quiz again.");
            recommendations.push("Try creating flashcards for key concepts in the document.");
        } else if (scorePercentage < 80) {
            recommendations.push("Focus on topics where you made mistakes in this quiz.");
            recommendations.push("Consider using the spaced repetition feature for better retention.");
        } else {
            recommendations.push("Great job! Try increasing the difficulty level in your next quiz.");
            recommendations.push("Challenge yourself with concepts that build upon what you've mastered.");
        }
        
        // Analyze incorrect answers to provide more specific recommendations
        const incorrectQuestions = [];
        const difficultyStats = { easy: 0, medium: 0, hard: 0 };
        
        // Find questions where answers were checked (look for visible .question-result)
        const answeredQuestions = document.querySelectorAll('.quiz-question');
        answeredQuestions.forEach((questionElement, index) => {
            const resultDiv = questionElement.querySelector('.question-result');
            if (resultDiv && resultDiv.style.display !== 'none') {
                // Check if incorrect
                if (resultDiv.querySelector('.result-incorrect')) {
                    const question = questions[index];
                    incorrectQuestions.push(question);
                    
                    // Track difficulty stats
                    const difficulty = question.difficulty || 'medium';
                    difficultyStats[difficulty]++;
                }
            }
        });
        
        // Add recommendations based on difficulty patterns
        if (difficultyStats.hard > 0 && difficultyStats.hard > difficultyStats.medium) {
            recommendations.push("You're struggling with difficult concepts. Focus on understanding fundamentals first.");
        }
        
        if (difficultyStats.easy > 0 && incorrectQuestions.length > 0) {
            recommendations.push("Review basic concepts - you missed some easier questions that are important for understanding.");
        }
        
        // Add recommendation about reviewing soon
        recommendations.push("For optimal learning, review these questions again in 1-2 days.");
        
        return recommendations;
    }
    
    // Check answers (original method, now redirects to evaluateQuiz)
    function checkAnswers() {
        evaluateQuiz();
    }
    
    // Save current questions
    async function saveCurrentQuestions() {
        try {
            // Show saving indicator
            const originalText = saveQuestionsBtn.innerHTML;
            saveQuestionsBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
            saveQuestionsBtn.disabled = true;
            
            // Make explicit save call to backend to ensure questions are properly saved
            // Even though questions are created when generated, this ensures they stay in the database
            const saveResponse = await fetchAPI('/api/questions/save', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    question_ids: currentQuestions.map(q => q.id)
                })
            });
            
            if (saveResponse.success) {
                showNotification('Questions saved successfully', 'success');
                
                // Refresh saved questions list
                await loadSavedQuestions();
                
                // Reset button
                saveQuestionsBtn.innerHTML = '<i class="fas fa-check-circle"></i> Saved';
                saveQuestionsBtn.disabled = true; // Disable after saving
            } else {
                throw new Error('Failed to save questions');
            }
        } catch (error) {
            console.error('Error saving questions:', error);
            showNotification('Failed to save questions: ' + error.message, 'danger');
            saveQuestionsBtn.innerHTML = originalText;
            saveQuestionsBtn.disabled = false;
        }
    }
    
    // Helper function to make API calls
    async function fetchAPI(url, options = {}) {
        console.log(`Fetching API: ${url}`, options);
        
        try {
            const response = await fetch(url, {
                ...options,
                credentials: 'same-origin'
            });
            
            console.log(`API response status: ${response.status}`);
            
            if (!response.ok) {
                const text = await response.text();
                console.error(`API error response: ${text}`);
                
                try {
                    const json = JSON.parse(text);
                    throw new Error(json.error || `API Error: ${response.status}`);
                } catch (parseError) {
                    console.error("Could not parse error response as JSON:", parseError);
                    throw new Error(`API Error: ${response.status} - ${text.substring(0, 100)}`);
                }
            }
            
            const data = await response.json();
            console.log(`API response data:`, data);
            return data;
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
    
    // Function to clear quiz history
    async function clearQuizHistory() {
        console.log("clearQuizHistory function called");
        
        if (!confirm('Are you sure you want to clear all quiz history? This cannot be undone.')) {
            console.log("User cancelled the operation");
            return;
        }
        
        try {
            console.log("Sending request to clear quiz history");
            
            const response = await fetchAPI('/api/questions/clear-history', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            console.log("Response received:", response);
            
            if (response.success) {
                showNotification('Quiz history cleared successfully', 'success');
                // Reload saved questions (should be empty)
                savedQuestionSets = [];
                renderSavedQuestions();
                // Reload stats
                loadStudyStatistics();
                
                console.log("Quiz history cleared successfully");
            } else {
                console.error("Failed to clear quiz history, API returned false success");
                showNotification('Failed to clear quiz history', 'danger');
            }
        } catch (error) {
            console.error('Error clearing quiz history:', error);
            showNotification('Failed to clear quiz history: ' + error.message, 'danger');
        }
    }
});