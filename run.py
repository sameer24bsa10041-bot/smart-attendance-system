#!/usr/bin/env python3
import os
import sys
from app import app, db

def main():
    # Check if running in production
    if len(sys.argv) > 1 and sys.argv[1] == '--production':
        os.environ['FLASK_ENV'] = 'production'
        print("🚀 Starting in PRODUCTION mode...")
    else:
        print("🔧 Starting in DEVELOPMENT mode...")
    
    # Optimize database
    db.optimize_database()
    
    # Start the application
    app.run(host='0.0.0.0', port=5000, debug=(os.environ.get('FLASK_ENV') != 'production'))

if __name__ == '__main__':
    main()