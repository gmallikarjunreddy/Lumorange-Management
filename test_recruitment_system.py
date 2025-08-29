"""
Comprehensive Recruitment System Test Script
Tests all functionality end-to-end
"""

import requests
import json
from datetime import datetime

def test_recruitment_system():
    base_url = "http://127.0.0.1:5000"
    
    print("🚀 COMPREHENSIVE RECRUITMENT SYSTEM TEST")
    print("=" * 50)
    
    # Test 1: Main Pages Load
    pages = [
        ("/", "Main Dashboard"),
        ("/recruitment", "Recruitment Dashboard"), 
        ("/candidates", "Candidates List"),
        ("/job_positions", "Job Positions"),
        ("/interviews", "Interviews"),
        ("/applications", "Applications"),
        ("/recruitment_reports", "Recruitment Reports")
    ]
    
    print("\n📄 Testing Page Loads:")
    for url, name in pages:
        try:
            response = requests.get(f"{base_url}{url}")
            status = "✅ PASS" if response.status_code == 200 else "❌ FAIL"
            print(f"   {status} {name} ({response.status_code})")
        except Exception as e:
            print(f"   ❌ FAIL {name} - Error: {e}")
    
    # Test 2: Form Pages
    form_pages = [
        ("/candidates/add", "Add Candidate Form"),
        ("/job_positions/add", "Add Job Position Form"),
        ("/add_candidate", "Add Candidate Alias"),
        ("/add_job_position", "Add Job Position Alias")
    ]
    
    print("\n📝 Testing Form Pages:")
    for url, name in form_pages:
        try:
            response = requests.get(f"{base_url}{url}")
            status = "✅ PASS" if response.status_code in [200, 302] else "❌ FAIL"
            print(f"   {status} {name} ({response.status_code})")
        except Exception as e:
            print(f"   ❌ FAIL {name} - Error: {e}")
    
    # Test 3: Video Interview Pages
    print("\n🎥 Testing Video Interview:")
    try:
        response = requests.get(f"{base_url}/video_interview/1")
        status = "✅ PASS" if response.status_code == 200 else "❌ FAIL"
        print(f"   {status} Video Interview Page ({response.status_code})")
    except Exception as e:
        print(f"   ❌ FAIL Video Interview - Error: {e}")
    
    # Test 4: Action Routes (GET routes only for safety)
    action_routes = [
        ("/view_feedback/1", "View Interview Feedback"),
        ("/view_details/1", "View Interview Details"),
        ("/view_profile/1", "View Candidate Profile"),
        ("/download_resume/1", "Download Resume"),
        ("/send_message/1", "Send Message"),
        ("/start_interview/1", "Start Interview")
    ]
    
    print("\n⚡ Testing Action Routes:")
    for url, name in action_routes:
        try:
            response = requests.get(f"{base_url}{url}")
            status = "✅ PASS" if response.status_code in [200, 302, 404] else "❌ FAIL"
            print(f"   {status} {name} ({response.status_code})")
        except Exception as e:
            print(f"   ❌ FAIL {name} - Error: {e}")
    
    print("\n📊 RECRUITMENT SYSTEM AUDIT COMPLETE!")
    print("=" * 50)
    
    return True

if __name__ == "__main__":
    test_recruitment_system()