#!/usr/bin/env python3
"""
Check database tables for recruitment data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import MySQLdb
import MySQLdb.cursors

def check_database_data():
    """Check what data exists in recruitment tables"""
    
    from app import app
    
    with app.app_context():
        from app import mysql
        
        try:
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            
            # Check candidates
            cur.execute("SELECT COUNT(*) as count FROM candidates")
            candidate_count = cur.fetchone()['count']
            print(f"Candidates: {candidate_count}")
            
            # Check job positions
            cur.execute("SELECT COUNT(*) as count FROM job_positions")
            job_count = cur.fetchone()['count']
            print(f"Job Positions: {job_count}")
            
            # Check job applications
            cur.execute("SELECT COUNT(*) as count FROM job_applications")
            app_count = cur.fetchone()['count']
            print(f"Job Applications: {app_count}")
            
            # Check interviews
            cur.execute("SELECT COUNT(*) as count FROM interviews")
            interview_count = cur.fetchone()['count']
            print(f"Interviews: {interview_count}")
            
            # If we have candidates and jobs but no applications, create some
            if candidate_count > 0 and job_count > 0 and app_count == 0:
                print("\nFound candidates and jobs but no applications. Creating sample applications...")
                
                # Get first few candidates and jobs
                cur.execute("SELECT id FROM candidates LIMIT 3")
                candidates = cur.fetchall()
                
                cur.execute("SELECT id FROM job_positions LIMIT 3")
                jobs = cur.fetchall()
                
                # Create applications
                for i, candidate in enumerate(candidates):
                    job = jobs[i % len(jobs)]
                    cur.execute("""
                        INSERT INTO job_applications (candidate_id, job_position_id, application_date, status)
                        VALUES (%s, %s, CURDATE(), %s)
                    """, (candidate['id'], job['id'], ['Applied', 'Under Review', 'Shortlisted'][i]))
                    print(f"Created application: Candidate {candidate['id']} -> Job {job['id']}")
                
                mysql.connection.commit()
                print("Sample applications created!")
                
            cur.close()
            
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == '__main__':
    check_database_data()