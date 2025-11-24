#!/usr/bin/env python3
import os
import sys
from database import Database

def setup_system():
    print("🎯 Smart Attendance System Setup")
    print("=" * 40)
    
    # Create necessary directories
    directories = ['uploads', 'static', 'templates', 'backup', 'logs', 'data']
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"✅ Created {directory}/ directory")
    
    # Initialize database
    try:
        db = Database()
        print("✅ Database initialized successfully")
        
        # Test database connection
        faculty = db.verify_faculty('F001', 'faculty123')
        if faculty:
            print("✅ Sample faculty account: F001 / faculty123")
        
        students = ['S001', 'S002', 'S003', 'S004']
        for student in students:
            test = db.verify_student(student, 'student123')
            if test:
                print(f"✅ Sample student account: {student} / student123")
        
        print("\n🎉 Setup completed successfully!")
        print("\n📋 Next steps:")
        print("1. Run: python run.py (for development)")
        print("2. Run: python run.py --production (for production)")
        print("3. Access: http://localhost:5000")
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")

if __name__ == '__main__':
    setup_system()