let videoStream = null;
let video = document.getElementById('video');
let canvas = document.getElementById('canvas');
let context = canvas.getContext('2d');
let currentAngle = 0;
const angles = [
    { id: 1, name: "Front View", icon: "👤", instruction: "Look straight at camera" },
    { id: 2, name: "Left Side", icon: "↖️", instruction: "Turn head slightly left" },
    { id: 3, name: "Right Side", icon: "↗️", instruction: "Turn head slightly right" },
    { id: 4, name: "Natural Expression", icon: "😊", instruction: "Smile naturally" }
];
let capturedAngles = [];

// Initialize camera
async function initCamera() {
    try {
        const constraints = {
            video: {
                width: { ideal: 640 },
                height: { ideal: 480 },
                facingMode: 'user'
            },
            audio: false
        };
        
        videoStream = await navigator.mediaDevices.getUserMedia(constraints);
        video.srcObject = videoStream;
        video.setAttribute('playsinline', true);
        video.muted = true;
        
        // Load current registration status
        await loadRegistrationStatus();
        
    } catch (error) {
        console.error('Camera error:', error);
        showMessage('Camera access failed. Please allow camera permissions.', 'error');
        document.getElementById('capture-btn').disabled = true;
    }
}

// Load current registration status
async function loadRegistrationStatus() {
    try {
        const response = await fetch('/get_face_status');
        const result = await response.json();
        
        if (result.success) {
            currentAngle = result.registered_count;
            capturedAngles = Array(result.registered_count).fill().map((_, i) => i);
            updateUI();
            updateAngleCards();
            
            if (result.registered_count > 0) {
                showFeedback(`Loaded ${result.registered_count} previously registered images`, 'success');
            }
        }
    } catch (error) {
        console.error('Error loading status:', error);
    }
}

// Capture current angle
document.getElementById('capture-btn').addEventListener('click', async function() {
    if (currentAngle >= 4) {
        showFeedback('🎉 All angles captured! Registration complete.', 'success');
        return;
    }
    
    if (!videoStream) {
        showFeedback('Camera not ready', 'error');
        return;
    }
    
    // Capture image
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    const imageData = canvas.toDataURL('image/jpeg');
    
    // Show loading state
    const btn = this;
    const originalHTML = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
    btn.disabled = true;
    
    try {
        const response = await fetch('/register_face', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                image: imageData,
                image_index: currentAngle
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Successfully registered
            capturedAngles.push(currentAngle);
            currentAngle++;
            
            // Add thumbnail
            addThumbnail(imageData, currentAngle);
            
            // Update angle card
            updateAngleCard(currentAngle, true);
            
            showFeedback(`✅ ${angles[currentAngle-1].name} captured successfully!`, 'success');
            
            if (currentAngle >= 4) {
                showFeedback('🎉 Face registration complete! All angles captured.', 'success');
                showMessage('Face registration completed successfully! You can now be recognized for attendance.', 'success');
            }
            
        } else {
            showFeedback(`❌ Failed: ${result.message}`, 'error');
        }
        
    } catch (error) {
        showFeedback('❌ Network error. Please try again.', 'error');
        console.error('Capture error:', error);
    } finally {
        btn.innerHTML = originalHTML;
        btn.disabled = false;
        updateUI();
    }
});

// Reset registration
document.getElementById('reset-btn').addEventListener('click', function() {
    if (capturedAngles.length === 0) {
        showFeedback('No images to reset', 'info');
        return;
    }
    
    if (confirm('Are you sure you want to reset all captured images? This will delete your face registration.')) {
        resetRegistration();
    }
});

async function resetRegistration() {
    try {
        const response = await fetch('/delete_face_data');
        const result = await response.json();
        
        if (result.success) {
            currentAngle = 0;
            capturedAngles = [];
            document.getElementById('thumbnails').innerHTML = '';
            updateUI();
            resetAngleCards();
            showFeedback('Registration reset. You can start over.', 'success');
        } else {
            showFeedback('Error resetting registration', 'error');
        }
    } catch (error) {
        showFeedback('Network error during reset', 'error');
    }
}

