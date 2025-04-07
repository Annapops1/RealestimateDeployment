// Client-side validation functions
const validators = {
    phone: (value) => {
        const pattern = /^(?:\+91)?[6-9]\d{9}$/;
        return {
            isValid: pattern.test(value),
            message: 'Please enter a valid Indian phone number'
        };
    },
    
    pincode: (value) => {
        const pattern = /^\d{6}$/;
        return {
            isValid: pattern.test(value),
            message: 'Please enter a valid 6-digit PIN code'
        };
    },
    
    email: (value) => {
        const pattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
        return {
            isValid: pattern.test(value),
            message: 'Please enter a valid email address'
        };
    },
    
    password: (value) => {
        const hasUpperCase = /[A-Z]/.test(value);
        const hasLowerCase = /[a-z]/.test(value);
        const hasNumbers = /\d/.test(value);
        const hasSpecialChar = /[!@#$%^&*(),.?":{}|<>]/.test(value);
        const isValidLength = value.length >= 8;
        
        return {
            isValid: hasUpperCase && hasLowerCase && hasNumbers && hasSpecialChar && isValidLength,
            message: 'Password must be at least 8 characters with uppercase, lowercase, number and special character'
        };
    },
    
    username: (value) => {
        const pattern = /^[a-zA-Z][a-zA-Z0-9_]{4,29}$/;
        return {
            isValid: pattern.test(value),
            message: 'Username must be 5-30 characters and start with a letter'
        };
    }
};

// Real-time validation function
function validateField(input, validatorName) {
    const field = input.closest('.form-group');
    const feedbackDiv = field.querySelector('.feedback-text');
    const value = input.value.trim();
    
    if (!value && !input.required) {
        field.classList.remove('is-invalid', 'is-valid');
        feedbackDiv.textContent = '';
        return true;
    }
    
    const validation = validators[validatorName](value);
    
    if (validation.isValid) {
        field.classList.remove('is-invalid');
        field.classList.add('is-valid');
        feedbackDiv.textContent = '';
    } else {
        field.classList.remove('is-valid');
        field.classList.add('is-invalid');
        feedbackDiv.textContent = validation.message;
    }
    
    return validation.isValid;
} 