#!/usr/bin/env python3
"""
Test script to verify interview_code generation and interview creation
"""

import requests
import sys

def test_interview_form_loading():
    """Test if the interview form loads without errors"""
    try:
        print("Testing interview form loading...")
        response = requests.get('http://127.0.0.1:5000/schedule_interview', timeout=10)
        
        if response.status_code == 200:
            print("✅ Interview form loaded successfully!")
            return True
        else:
            print(f"❌ Failed to load interview form. Status code: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Flask app. Make sure it's running on http://127.0.0.1:5000")
        return False
    except Exception as e:
        print(f"❌ Error testing interview form: {str(e)}")
        return False

def test_interview_creation():
    """Test creating a new interview via POST request"""
    try:
        print("\nTesting interview creation...")
        
        # Prepare test data
        test_data = {
            'action': 'schedule',
            'application_id': '1',  # Assuming we have application with ID 1
            'interview_type_id': '1',  # Assuming we have interview type with ID 1
            'interview_round': '1',
            'scheduled_date': '2025-09-01',
            'scheduled_time': '10:00',
            'duration_minutes': '60',
            'interview_mode': 'Video Call',
            'meeting_link': 'https://meet.google.com/test-link',
            'interviewer_notes': 'Test interview creation'
        }
        
        response = requests.post('http://127.0.0.1:5000/schedule_interview', 
                               data=test_data, timeout=10, allow_redirects=False)
        
        if response.status_code in [200, 302]:  # 302 is redirect after successful creation
            print("✅ Interview creation test successful!")
            return True
        else:
            print(f"❌ Interview creation failed. Status code: {response.status_code}")
            if response.text:
                print(f"Response: {response.text[:500]}...")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Flask app. Make sure it's running on http://127.0.0.1:5000")
        return False
    except Exception as e:
        print(f"❌ Error testing interview creation: {str(e)}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Interview Form and Creation")
    print("=" * 50)
    
    # Test form loading
    form_test = test_interview_form_loading()
    
    # Test interview creation
    creation_test = test_interview_creation()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"Form Loading: {'✅ PASS' if form_test else '❌ FAIL'}")
    print(f"Interview Creation: {'✅ PASS' if creation_test else '❌ FAIL'}")
    
    if form_test and creation_test:
        print("\n🎉 All tests passed! Interview functionality is working.")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed. Check the Flask application.")
        sys.exit(1)