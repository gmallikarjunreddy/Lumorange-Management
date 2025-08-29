#!/usr/bin/env python3
"""
Test script to check job applications for interview scheduling
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import MySQLdb
import MySQLdb.cursors

def test_applications():
    """Test job applications data for dropdown"""
    
    from app import app
    
    with app.app_context():
        from app import mysql
        
        try:
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            
            # Test the exact query from the schedule_interview route
            cur.execute("""
                SELECT ja.id, 
                       CONCAT(c.first_name, ' ', c.last_name) as candidate_name,
                       c.email as candidate_email,
                       jp.position_title,
                       COALESCE(d.name, 'No Department') as department_name
                FROM job_applications ja
                JOIN candidates c ON ja.candidate_id = c.id
                JOIN job_positions jp ON ja.job_position_id = jp.id
                LEFT JOIN departments d ON jp.department_id = d.id
                WHERE ja.status IN ('Applied', 'Under Review', 'Interview Scheduled')
                ORDER BY ja.application_date DESC
                LIMIT 5
            """)
            
            applications = cur.fetchall()
            print(f"Found {len(applications)} applications for interview scheduling:")
            
            if applications:
                for app in applications:
                    print(f"  - ID: {app['id']}")
                    print(f"    Candidate: {app['candidate_name']}")
                    print(f"    Email: {app['candidate_email']}")  
                    print(f"    Position: {app['position_title']}")
                    print(f"    Department: {app['department_name']}")
                    print("    ---")
            else:
                print("  No applications found with status: Applied, Under Review, or Interview Scheduled")
                
                # Check all applications
                cur.execute("SELECT ja.status, COUNT(*) as count FROM job_applications ja GROUP BY ja.status")
                statuses = cur.fetchall()
                print("\nAll application statuses:")
                for status in statuses:
                    print(f"  - {status['status']}: {status['count']} applications")
                    
            cur.close()
            
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == '__main__':
    test_applications()