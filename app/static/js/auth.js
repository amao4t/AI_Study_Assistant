/**
 * Authentication functionality
 */

// Password match validation for registration
document.addEventListener('DOMContentLoaded', function() {
    const password = document.getElementById('password');
    const confirmPassword = document.getElementById('confirm_password');
    
    if (password && confirmPassword) {
        function validatePasswordMatch() {
            if (confirmPassword.value !== password.value) {
                confirmPassword.setCustomValidity('Passwords do not match');
            } else {
                confirmPassword.setCustomValidity('');
            }
        }
        
        password.addEventListener('change', validatePasswordMatch);
        confirmPassword.addEventListener('keyup', validatePasswordMatch);
    }
}); 