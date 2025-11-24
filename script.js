// Tab switching functionality
document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', function() {
        // Remove active class from all tabs and forms
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.login-form').forEach(f => f.classList.remove('active'));
        
        // Add active class to clicked tab
        this.classList.add('active');
        
        // Show corresponding form
        const tabId = this.getAttribute('data-tab');
        document.getElementById(`${tabId}-form`).classList.add('active');
    });
});

// Form submission handling
document.getElementById('faculty-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    await login('faculty');
});

document.getElementById('student-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    await login('student');
});

async function login(userType) {
    const userId = document.getElementById(`${userType}-id`).value;
    const password = document.getElementById(`${userType}-password`).value;
    
    try {
        const response = await fetch('/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_type: userType,
                user_id: userId,
                password: password
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            window.location.href = result.redirect;
        } else {
            showMessage(result.message, 'error');
        }
    } catch (error) {
        showMessage('Login failed. Please try again.', 'error');
        console.error('Login error:', error);
    }
}

function showMessage(message, type) {
    // Remove existing messages
    const existingMessage = document.querySelector('.message');
    if (existingMessage) {
        existingMessage.remove();
    }
    
    // Create new message element
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    messageDiv.textContent = message;
    messageDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        border-radius: 5px;
        color: white;
        font-weight: 600;
        z-index: 1000;
        background-color: ${type === 'error' ? '#e74c3c' : '#2ecc71'};
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    `;
    
    document.body.appendChild(messageDiv);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        messageDiv.remove();
    }, 3000);
}