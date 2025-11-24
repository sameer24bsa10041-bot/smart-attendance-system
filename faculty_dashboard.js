let videoStream = null;
let video = document.getElementById('video');
let canvas = document.getElementById('canvas');
let context = canvas.getContext('2d');
let testMode = false;

// Initialize camera
async function initCamera() {
    try {
        videoStream = await navigator.mediaDevices.getUserMedia({ 
            video: { width: 640, height: 480 } 
        });
        video.srcObject = videoStream;
    } catch (error) {
        console.error('Error accessing camera:', error);
        showMessage('Cannot access camera. Please check permissions.', 'error');
    }
}

// Test mode toggle
document.getElementById('test-mode-btn').addEventListener('click', function() {
    testMode = !testMode;
    const testStudentGroup = document.getElementById('test-student-group');
    const video = document.getElementById('video');
    const testModeBtn = document.getElementById('test-mode-btn');
    
    if (testMode) {
        testModeBtn.textContent = 'Disable Test Mode';
        testModeBtn.classList.remove('btn-secondary');
        testModeBtn.classList.add('btn-warning');
        testStudentGroup.style.display = 'block';
        video.style.opacity = '0.5';
        showMessage('Test mode enabled. Select a student to simulate recognition.', 'success');
    } else {
        testModeBtn.textContent = 'Enable Test Mode';
        testModeBtn.classList.remove('btn-warning');
        testModeBtn.classList.add('btn-secondary');
        testStudentGroup.style.display = 'none';
        video.style.opacity = '1';
        showMessage('Test mode disabled. Using real face recognition.', 'success');
    }
});

// Capture button handler
document.getElementById('capture-btn').addEventListener('click', async function() {
    if (testMode) {
        await markAttendanceTest();
    } else {
        await markAttendanceReal();
    }
});

// Test mode attendance marking
async function markAttendanceTest() {
    const subject = document.getElementById('subject-select').value;
    const studentId = document.getElementById('test-student-select').value;
    
    const students = {
        'S001': { name: 'John Doe' },
        'S002': { name: 'Jane Smith' },
        'S003': { name: 'Mike Johnson' },
        'S004': { name: 'Sarah Wilson' }
    };
    
    const student = students[studentId];
    
    if (!studentId) {
        showMessage('Please select a student first', 'error');
        return;
    }
    
    const captureBtn = document.getElementById('capture-btn');
    const originalText = captureBtn.textContent;
    captureBtn.textContent = 'Marking...';
    captureBtn.disabled = true;
    
    try {
        const response = await fetch('/mark_attendance', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                test_mode: true,
                student_id: studentId,
                subject: subject
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showMessage(`TEST: Attendance marked for ${student.name}`, 'success');
            addAttendanceRecord({
                student_id: studentId,
                student_name: student.name,
                subject: subject,
                time: new Date().toLocaleTimeString(),
                confidence: '0.95 (Test)'
            });
        } else {
            showMessage(result.message, 'error');
        }
    } catch (error) {
        showMessage('Error marking attendance', 'error');
        console.error('Attendance error:', error);
    } finally {
        captureBtn.textContent = originalText;
        captureBtn.disabled = false;
    }
}

// Real face recognition attendance marking
async function markAttendanceReal() {
    if (!videoStream) {
        showMessage('Camera not available', 'error');
        return;
    }
    
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    const imageData = canvas.toDataURL('image/jpeg');
    const subject = document.getElementById('subject-select').value;
    
    const captureBtn = document.getElementById('capture-btn');
    const originalText = captureBtn.textContent;
    captureBtn.textContent = 'Recognizing...';
    captureBtn.disabled = true;
    
    try {
        const response = await fetch('/mark_attendance', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                image: imageData,
                subject: subject
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showMessage(result.message, 'success');
            addAttendanceRecord({
                student_id: result.student_id,
                student_name: result.student_name,
                subject: subject,
                time: new Date().toLocaleTimeString(),
                confidence: result.confidence
            });
        } else {
            showMessage(result.message, 'error');
        }
    } catch (error) {
        showMessage('Error marking attendance', 'error');
        console.error('Attendance error:', error);
    } finally {
        captureBtn.textContent = originalText;
        captureBtn.disabled = false;
    }
}

// Add attendance record to the list
function addAttendanceRecord(record) {
    const recordsContainer = document.getElementById('attendance-records');
    
    // Remove "no records" message if it exists
    const noRecords = recordsContainer.querySelector('.no-records');
    if (noRecords) {
        noRecords.remove();
    }
    
    const recordElement = document.createElement('div');
    recordElement.className = 'attendance-record';
    recordElement.innerHTML = `
        <div class="record-header">
            <span class="student-name">${record.student_name}</span>
            <span class="confidence">Confidence: ${record.confidence}</span>
        </div>
        <div class="record-details">
            <span class="subject">${record.subject}</span>
            <span class="time">${record.time}</span>
        </div>
    `;
    
    recordsContainer.insertBefore(recordElement, recordsContainer.firstChild);
    
    // Limit to 10 records
    if (recordsContainer.children.length > 10) {
        recordsContainer.removeChild(recordsContainer.lastChild);
    }
}

// Refresh attendance records
document.getElementById('refresh-btn').addEventListener('click', loadRecentAttendance);

// Load recent attendance records
async function loadRecentAttendance() {
    try {
        // For now, we'll just clear the "no records" message
        const recordsContainer = document.getElementById('attendance-records');
        const noRecords = recordsContainer.querySelector('.no-records');
        if (noRecords) {
            noRecords.textContent = 'Attendance records will appear here when marked.';
        }
    } catch (error) {
        console.error('Error loading attendance records:', error);
    }
}

// Utility function to show messages
function showMessage(message, type) {
    const resultDiv = document.getElementById('result');
    resultDiv.innerHTML = `
        <div class="message ${type}">
            <i class="fas fa-${type === 'success' ? 'check' : 'exclamation'}-circle"></i>
            ${message}
        </div>
    `;
    
    setTimeout(() => {
        resultDiv.innerHTML = '';
    }, 5000);
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    initCamera();
    loadRecentAttendance();
});

// Clean up camera when leaving page
window.addEventListener('beforeunload', function() {
    if (videoStream) {
        videoStream.getTracks().forEach(track => track.stop());
    }
});