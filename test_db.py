from database import Database

# Test database connection
def test_database():
    try:
        db = Database('test_attendance.db')
        print("✅ Database initialized successfully")
        
        # Test faculty login
        faculty = db.verify_faculty('F001', 'faculty123')
        if faculty:
            print("✅ Faculty login works")
        else:
            print("❌ Faculty login failed")
        
        # Test student login
        student = db.verify_student('S001', 'student123')
        if student:
            print("✅ Student login works")
        else:
            print("❌ Student login failed")
            
    except Exception as e:
        print(f"❌ Database error: {e}")

if __name__ == '__main__':
    test_database()