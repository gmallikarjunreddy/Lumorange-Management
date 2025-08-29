#!/usr/bin/env python3
"""
Check recent interviews with generated interview codes
"""

import MySQLdb
import os

def check_interview_codes():
    """Check the latest interviews and their codes"""
    try:
        # Database connection
        db = MySQLdb.connect(
            host='localhost',
            user='root',
            passwd='',
            db='lumorange_recruitment'
        )
        cursor = db.cursor(MySQLdb.cursors.DictCursor)
        
        # Get recent interviews with their codes
        query = """
        SELECT i.id, i.interview_code, i.status, i.scheduled_date, i.scheduled_time,
               c.full_name as candidate_name, jp.job_title
        FROM interviews i
        JOIN job_applications ja ON i.application_id = ja.id
        JOIN candidates c ON ja.candidate_id = c.id
        JOIN job_positions jp ON ja.job_position_id = jp.id
        ORDER BY i.created_at DESC
        LIMIT 10
        """
        
        cursor.execute(query)
        interviews = cursor.fetchall()
        
        print("🔍 Recent Interviews with Generated Codes:")
        print("=" * 80)
        
        if interviews:
            for interview in interviews:
                print(f"ID: {interview['id']:2} | Code: {interview['interview_code']} | "
                      f"Status: {interview['status']:10} | Date: {interview['scheduled_date']} "
                      f"{interview['scheduled_time']} | "
                      f"Candidate: {interview['candidate_name']} | Job: {interview['job_title']}")
        else:
            print("No interviews found in database.")
        
        cursor.close()
        db.close()
        
        return len(interviews)
        
    except Exception as e:
        print(f"❌ Database error: {str(e)}")
        return 0

if __name__ == "__main__":
    print("🧪 Checking Interview Codes in Database")
    print("=" * 80)
    
    count = check_interview_codes()
    
    print("\n" + "=" * 80)
    print(f"📊 Found {count} interviews in database")
    
    if count > 0:
        print("✅ Interview codes are being generated successfully!")
    else:
        print("ℹ️  No interviews found. Create a new interview to test the code generation.")