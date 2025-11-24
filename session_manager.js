// Advanced Session Management System
class SessionManager {
    constructor() {
        this.timeout = 120 * 60 * 1000; // 2 hours in milliseconds
        this.warningTime = 5 * 60 * 1000; // 5 minutes warning
        this.logoutUrl = '/logout';
        this.checkSessionUrl = '/check_session';
        this.timer = null;
        this.warningTimer = null;
        this.isWarningShown = false;
        
        this.init();
    }
    
    init() {
        console.log('Session Manager Initialized');
        this.resetTimer();
        this.setupEventListeners();
        this.startSessionChecker();
    }
    
    setupEventListeners() {
        // Reset timer on user activity
        const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'];
        events.forEach(event => {
            document.addEventListener(event, () => this.resetTimer());
        });
    }
    
    resetTimer() {
        // Clear existing timers
        if (this.timer) clearTimeout(this.timer);
        if (this.warningTimer) clearTimeout(this.warningTimer);
        this.isWarningShown = false;
        
        // Set new timers
        this.warningTimer = setTimeout(() => this.showWarning(), this.timeout - this.warningTime);
        this.timer = setTimeout(() => this.logout(), this.timeout);
    }
    
    showWarning() {
        if (this.isWarningShown) return;
        
        this.isWarningShown = true;
        this.createWarningModal();
    }
    
    createWarningModal() {
        // Remove existing modal if any
        const existingModal = document.getElementById('session-warning-modal');
        if (existingModal) existingModal.remove();
        
        // Create warning modal
        const modal = document.createElement('div');
        modal.id = 'session-warning-modal';
        modal.innerHTML = `
            <div class="session-warning-overlay">
                <div class="session-warning-modal">
                    <div class="warning-header">
                        <i class="fas fa-exclamation-triangle"></i>
                        <h3>Session Timeout Warning</h3>
                    </div>
                    <div class="warning-body">
                        <p>Your session will expire in <strong id="countdown">5:00</strong> minutes due to inactivity.</p>
                    </div>
                    <div class="warning-actions">
                        <button id="continue-session" class="btn">
                            Continue Session
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Start countdown
        this.startCountdown(5 * 60);
        
        // Add event listeners
        document.getElementById('continue-session').addEventListener('click', () => {
            this.continueSession();
        });
    }
    
    startCountdown(seconds) {
        let timeLeft = seconds;
        const countdownElement = document.getElementById('countdown');
        
        const countdownInterval = setInterval(() => {
            if (!this.isWarningShown) {
                clearInterval(countdownInterval);
                return;
            }
            
            timeLeft--;
            const minutes = Math.floor(timeLeft / 60);
            const seconds = timeLeft % 60;
            countdownElement.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
            
            if (timeLeft <= 0) {
                clearInterval(countdownInterval);
                this.logout();
            }
        }, 1000);
    }
    
    continueSession() {
        this.resetTimer();
        this.removeWarningModal();
        this.showToast('Session extended successfully!', 'success');
    }
    
    async checkSessionStatus() {
        try {
            const response = await fetch(this.checkSessionUrl);
            const data = await response.json();
            
            if (!data.logged_in) {
                this.redirectToLogin();
            }
        } catch (error) {
            console.error('Session check failed:', error);
        }
    }
    
    startSessionChecker() {
        // Check session status every minute
        setInterval(() => this.checkSessionStatus(), 60 * 1000);
    }
    
    logout() {
        this.showToast('Session expired. Redirecting to login...', 'warning');
        
        setTimeout(() => {
            window.location.href = this.logoutUrl;
        }, 2000);
    }
    
    redirectToLogin() {
        window.location.href = '/?message=session_expired';
    }
    
    removeWarningModal() {
        const modal = document.getElementById('session-warning-modal');
        if (modal) modal.remove();
        this.isWarningShown = false;
    }
    
    showToast(message, type = 'info') {
        const existingToasts = document.querySelectorAll('.session-toast');
        existingToasts.forEach(toast => toast.remove());
        
        const toast = document.createElement('div');
        toast.className = `session-toast session-toast-${type}`;
        toast.innerHTML = `<div class="toast-content">${message}</div>`;
        
        document.body.appendChild(toast);
        
        setTimeout(() => toast.classList.add('show'), 100);
        
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
}

// Initialize session manager
document.addEventListener('DOMContentLoaded', () => {
    new SessionManager();
});