let videoStream = null;
let video = document.getElementById('video');
let canvas = document.getElementById('canvas');
let context = canvas.getContext('2d');
let capturedImages = [];
let currentImageIndex = 0;
const maxImages = 4;

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
        video.setAttribute('webkit-playsinline', true);
        video.muted = true;
        video.play();
        
        // Load existing registration status
        await loadRegistrationStatus();
        
    } catch (error) {
        console.error('Camera error:', error);
        showMessage('Camera access failed. Please ensure you are using HTTPS and have granted camera permissions.', 'error');
    }
}

// Capture image
document.getElementById('capture-btn').addEventListener('click', async function() {
    if (!videoStream) {
        showMessage('Camera not available', 'error');
        return;
    }
    
    if (currentImageIndex >= maxImages) {
        showMessage('Maximum images captured. You can reset to start over.', 'info');
        return;
    }
    
    // Set canvas dimensions to match video
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    // Draw current video frame to canvas
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    // Convert canvas image to base64
    const imageData = canvas.toDataURL('image/jpeg');
    
    // Store captured image
    capturedImages.push({
        imageData: imageData,
        index: currentImageIndex + 1,
        timestamp: new Date().toLocaleTimeString()
    });
    
    // Show captured image thumbnail
    displayCapturedImage(imageData, currentImageIndex + 1);
    
    // Register face with the captured image
    await registerFaceImage(imageData, currentImageIndex);
    
    currentImageIndex++;
    updateUI();
});

// Reset registration
document.getElementById('reset-btn').addEventListener('click', function() {
    if (confirm('Are you sure you want to reset all captured images?')) {
        capturedImages = [];
        currentImageIndex = 0;
        document.getElementById('imagesGrid').innerHTML = '';
        document.getElementById('registration-result').innerHTML = '';
        updateUI();
        showMessage('Registration reset. You can start over.', 'info');
    }
});

// Register a single face image
async function registerFaceImage(imageData, imageIndex) {
    const btn = document.getElementById('capture-btn');
    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Registering...';
    btn.disabled = true;
    
    try {
        const response = await fetch('/register_face', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                image: imageData,
                image_index: imageIndex
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showMessage(`✅ Image ${imageIndex + 1} registered successfully!`, 'success');
        } else {
            showMessage(`❌ Image ${imageIndex + 1} failed: ${result.message}`, 'error');
            // Remove the failed image from array
            capturedImages.pop();
            currentImageIndex--;
        }
    } catch (error) {
        showMessage('Error registering face', 'error');
        capturedImages.pop();
        currentImageIndex--;
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
        updateUI();
    }
}

// Display captured image thumbnail
function displayCapturedImage(imageData, imageNumber) {
    const imagesGrid = document.getElementById('imagesGrid');
    
    const imageElement = document.createElement('div');
    imageElement.className = 'captured-image-thumb';
    imageElement.innerHTML = `
        <img src="${imageData}" alt="Captured image ${imageNumber}">
        <div class="image-number">${imageNumber}</div>
        <div class="image-status">✅ Registered</div>
    `;
    
    imagesGrid.appendChild(imageElement);
}

// Update UI based on current state
function updateUI() {
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');
    const currentImageSpan = document.getElementById('currentImage');
    const captureBtn = document.getElementById('capture-btn');
    
    // Update progress
    const progress = (currentImageIndex / maxImages) * 100;
    progressFill.style.width = `${progress}%`;
    progressText.textContent = `${currentImageIndex}/${maxImages} images registered`;
    currentImageSpan.textContent = currentImageIndex + 1;
    
    // Update button state
    if (currentImageIndex >= maxImages) {
        captureBtn.disabled = true;
        captureBtn.innerHTML = '<i class="fas fa-check"></i> All Images Captured';
        showMessage('🎉 All images captured! Face registration complete.', 'success');
    }
}

// Load existing registration status
async function loadRegistrationStatus() {
    try {
        const response = await fetch('/get_face_registration_status');
        const result = await response.json();
        
        if (result.success) {
            currentImageIndex = result.registered_count;
            updateUI();
            
            if (result.registered_count > 0) {
                showMessage(`You have ${result.registered_count} images registered.`, 'info');
            }
        }
    } catch (error) {
        console.error('Error loading registration status:', error);
    }
}

// Utility function to show messages
function showMessage(message, type) {
    const resultDiv = document.getElementById('registration-result');
    resultDiv.innerHTML = `
        <div class="message ${type}">
            <i class="fas fa-${type === 'success' ? 'check' : 'exclamation'}-circle"></i>
            ${message}
        </div>
    `;
    
    if (type === 'success') {
        setTimeout(() => {
            resultDiv.innerHTML = '';
        }, 5000);
    }
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
                    <small>Your attendance will appear here once marked by faculty.</small>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error loading attendance records:', error);
        document.getElementById('attendance-list').innerHTML = `
            <div class="error">
                <i class="fas fa-exclamation-triangle"></i>
                <p>Error loading attendance records.</p>
            </div>
        `;
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    initCamera();
    loadAttendanceRecords();
    
    // Add refresh button functionality
    const refreshBtn = document.getElementById('refresh-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', loadAttendanceRecords);
    }
});

// Cleanup
window.addEventListener('beforeunload', function() {
    if (videoStream) {
        videoStream.getTracks().forEach(track => track.stop());
    }
});