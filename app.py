from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from database import Database
from my_face_utils import FaceRecognition
import os
from datetime import datetime
import base64
import cv2
import numpy as np
import sqlite3 
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta
import time
import logging
from logging.handlers import RotatingFileHandler
import re
import shutil

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def setup_logging():
    """Setup application logging"""
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    logger = logging.getLogger('attendance_system')
    logger.setLevel(logging.INFO)
    
    file_handler = RotatingFileHandler('logs/attendance.log', maxBytes=10240, backupCount=10)
    file_handler.setLevel(logging.INFO)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    return logger

def log_event(level, message, user_id=None):
    """Log security events"""
    user_info = f"User: {user_id}" if user_id else "User: Unknown"
    ip_info = f"IP: {request.remote_addr}"
    log_message = f"{message} - {user_info} - {ip_info}"
    
    if level == 'info':
        logger.info(log_message)
    elif level == 'warning':
        logger.warning(log_message)
    elif level == 'error':
        logger.error(log_message)

def validate_student_id(student_id):
    """Validate student ID format"""
    return bool(re.match(r'^[A-Z0-9]{4,10}$', student_id))

def validate_name(name):
    """Validate name format"""
    return bool(re.match(r'^[a-zA-Z\s]{2,50}$', name)) and len(name.strip()) >= 2

def sanitize_input(data):
    """Sanitize input data"""
    if isinstance(data, str):
        data = re.sub(r'[<>]', '', data)
        data = re.sub(r'javascript:', '', data, flags=re.IGNORECASE)
        return data.strip()
    return data

app = Flask(__name__)
app.secret_key = 'smart-attendance-system-secret-key-2024'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)

# Rate limiting storage
request_times = {}

def rate_limit(key, max_requests=10, time_window=60):
    """Simple rate limiting implementation"""
    current_time = time.time()
    if key not in request_times:
        request_times[key] = []
    
    # Remove old requests outside the time window
    request_times[key] = [t for t in request_times[key] if current_time - t < time_window]
    
    # Check if limit exceeded
    if len(request_times[key]) >= max_requests:
        return False
    
    # Add current request
    request_times[key].append(current_time)
    return True

# Initialize database and face recognition
db = Database()
fr = FaceRecognition()

@app.before_request
def security_checks():
    # 1. Rate limiting logic
    sensitive_endpoints = ['/login', '/register_face', '/mark_attendance', '/add_student']
    if request.path in sensitive_endpoints:
        client_ip = request.remote_addr
        if not rate_limit(client_ip):
            log_event('warning', 'Rate limit exceeded', session.get('user_id'))
            return jsonify({'success': False, 'message': 'Too many requests. Please try again later.'}), 429
    
    # 2. Session management logic
    session.permanent = True  # Make session permanent
    protected_routes = ['/faculty_dashboard', '/student_dashboard', '/reports', '/manage_students', '/admin', '/profile']
    if request.path in protected_routes and 'user_id' not in session:
        return redirect('/')
    
    # 3. Request logging logic
    if 'static' not in request.path and request.path != '/favicon.ico':
        log_event('info', f'{request.method} {request.path}', session.get('user_id'))


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/faculty_dashboard')
def faculty_dashboard():
    if 'user_type' not in session or session['user_type'] != 'faculty':
        return redirect('/')
    return render_template('faculty_dashboard.html')

@app.route('/student_dashboard')
def student_dashboard():
    if 'user_type' not in session or session['user_type'] != 'student':
        return redirect('/')
    return render_template('student_dashboard_enhanced.html')  # Use the new template

