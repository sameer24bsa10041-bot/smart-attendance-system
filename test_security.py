from database import Database
from werkzeug.security import check_password_hash

def test_security():
    db = Database('test_secure.db')
    
    # Test faculty login
    faculty = db.verify_faculty('F001', 'faculty123')
    print(f"Faculty login: {'SUCCESS' if faculty else 'FAILED'}")
    
    # Test student login
    student = db.verify_student('S001', 'student123')
    print(f"Student login: {'SUCCESS' if student else 'FAILED'}")
    
    # Test wrong password
    wrong = db.verify_faculty('F001', 'wrongpassword')
    print(f"Wrong password: {'FAILED' if not wrong else 'SECURITY BREACH!'}")
    
    print("✅ Security test completed")

if __name__ == '__main__':
    test_security()