import sqlite3
import os
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import threading
from functools import wraps
import time

def retry_on_locked(max_retries=3, delay=1):
    """Retry decorator for database locked errors"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except sqlite3.OperationalError as e:
                    if "database is locked" in str(e) and attempt < max_retries - 1:
                        print(f"Database locked, retrying in {delay} seconds...")
                        time.sleep(delay)
                    else:
                        raise
            return func(*args, **kwargs)
        return wrapper
    return decorator

class Database:
    def __init__(self, db_name='attendance.db'):
        self.db_name = db_name
        self.lock = threading.Lock()
        self.init_db()
    
    def get_connection(self):
        """Get database connection with timeout and error handling"""
        try:
            conn = sqlite3.connect(
                self.db_name, 
                timeout=30,
                check_same_thread=False
            )
            conn.execute("PRAGMA busy_timeout = 30000")
            return conn
        except sqlite3.Error as e:
            print(f"Database connection error: {e}")
            raise
    
    def init_db(self):
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Faculty table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS faculty (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    password TEXT NOT NULL,
                    email TEXT
                )
            ''')
            
            # Students table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS students (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    password TEXT NOT NULL,
                    email TEXT,
                    face_registered BOOLEAN DEFAULT FALSE
                )
            ''')
            
            # Attendance table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id TEXT,
                    subject TEXT,
                    date TEXT,
                    time TEXT,
                    marked_by TEXT,
                    FOREIGN KEY (student_id) REFERENCES students (id)
                )
            ''')
            
            # Clear and insert sample faculty with HASHED passwords
            cursor.execute('DELETE FROM faculty')
            cursor.execute('''
                INSERT OR IGNORE INTO faculty (id, name, password, email) 
                VALUES (?, ?, ?, ?)
            ''', ('F001', 'Dr. C.P Koushik', generate_password_hash('faculty123'), 'smith@university.edu'))
            
            # Clear and insert sample students with HASHED passwords
            cursor.execute('DELETE FROM students')
            sample_students = [
                ('S001', 'Sameer Jain', generate_password_hash('student123'), 'john@university.edu'),
                ('S002', 'Tanmaya Puri', generate_password_hash('student123'), 'jane@university.edu'),
                ('S003', 'Devansh Bansal', generate_password_hash('student123'), 'mike@university.edu'),
                ('S004', 'Anuj Parashar', generate_password_hash('student123'), 'sarah@university.edu')
            ]
            
            for student in sample_students:
                cursor.execute('''
                    INSERT OR IGNORE INTO students (id, name, password, email) 
                    VALUES (?, ?, ?, ?)
                ''', student)
            
            # Clear existing attendance
            cursor.execute('DELETE FROM attendance')
            
            # Add some sample attendance records for testing
            today = datetime.now().strftime('%Y-%m-%d')
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            
            sample_attendance = [
                ('S001', 'Mathematics', yesterday, '09:00:00', 'F001'),
                ('S002', 'Mathematics', yesterday, '09:01:00', 'F001'),
                ('S001', 'Physics', today, '10:00:00', 'F001'),
                ('S003', 'Physics', today, '10:01:00', 'F001'),
            ]
            
            for record in sample_attendance:
                cursor.execute('''
                    INSERT OR IGNORE INTO attendance (student_id, subject, date, time, marked_by)
                    VALUES (?, ?, ?, ?, ?)
                ''', record)
            
            # Add indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_attendance_student_id ON attendance(student_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_attendance_subject ON attendance(subject)')
            
            conn.commit()
            conn.close()
            print("✅ Database initialized with secure passwords")
    
    def verify_faculty(self, faculty_id, password):
        """Verify faculty with password hashing"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM faculty WHERE id = ?', (faculty_id,))
        faculty = cursor.fetchone()
        conn.close()
        
        if faculty and check_password_hash(faculty[2], password):
            return faculty
        return None
    
    def verify_student(self, student_id, password):
        """Verify student with password hashing"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM students WHERE id = ?', (student_id,))
        student = cursor.fetchone()
        conn.close()
        
        if student and check_password_hash(student[2], password):
            return student
        return None
    
    @retry_on_locked()
    def add_student(self, student_id, name, password='student123', email=''):
        """Add student with password hashing"""
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            try:
                hashed_password = generate_password_hash(password)
                
                cursor.execute('''
                    INSERT INTO students (id, name, password, email) 
                    VALUES (?, ?, ?, ?)
                ''', (student_id, name, hashed_password, email))
                
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                raise Exception('Student ID already exists')
            except Exception as e:
                raise Exception(f'Database error: {str(e)}')
            finally:
                conn.close()
    
    @retry_on_locked()
    def delete_student(self, student_id):
        """Delete student safely"""
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            try:
                cursor.execute('DELETE FROM students WHERE id = ?', (student_id,))
                conn.commit()
                return True
            except Exception as e:
                raise Exception(f'Database error: {str(e)}')
            finally:
                conn.close()
    
    @retry_on_locked()
    def mark_attendance(self, student_id, subject, marked_by):
        """Mark attendance with thread safety"""
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            try:
                current_date = datetime.now().strftime('%Y-%m-%d')
                current_time = datetime.now().strftime('%H:%M:%S')
                
                cursor.execute('''
                    INSERT INTO attendance (student_id, subject, date, time, marked_by)
                    VALUES (?, ?, ?, ?, ?)
                ''', (student_id, subject, current_date, current_time, marked_by))
                
                conn.commit()
            except Exception as e:
                raise Exception(f'Database error: {str(e)}')
            finally:
                conn.close()
    
    def get_student_attendance(self, student_id):
        """Get student attendance records"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT subject, date, time, marked_by 
                FROM attendance 
                WHERE student_id = ? 
                ORDER BY date DESC, time DESC
            ''', (student_id,))
            
            attendance = cursor.fetchall()
            
            return [{
                'subject': record[0],
                'date': record[1],
                'time': record[2],
                'marked_by': record[3]
            } for record in attendance]
        finally:
            conn.close()
    
    def get_student_name(self, student_id):
        """Get student name by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT name FROM students WHERE id = ?', (student_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    
    
    def get_all_students(self):
        """Get all students for management"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM students ORDER BY id')
        students = cursor.fetchall()
        conn.close()
        return students

def optimize_database(self):
    """Optimize database performance."""
    conn = self.get_connection()
    cursor = conn.cursor()
    
    # Enable WAL mode for better concurrency
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA cache_size=-64000")  # 64MB cache
    
    # Create additional indexes
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_attendance_date_subject 
        ON attendance(date, subject)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_attendance_student_date 
        ON attendance(student_id, date DESC)
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Database optimized for performance")