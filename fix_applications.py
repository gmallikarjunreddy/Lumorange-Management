#!/usr/bin/env python3
"""
Update job application statuses to make them available for interview scheduling
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import MySQLdb
import MySQLdb.cursors

def create_interview_ready_applications():
    """Create applications that are ready for interview scheduling"""
    
    from app import app
    
    with app.app_context():
        from app import mysql
        
        try:
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            
            # Check what applications we have
            cur.execute("""
                SELECT ja.id, ja.status,
                       CONCAT(c.first_name, ' ', c.last_name) as candidate_name,
                       jp.position_title
                FROM job_applications ja
                JOIN candidates c ON ja.candidate_id = c.id
                JOIN job_positions jp ON ja.job_position_id = jp.id
            """)
            
            all_applications = cur.fetchall()
            print(f"Total applications: {len(all_applications)}")
            
            for app in all_applications:
                print(f"  - {app['candidate_name']} for {app['position_title']} (Status: {app['status']})")
            
            # Update some applications to be interview-ready
            interview_statuses = ['Applied', 'Under Review', 'Shortlisted']
            
            for i, app in enumerate(all_applications[:5]):  # Update first 5 applications
                new_status = interview_statuses[i % len(interview_statuses)]
                cur.execute("UPDATE job_applications SET status = %s WHERE id = %s", (new_status, app['id']))
                print(f"Updated application {app['id']} to status: {new_status}")
            
            mysql.connection.commit()
            print("\nApplications updated successfully!")
            
            # Verify
            cur.execute("""
                SELECT ja.id, ja.status,
                       CONCAT(c.first_name, ' ', c.last_name) as candidate_name,
                       jp.position_title
                FROM job_applications ja
                JOIN candidates c ON ja.candidate_id = c.id
                JOIN job_positions jp ON ja.job_position_id = jp.id
                WHERE ja.status IN ('Applied', 'Under Review', 'Shortlisted')
            """)
            
            ready_applications = cur.fetchall()
            print(f"\nApplications ready for interview scheduling: {len(ready_applications)}")
            for app in ready_applications:
                print(f"  - {app['candidate_name']} for {app['position_title']} (Status: {app['status']})")
                
            cur.close()
            
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == '__main__':
    create_interview_ready_applications()