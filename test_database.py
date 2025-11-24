from database import Database

def test_database():
    try:
        db = Database('test.db')
        print("✅ Database class created successfully")
        
        # Test attendance retrieval
        attendance = db.get_student_attendance('S001')
        print(f"✅ Attendance records for S001: {len(attendance)}")
        
        # Test student name retrieval
        name = db.get_student_name('S001')
        print(f"✅ Student name: {name}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    test_database()