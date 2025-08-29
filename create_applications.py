#!/usr/bin/env python3
"""
Create more job applications for interview scheduling testing
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import MySQLdb
import MySQLdb.cursors
from datetime import date

def create_more_applications():
    """Create more job applications"""
    
    from app import app
    
    with app.app_context():
        from app import mysql
        
        try:
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            
            # Get candidates and jobs
            cur.execute("SELECT id, first_name, last_name FROM candidates LIMIT 8")
            candidates = cur.fetchall()
            
            cur.execute("SELECT id, position_title FROM job_positions LIMIT 6")
            jobs = cur.fetchall()
            
            print(f"Found {len(candidates)} candidates and {len(jobs)} jobs")
            
            # Create applications for different candidate-job combinations
            statuses = ['Applied', 'Under Review', 'Shortlisted']
            
            applications_created = 0
            for i, candidate in enumerate(candidates):
                for j, job in enumerate(jobs[:3]):  # Each candidate applies to max 3 jobs
                    if i + j < 8:  # Limit total applications
                        status = statuses[(i + j) % len(statuses)]
                        
                        # Check if application already exists
                        cur.execute("""
                            SELECT id FROM job_applications 
                            WHERE candidate_id = %s AND job_position_id = %s
                        """, (candidate['id'], job['id']))
                        
                        existing = cur.fetchone()
                        if not existing:
                            cur.execute("""
                                INSERT INTO job_applications (candidate_id, job_position_id, application_date, status)
                                VALUES (%s, %s, %s, %s)
                            """, (candidate['id'], job['id'], date.today(), status))
                            
                            print(f"Created: {candidate['first_name']} {candidate['last_name']} -> {job['position_title']} ({status})")
                            applications_created += 1
                        else:
                            print(f"Skipped: {candidate['first_name']} {candidate['last_name']} -> {job['position_title']} (exists)")
            
            mysql.connection.commit()
            print(f"\n{applications_created} new applications created!")
            
            # Show final count
            cur.execute("""
                SELECT COUNT(*) as count FROM job_applications 
                WHERE status IN ('Applied', 'Under Review', 'Shortlisted')
            """)
            ready_count = cur.fetchone()['count']
            print(f"Total applications ready for interview scheduling: {ready_count}")
                
            cur.close()
            
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == '__main__':
    create_more_applications()