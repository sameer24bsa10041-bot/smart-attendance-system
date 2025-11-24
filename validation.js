// Data Validation Utilities
class Validator {
    static sanitizeInput(input) {
        if (typeof input !== 'string') return input;
        return input.replace(/[<>]/g, '').trim();
    }
    
    static validateEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }
    
    static validateStudentId(id) {
        return /^[A-Z0-9]{4,10}$/.test(id);
    }
    
    static validateName(name) {
        return /^[a-zA-Z\s]{2,50}$/.test(name);
    }
    
    static validatePassword(password) {
        return password.length >= 6;
    }
}

// Form validation
function setupFormValidation() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateForm(this)) {
                e.preventDefault();
            }
        });
    });
}

function validateForm(form) {
    let isValid = true;
    const errors = [];
    
    // Clear previous errors
    const existingErrors = form.querySelectorAll('.error-message');
    existingErrors.forEach(error => error.remove());
    
    const inputs = form.querySelectorAll('input, select');
    
    inputs.forEach(input => {
        input.classList.remove('error');
        const value = input.value.trim();
        const name = input.name;
        
        // Required field validation
        if (input.required && !value) {
            showFieldError(input, 'This field is required');
            isValid = false;
            return;
        }
        
        // Type-specific validation
        switch (name) {
            case 'student_id':
                if (value && !Validator.validateStudentId(value)) {
                    showFieldError(input, 'Student ID must be 4-10 alphanumeric characters');
                    isValid = false;
                }
                break;
                
            case 'name':
                if (value && !Validator.validateName(value)) {
                    showFieldError(input, 'Name must be 2-50 letters only');
                    isValid = false;
                }
                break;
                
            case 'email':
                if (value && !Validator.validateEmail(value)) {
                    showFieldError(input, 'Please enter a valid email address');
                    isValid = false;
                }
                break;
                
            case 'password':
                if (value && !Validator.validatePassword(value)) {
                    showFieldError(input, 'Password must be at least 6 characters');
                    isValid = false;
                }
                break;
        }
    });
    
    return isValid;
}

function showFieldError(input, message) {
    input.classList.add('error');
    
    const errorElement = document.createElement('div');
    errorElement.className = 'error-message';
    errorElement.textContent = message;
    errorElement.style.color = '#e74c3c';
    errorElement.style.fontSize = '14px';
    errorElement.style.marginTop = '5px';
    
    input.parentNode.appendChild(errorElement);
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', setupFormValidation);