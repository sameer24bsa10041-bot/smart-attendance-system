# my_face_utils.py - CORRECTED VERSION
import face_recognition
import cv2
import numpy as np
import sqlite3
from datetime import datetime
import os
import pickle

class FaceRecognition:
    def __init__(self):
        self.face_encodings = {}
        self.encoding_file = 'face_encodings.pkl'
        self.load_encodings()
    
    def load_encodings(self):
        """Load face encodings from file"""
        try:
            if os.path.exists(self.encoding_file):
                with open(self.encoding_file, 'rb') as f:
                    self.face_encodings = pickle.load(f)
                print(f"✅ Loaded {len(self.face_encodings)} face encodings")
            else:
                print("ℹ️ No existing face encodings file found")
        except Exception as e:
            print(f"❌ Error loading encodings: {e}")
            self.face_encodings = {}
    
    def save_encodings(self):
        """Save face encodings to file"""
        try:
            with open(self.encoding_file, 'wb') as f:
                pickle.dump(self.face_encodings, f)
            print(f"💾 Saved {len(self.face_encodings)} face encodings")
        except Exception as e:
            print(f"❌ Error saving encodings: {e}")
    
    def register_face(self, image, user_id, user_name, image_index=0):
        """
        CORRECTED: Register a new face
        """
        try:
            print(f"🔍 Registering face image {image_index + 1} for {user_name} ({user_id})")
            
            # Convert BGR to RGB (IMPORTANT: face_recognition uses RGB)
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # ✅ CORRECT: Call face_locations from face_recognition module
            face_locations = face_recognition.face_locations(rgb_image)
            print(f"✅ Found {len(face_locations)} face(s)")
            
            if len(face_locations) == 0:
                print("❌ No face detected in the image")
                return False
            
            # ✅ CORRECT: Get face encodings
            face_encodings = face_recognition.face_encodings(rgb_image, face_locations)
            
            if len(face_encodings) == 0:
                print("❌ Could not encode face")
                return False
            
            # Store the encoding
            encoding_key = f"{user_id}_{image_index}"
            self.face_encodings[encoding_key] = {
                'encoding': face_encodings[0],
                'name': user_name,
                'user_id': user_id,
                'timestamp': datetime.now()
            }
            
            # Save to database
            self._save_to_database(user_id, user_name, face_encodings[0])
            
            # Save to file
            self.save_encodings()
            
            print(f"🎉 Face successfully registered for {user_name}")
            return True
            
        except Exception as e:
            print(f"❌ Error in register_face: {e}")
            return False
    
    def _save_to_database(self, user_id, user_name, face_encoding):
        """Save face encoding to database"""
        try:
            conn = sqlite3.connect('attendance.db')
            cursor = conn.cursor()
            
            # Convert numpy array to string
            encoding_str = str(face_encoding.tolist())
            
            # Update student record
            cursor.execute('''
                UPDATE students SET face_encoding = ?, registration_date = datetime('now')
                WHERE id = ?
            ''', (encoding_str, user_id))
            
            conn.commit()
            conn.close()
            print(f"💾 Saved face data to database for {user_name}")
            
        except Exception as e:
            print(f"❌ Database save error: {e}")
    
    def recognize_face(self, image):
        """
        Recognize a face in the image
        """
        try:
            # Convert BGR to RGB
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Detect faces using face_recognition module
            face_locations = face_recognition.face_locations(rgb_image)
            
            if len(face_locations) == 0:
                return None, 0
            
            # Get encoding
            face_encodings = face_recognition.face_encodings(rgb_image, face_locations)
            
            if len(face_encodings) == 0:
                return None, 0
            
            unknown_encoding = face_encodings[0]
            
            # Compare with known faces
            best_match = None
            best_distance = 1.0
            
            for key, data in self.face_encodings.items():
                known_encoding = data['encoding']
                distance = face_recognition.face_distance([known_encoding], unknown_encoding)[0]
                
                if distance < best_distance:
                    best_distance = distance
                    best_match = data
            
            confidence = 1 - best_distance
            
            if best_match and confidence > 0.6:
                return best_match['user_id'], confidence
            else:
                return None, confidence
                
        except Exception as e:
            print(f"❌ Recognition error: {e}")
            return None, 0
    
    def get_user_encodings_count(self, user_id):
        """Count registered face encodings for a user"""
        count = 0
        for key in self.face_encodings.keys():
            if key.startswith(f"{user_id}_"):
                count += 1
        return count
    
    def remove_user_faces(self, user_id):
        """Remove all face encodings for a user"""
        keys_to_remove = [key for key in self.face_encodings.keys() if key.startswith(f"{user_id}_")]
        for key in keys_to_remove:
            del self.face_encodings[key]
        self.save_encodings()
        print(f"🗑️ Removed {len(keys_to_remove)} face encodings for user {user_id}")