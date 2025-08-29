#!/usr/bin/env python3
"""
Update some job applications to make them available for interview scheduling
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import MySQLdb
import MySQLdb.cursors

def update_applications_for_interviews():
    """Update some applications to be available for interview scheduling"""
    
    from app import app
    
    with app.app_context():
        from app import mysql
        
        try:
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            
            # First, check current applications
            cur.execute("SELECT id, status FROM job_applications LIMIT 5")
            applications = cur.fetchall()
            print("Current applications:")
            for app in applications:
                print(f"  - Application ID {app['id']}: {app['status']}")
            
            if applications:
                # Update the first few applications to have interview-ready statuses
                app_ids_to_update = [app['id'] for app in applications[:3]]
                
                statuses = ['Applied', 'Under Review', 'Shortlisted']
                
                for i, app_id in enumerate(app_ids_to_update):
                    status = statuses[i % len(statuses)]
                    cur.execute("UPDATE job_applications SET status = %s WHERE id = %s", (status, app_id))
                    print(f"Updated application {app_id} to status: {status}")
                
                mysql.connection.commit()
                print("Applications updated successfully!")
                
                # Verify the updates
                print("\nVerifying updates...")
                cur.execute("""
                    SELECT ja.id, ja.status,
                           CONCAT(c.first_name, ' ', c.last_name) as candidate_name,
                           jp.position_title
                    FROM job_applications ja
                    JOIN candidates c ON ja.candidate_id = c.id
                    JOIN job_positions jp ON ja.job_position_id = jp.id
                    WHERE ja.status IN ('Applied', 'Under Review', 'Shortlisted')
                    LIMIT 5
                """)
                
                updated_apps = cur.fetchall()
                print(f"Found {len(updated_apps)} applications ready for interview scheduling:")
                for app in updated_apps:
                    print(f"  - {app['candidate_name']} for {app['position_title']} (Status: {app['status']})")
                    
            else:
                print("No applications found to update")
                
            cur.close()
            
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == '__main__':
    update_applications_for_interviews()