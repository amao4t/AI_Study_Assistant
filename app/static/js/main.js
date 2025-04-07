document.addEventListener('DOMContentLoaded', function() {
    // Initialize functionality when DOM is loaded
    initThemeToggle();
    initMobileMenu();
    initAlertDismiss();
    initFormValidation();
    initFetchAPI();
});

/**
 * Theme Toggle Functionality
 */
function initThemeToggle() {
    const themeToggleBtn = document.getElementById('theme-toggle-btn');
    const themeIcon = document.getElementById('theme-icon');
    
    // Check if user has previously set a theme preference
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        document.documentElement.setAttribute('data-theme', savedTheme);
        updateThemeIcon(savedTheme);
    }
    
    // Toggle theme on button click
    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', () => {
            const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            
            // Apply the new theme
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            
            // Update the icon
            updateThemeIcon(newTheme);
        });
    }
    
    function updateThemeIcon(theme) {
        if (themeIcon) {
            if (theme === 'dark') {
                themeIcon.classList.remove('fa-moon');
                themeIcon.classList.add('fa-sun');
            } else {
                themeIcon.classList.remove('fa-sun');
                themeIcon.classList.add('fa-moon');
            }
        }
    }
}

/**
 * Mobile Menu Functionality
 */
function initMobileMenu() {
    const menuToggle = document.getElementById('mobile-menu-toggle');
    const navLinks = document.getElementById('nav-links');
    
    if (menuToggle && navLinks) {
        menuToggle.addEventListener('click', () => {
            navLinks.classList.toggle('active');
            
            // Toggle icon between bars and X
            const icon = menuToggle.querySelector('i');
            if (icon.classList.contains('fa-bars')) {
                icon.classList.remove('fa-bars');
                icon.classList.add('fa-times');
            } else {
                icon.classList.remove('fa-times');
                icon.classList.add('fa-bars');
            }
        });
        
        // Close menu when clicking outside
        document.addEventListener('click', (event) => {
            if (!event.target.closest('.main-nav') && navLinks.classList.contains('active')) {
                navLinks.classList.remove('active');
                const icon = menuToggle.querySelector('i');
                icon.classList.remove('fa-times');
                icon.classList.add('fa-bars');
            }
        });
    }
}

/**
 * Alert Dismissal
 */
function initAlertDismiss() {
    document.querySelectorAll('.alert-close').forEach(button => {
        button.addEventListener('click', () => {
            const alert = button.closest('.alert');
            
            // Add fade-out animation
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-10px)';
            
            // Remove after animation completes
            setTimeout(() => {
                alert.remove();
            }, 300);
        });
    });
}

/**
 * Form Validation
 */
function initFormValidation() {
    // Get all forms with validation
    const forms = document.querySelectorAll('form.needs-validation');
    
    forms.forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            // Add validation classes
            form.classList.add('was-validated');
            
            // Highlight invalid fields
            form.querySelectorAll(':invalid').forEach(input => {
                input.classList.add('is-invalid');
                
                // Find the closest form-group and add the feedback
                const formGroup = input.closest('.form-group');
                if (formGroup) {
                    const feedback = formGroup.querySelector('.invalid-feedback');
                    if (!feedback) {
                        const newFeedback = document.createElement('div');
                        newFeedback.className = 'invalid-feedback';
                        newFeedback.textContent = input.validationMessage;
                        formGroup.appendChild(newFeedback);
                    }
                }
            });
        }, false);
        
        // Remove invalid class when input changes
        form.querySelectorAll('input, select, textarea').forEach(input => {
            input.addEventListener('input', () => {
                if (input.checkValidity()) {
                    input.classList.remove('is-invalid');
                    
                    // Find and remove feedback if it exists
                    const formGroup = input.closest('.form-group');
                    if (formGroup) {
                        const feedback = formGroup.querySelector('.invalid-feedback');
                        if (feedback) {
                            feedback.remove();
                        }
                    }
                }
            });
        });
    });
}

/**
 * Fetch API for AJAX requests
 */
function initFetchAPI() {
    // Common fetch function with error handling
    window.fetchAPI = async function(url, options = {}) {
        // Set default options
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            credentials: 'same-origin'
        };
        
        // Merge options
        const fetchOptions = { ...defaultOptions, ...options };
        
        // Add CSRF token if available (for POST, PUT, DELETE requests)
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
        if (csrfToken && ['POST', 'PUT', 'DELETE'].includes(fetchOptions.method)) {
            fetchOptions.headers['X-CSRFToken'] = csrfToken;
        }
        
        try {
            const response = await fetch(url, fetchOptions);
            
            // Check if response is JSON
            const contentType = response.headers.get('content-type');
            const isJson = contentType && contentType.includes('application/json');
            
            // Parse response
            const data = isJson ? await response.json() : await response.text();
            
            // Check for error status
            if (!response.ok) {
                // Create error object with response details
                const error = new Error(isJson && data.error ? data.error : 'Network response was not ok');
                error.status = response.status;
                error.response = response;
                error.data = data;
                throw error;
            }
            
            return data;
        } catch (error) {
            // Display error message
            showNotification(error.message || 'An error occurred', 'danger');
            console.error('Fetch Error:', error);
            throw error;
        }
    };
}

/**
 * Show notification
 * @param {string} message - Notification message
 * @param {string} type - Notification type (success, warning, danger, info)
 * @param {number} duration - Duration in milliseconds before auto-dismiss
 */
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
        
        // Add styles for notifications container
        const style = document.createElement('style');
        style.textContent = `
            .notifications-container {
                position: fixed;
                top: 20px;
                right: 20px;
                max-width: 400px;
                z-index: 9999;
            }
            
            .notifications-container .alert {
                margin-bottom: 10px;
                animation: slideIn 0.3s ease forwards;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            
            @keyframes slideIn {
                from {
                    opacity: 0;
                    transform: translateX(50px);
                }
                to {
                    opacity: 1;
                    transform: translateX(0);
                }
            }
            
            @keyframes slideOut {
                from {
                    opacity: 1;
                    transform: translateX(0);
                }
                to {
                    opacity: 0;
                    transform: translateX(50px);
                }
            }
        `;
        document.head.appendChild(style);
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