@app.route('/mark_attendance', methods=['POST'])
def mark_attendance():
    if 'user_type' not in session or session['user_type'] != 'faculty':
        return jsonify({'success': False, 'message': 'Faculty access required'})
    
    if request.json.get('test_mode'):
        student_id = request.json.get('student_id')
        subject = request.json.get('subject', 'General')
        
        if not student_id:
            return jsonify({'success': False, 'message': 'No student selected'})
        
        db.mark_attendance(student_id, subject, session['user_id'])
        student_name = db.get_student_name(student_id)
        
        return jsonify({
            'success': True,
            'message': f'Attendance marked for {student_name}',
            'student_id': student_id,
            'student_name': student_name,
            'confidence': 0.95
        })
    
    image_data = request.json.get('image')
    subject = request.json.get('subject', 'General')
    
    image_data = image_data.split(',')[1]
    nparr = np.frombuffer(base64.b64decode(image_data), np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    user_id, confidence = fr.recognize_face(img)
    confidence_threshold = 0.6
    
    if user_id and confidence > confidence_threshold:
        db.mark_attendance(user_id, subject, session['user_id'])
        student_name = db.get_student_name(user_id)
        return jsonify({
            'success': True,
            'message': f'Attendance marked for {student_name}',
            'student_id': user_id,
            'student_name': student_name,
            'confidence': round(confidence, 2)
        })
    else:
        return jsonify({'success': False, 'message': 'Face not recognized'})

@app.route('/get_attendance')
def get_attendance():
    if 'user_type' not in session or session['user_type'] != 'student':
        return jsonify({'success': False, 'message': 'Student access required'})
    
    try:
        attendance = db.get_student_attendance(session['user_id'])
        return jsonify({'success': True, 'attendance': attendance})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/reports')
def attendance_reports():
    if 'user_type' not in session or session['user_type'] != 'faculty':
        return redirect('/')
    
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(DISTINCT student_id) FROM attendance')
    total_students = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM attendance')
    total_records = cursor.fetchone()[0]
    
    cursor.execute('''
        SELECT subject, COUNT(*) as count 
        FROM attendance 
        GROUP BY subject 
        ORDER BY count DESC
    ''')
    subject_stats = cursor.fetchall()
    
    cursor.execute('''
        SELECT date, subject, COUNT(DISTINCT student_id) as present_count
        FROM attendance 
        WHERE date >= date('now', '-7 days')
        GROUP BY date, subject
        ORDER BY date DESC
    ''')
    recent_attendance = cursor.fetchall()
    conn.close()
    
    return render_template('reports.html',
                           total_students=total_students,
                           total_records=total_records,
                           subject_stats=subject_stats,
                           recent_attendance=recent_attendance)

@app.route('/api/attendance_data')
def api_attendance_data():
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT date, COUNT(DISTINCT student_id) as count
        FROM attendance 
        GROUP BY date 
        ORDER BY date
    ''')
    daily_data = cursor.fetchall()
    
    cursor.execute('''
        SELECT subject, COUNT(*) as count 
        FROM attendance 
        GROUP BY subject
    ''')
    subject_data = cursor.fetchall()
    conn.close()
    
    return jsonify({
        'daily': [{'date': row[0], 'count': row[1]} for row in daily_data],
        'subjects': [{'subject': row[0], 'count': row[1]} for row in subject_data]
    })

@app.route('/manage_students')
def manage_students():
    if 'user_type' not in session or session['user_type'] != 'faculty':
        return redirect('/')
    
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM students ORDER BY id')
    students = cursor.fetchall()
    conn.close()
    
    return render_template('manage_students.html', students=students)

@app.route('/delete_student/<student_id>')
def delete_student(student_id):
    if 'user_type' not in session or session['user_type'] != 'faculty':
        return jsonify({'success': False, 'message': 'Access denied'})
    
    try:
        db.delete_student(student_id)
        return jsonify({'success': True, 'message': 'Student deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/add_sample_attendance')
def add_sample_attendance():
    students = ['S001', 'S002', 'S003', 'S004']
    subjects = ['Mathematics', 'Physics', 'Chemistry', 'Computer Science']
    
    for student_id in students:
        for i in range(3):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            subject = subjects[i % len(subjects)]
            db.mark_attendance(student_id, subject, 'F001')
    
    return "Sample attendance data added!"

@app.route('/change_password', methods=['POST'])
def change_password():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    try:
        current_password = request.json.get('current_password')
        new_password = request.json.get('new_password')
        
        if not current_password or not new_password:
            return jsonify({'success': False, 'message': 'Both passwords are required'})
        
        if len(new_password) < 6:
            return jsonify({'success': False, 'message': 'New password must be at least 6 characters'})
        
        user = None
        if session['user_type'] == 'faculty':
            user = db.verify_faculty(session['user_id'], current_password)
        else:
            user = db.verify_student(session['user_id'], current_password)
        
        if not user:
            return jsonify({'success': False, 'message': 'Current password is incorrect'})
        
        conn = db.get_connection()
        cursor = conn.cursor()
        hashed_password = generate_password_hash(new_password)
        
        table = 'faculty' if session['user_type'] == 'faculty' else 'students'
        cursor.execute(f'UPDATE {table} SET password = ? WHERE id = ?', (hashed_password, session['user_id']))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Password updated successfully'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect('/')
    
    return render_template('profile.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

@app.errorhandler(403)
def forbidden_error(error):
    return render_template('403.html'), 403

@app.route('/check_session')
def check_session_status():
    if 'user_id' in session:
        return jsonify({
            'logged_in': True,
            'user_type': session.get('user_type'),
            'user_id': session.get('user_id')
        })
    return jsonify({'logged_in': False})

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.json
        user_type = data.get('user_type')
        user_id = data.get('user_id')
        password = data.get('password')
        
        log_event('info', f'Login attempt - Type: {user_type}', user_id)
        
        user = None
        redirect_url = ''
        if user_type == 'faculty':
            user = db.verify_faculty(user_id, password)
            redirect_url = '/faculty_dashboard'
        elif user_type == 'student':
            user = db.verify_student(user_id, password)
            redirect_url = '/student_dashboard'
        
        if user:
            session['user_id'] = user_id
            session['user_type'] = user_type
            session['name'] = user[1]
            log_event('info', f'{user_type.capitalize()} login successful', user_id)
            return jsonify({'success': True, 'redirect': redirect_url})
        else:
            log_event('warning', 'Login failed - invalid credentials', user_id)
            return jsonify({'success': False, 'message': 'Invalid credentials'})
    
    except Exception as e:
        log_event('error', f'Login error: {str(e)}')
        return jsonify({'success': False, 'message': 'Login error occurred'})

@app.route('/add_student', methods=['POST'])
def add_student():
    if 'user_type' not in session or session['user_type'] != 'faculty':
        return jsonify({'success': False, 'message': 'Access denied'})
    
    try:
        student_id = sanitize_input(request.json.get('student_id', ''))
        name = sanitize_input(request.json.get('name', ''))
        password = sanitize_input(request.json.get('password', 'student123'))
        email = sanitize_input(request.json.get('email', ''))
        
        if not student_id or not validate_student_id(student_id):
            return jsonify({'success': False, 'message': 'Invalid Student ID format. Use 4-10 alphanumeric characters.'})
        
        if not name or not validate_name(name):
            return jsonify({'success': False, 'message': 'Invalid name format. Use 2-50 letters and spaces only.'})
        
        if email and not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
            return jsonify({'success': False, 'message': 'Invalid email format'})
        
        db.add_student(student_id, name, password, email)
        log_event('info', f'Student added: {name} ({student_id})', session['user_id'])
        
        return jsonify({'success': True, 'message': 'Student added successfully'})
    
    except Exception as e:
        log_event('error', f'Add student error: {str(e)}', session.get('user_id'))
        return jsonify({'success': False, 'message': str(e)})

@app.route('/register_face', methods=['POST'])
def register_face():
    if 'user_type' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    try:
        image_data = request.json.get('image')
        image_index = request.json.get('image_index', 0)
        user_id = session['user_id']
        user_name = session['name']
        
        if not image_data:
            return jsonify({'success': False, 'message': 'No image data received'})
        
        print(f"🎯 Starting face registration for {user_name} ({user_id})")
        
        # Convert base64 to image
        image_data = image_data.split(',')[1]
        nparr = np.frombuffer(base64.b64decode(image_data), np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return jsonify({'success': False, 'message': 'Invalid image data'})
        
        # ✅ CORRECT: Call register_face on the FaceRecognition instance (fr)
        success = fr.register_face(img, user_id, user_name, image_index)
        
        if success:
            registered_count = fr.get_user_encodings_count(user_id)
            return jsonify({
                'success': True, 
                'message': f'Face image {image_index + 1} registered successfully!',
                'registered_count': registered_count
            })
        else:
            return jsonify({
                'success': False, 
                'message': 'Face detection failed. Please ensure good lighting and clear face visibility.'
            })
            
    except Exception as e:
        print(f"❌ Error in register_face route: {e}")
        return jsonify({'success': False, 'message': f'Registration error: {str(e)}'})
    

@app.route('/get_face_status')
def get_face_status():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    try:
        user_id = session['user_id']
        registered_count = fr.get_user_encodings_count(user_id)
        
        return jsonify({
            'success': True,
            'registered_count': registered_count,
            'total_images': 4,
            'progress_percent': int((registered_count / 4) * 100),
            'completed': registered_count >= 4
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/delete_face_data')
def delete_face_data():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    try:
        user_id = session['user_id']
        fr.remove_user_faces(user_id)
        return jsonify({'success': True, 'message': 'Face data deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/backup')
def backup_database():
    if 'user_type' not in session or session['user_type'] != 'faculty':
        return jsonify({'success': False, 'message': 'Access denied'})
    
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'backup/attendance_backup_{timestamp}.db'
        os.makedirs('backup', exist_ok=True)
        shutil.copy2('attendance.db', backup_filename)
        
        return jsonify({'success': True, 'message': f'Backup created: {backup_filename}'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

if __name__ == '__main__':
    # Create necessary directories on startup
    directories = ['uploads', 'static', 'templates', 'backup', 'logs']
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Created {directory} directory")
    
    # Initialize logging
    logger = setup_logging()

    print("🚀 Starting Secure Smart Attendance System...")
    print("📊 Access the application at http://0.0.0.0:5000 or http://localhost:5000")
    
    # Run the Flask app
    # Set debug=False for production, debug=True for development
    app.run(debug=True, host='0.0.0.0', port=5000)