// Update the UI
function updateUI() {
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');
    const captureBtn = document.getElementById('capture-btn');
    const captureText = document.getElementById('capture-text');
    
    // Update progress
    const progress = (currentAngle / 4) * 100;
    progressFill.style.width = `${progress}%`;
    progressText.textContent = `${currentAngle}/4 images registered`;
    
    // Update button text
    if (currentAngle < 4) {
        const nextAngle = angles[currentAngle];
        captureText.textContent = `Capture ${nextAngle.name} (${currentAngle + 1}/4)`;
        captureBtn.disabled = false;
    } else {
        captureText.textContent = 'Registration Complete!';
        captureBtn.disabled = true;
    }
    
    // Highlight current angle
    highlightCurrentAngle();
}

// Update angle cards
function updateAngleCards() {
    angles.forEach((angle, index) => {
        const isCaptured = capturedAngles.includes(index);
        updateAngleCard(index + 1, isCaptured);
    });
}

function updateAngleCard(angleNumber, isCaptured) {
    const card = document.getElementById(`angle${angleNumber}`);
    const status = document.getElementById(`status${angleNumber}`);
    
    if (isCaptured) {
        card.classList.add('active');
        status.innerHTML = '✅ Captured';
        status.style.color = '#4CAF50';
    } else {
        card.classList.remove('active');
        status.innerHTML = '❌ Not captured';
        status.style.color = '#f44336';
    }
}

function resetAngleCards() {
    for (let i = 1; i <= 4; i++) {
        const card = document.getElementById(`angle${i}`);
        const status = document.getElementById(`status${i}`);
        card.classList.remove('active');
        status.innerHTML = '❌ Not captured';
        status.style.color = '#f44336';
    }
}

function highlightCurrentAngle() {
    // Remove current highlight
    for (let i = 1; i <= 4; i++) {
        document.getElementById(`angle${i}`).classList.remove('current-angle');
    }
    
    // Highlight current angle if not completed
    if (currentAngle < 4) {
        document.getElementById(`angle${currentAngle + 1}`).classList.add('current-angle');
    }
}

// Add thumbnail to results
function addThumbnail(imageData, angleNumber) {
    const thumbnails = document.getElementById('thumbnails');
    
    const thumbnail = document.createElement('div');
    thumbnail.className = 'thumbnail';
    thumbnail.innerHTML = `
        <img src="${imageData}" alt="Angle ${angleNumber}">
        <div class="thumbnail-label">${angles[angleNumber-1].name}</div>
    `;
    
    thumbnails.appendChild(thumbnail);
}

// Show feedback message
function showFeedback(message, type) {
    const feedback = document.getElementById('feedback');
    feedback.textContent = message;
    feedback.className = `capture-feedback ${type}-feedback`;
    
    setTimeout(() => {
        feedback.textContent = '';
        feedback.className = 'capture-feedback';
    }, 5000);
}

// Show permanent message
function showMessage(message, type) {
    const resultDiv = document.getElementById('registration-result');
    resultDiv.innerHTML = `
        <div class="message ${type}">
            <i class="fas fa-${type === 'success' ? 'check' : 'exclamation'}-circle"></i>
            ${message}
        </div>
    `;
}

// Load attendance records
async function loadAttendanceRecords() {
    try {
        const response = await fetch('/get_attendance');
        const result = await response.json();
        
        const attendanceList = document.getElementById('attendance-list');
        
        if (result.success && result.attendance && result.attendance.length > 0) {
            attendanceList.innerHTML = result.attendance.map(record => `
                <div class="attendance-item">
                    <div class="subject"><strong>${record.subject || 'General'}</strong></div>
                    <div class="date-time">
                        <span class="date">${record.date || 'N/A'}</span>
                        <span class="time">${record.time || 'N/A'}</span>
                    </div>
                    <div class="marked-by">Marked by: ${record.marked_by || 'Faculty'}</div>
                </div>
            `).join('');
        } else {
            attendanceList.innerHTML = `
                <div class="no-attendance">
                    <i class="fas fa-clipboard-list"></i>
                    <p>No attendance records found.</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error loading attendance:', error);
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    initCamera();
    loadAttendanceRecords();
    
    // Refresh attendance button
    document.getElementById('refresh-btn').addEventListener('click', loadAttendanceRecords);
});

// Cleanup
window.addEventListener('beforeunload', function() {
    if (videoStream) {
        videoStream.getTracks().forEach(track => track.stop());
    }
});