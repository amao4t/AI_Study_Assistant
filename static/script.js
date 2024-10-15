document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const uploadForm = document.getElementById('upload-form');
    const loader = document.getElementById('loader');
    const summaryResult = document.getElementById('summary-result');
    const quizButton = document.getElementById('quiz-btn');  // Updated from quizButton to quiz-btn
    const quizModal = document.getElementById('quiz-modal');
    const summaryContent = document.getElementById('summary-content');
    const quizQuestions = document.getElementById('quiz-questions');
    const closeModal = document.querySelector('.close');

    // Upload form submission
    if (uploadForm) {
        uploadForm.addEventListener('submit', function(event) {
            event.preventDefault();

            const formData = new FormData(uploadForm);

            loader.style.display = 'block';
            summaryResult.style.display = 'none';
            quizButton.style.display = 'none';

            fetch(uploadForm.action, {
                method: 'POST',
                body: formData,
            })
            .then(response => response.json())
            .then(data => {
                loader.style.display = 'none';
                if (data.error) {
                    alert(data.error);
                } else {
                    summaryContent.textContent = data.summary;
                    summaryResult.style.display = 'block';
                    quizButton.style.display = 'block';  // Show "Do Quiz" button
                    
                    // Store questions in hidden quiz container for later
                    const questionsArray = data.questions.split('\n');  // Assuming questions are separated by newlines
                    quizQuestions.innerHTML = ''; // Clear previous questions
                    questionsArray.forEach((question, index) => {
                        if (index < 10) {  // Only take 10 questions
                            quizQuestions.innerHTML += `<li>${question}</li>`;
                        }
                    });
                }
            })
            .catch(error => {
                loader.style.display = 'none';
                alert('An error occurred while processing your document. Please try again.');
            });
        });
    }

    // Handle Quiz Button Click
    if (quizButton) {
        quizButton.addEventListener('click', function() {
            quizModal.style.display = 'block';  // Show modal
        });
    }

    // Close modal when the close button is clicked
    if (closeModal) {
        closeModal.addEventListener('click', function() {
            quizModal.style.display = 'none';
        });
    }

    // Close modal when clicking outside the modal content
    window.addEventListener('click', function(event) {
        if (event.target == quizModal) {
            quizModal.style.display = 'none';
        }
    });

    // Menu toggle for mobile view
    document.getElementById('hamburger-menu').addEventListener('click', toggleMenu);

    // Navigation link clicks
    const navLinks = document.querySelectorAll('#navbar-links a');
    navLinks.forEach(link => {
        link.addEventListener('click', function() {
            const sectionId = this.getAttribute('href').substring(1);
            showSection(sectionId);
        });
    });

    // Toggle menu function
    function toggleMenu() {
        const navbarLinks = document.getElementById('navbar-links');
        navbarLinks.classList.toggle('show');
    }

    // Show specific section function
    function showSection(sectionId) {
        const sections = document.querySelectorAll('.content-section');
        sections.forEach(section => {
            section.style.display = 'none';
        });
        const selectedSection = document.getElementById(sectionId);
        if (selectedSection) {
            selectedSection.style.display = 'block';
        }
    }

    // Handle Start button click function
    function handleStartButtonClick() {
        if (loggedIn) {
            showSection('features-upload');
        } else {
            showSection('login-signup');
        }
    }

    // Make functions globally accessible for HTML event handlers
    window.showSection = showSection;
    window.handleStartButtonClick = handleStartButtonClick;
    window.toggleSignUp = function() {
        const signupForm = document.getElementById('signup-form');
        signupForm.style.display = signupForm.style.display === 'none' ? 'block' : 'none';
    };
});
