#!/usr/bin/env python3
"""
Test script to verify deletion functionality in the recruitment system
"""

import MySQLdb
import MySQLdb.cursors
from flask_mysqldb import MySQL
from app import app
import sys

def test_deletion_functionality():
    """Test various deletion scenarios"""
    
    with app.app_context():
        from app import mysql
        
        try:
            # Test database connection
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            print("✅ Database connection successful")
            
            # Check candidates and their relationships
            cur.execute("""
                SELECT c.id, c.first_name, c.last_name,
                       COUNT(ja.id) as application_count,
                       COUNT(i.id) as interview_count
                FROM candidates c
                LEFT JOIN job_applications ja ON c.id = ja.candidate_id
                LEFT JOIN interviews i ON ja.id = i.application_id
                GROUP BY c.id
                LIMIT 10
            """)
            
            candidates = cur.fetchall()
            print(f"\n📊 Found {len(candidates)} candidates:")
            
            for candidate in candidates:
                print(f"  • ID: {candidate['id']}, Name: {candidate['first_name']} {candidate['last_name']}")
                print(f"    Applications: {candidate['application_count']}, Interviews: {candidate['interview_count']}")
            
            # Check for orphaned records
            print("\n🔍 Checking for orphaned records...")
            
            # Check for applications without candidates
            cur.execute("""
                SELECT COUNT(*) as orphaned_applications 
                FROM job_applications ja 
                LEFT JOIN candidates c ON ja.candidate_id = c.id 
                WHERE c.id IS NULL
            """)
            orphaned_apps = cur.fetchone()['orphaned_applications']
            
            # Check for interviews without applications
            cur.execute("""
                SELECT COUNT(*) as orphaned_interviews 
                FROM interviews i 
                LEFT JOIN job_applications ja ON i.application_id = ja.id 
                WHERE ja.id IS NULL
            """)
            orphaned_interviews = cur.fetchone()['orphaned_interviews']
            
            print(f"  • Orphaned Applications: {orphaned_apps}")
            print(f"  • Orphaned Interviews: {orphaned_interviews}")
            
            # Check foreign key constraints
            print("\n🔗 Checking foreign key constraints...")
            cur.execute("SHOW CREATE TABLE job_applications")
            create_sql = cur.fetchone()['Create Table']
            
            if 'ON DELETE CASCADE' in create_sql:
                print("  ✅ job_applications has CASCADE delete constraints")
            else:
                print("  ⚠️  job_applications missing CASCADE delete constraints")
            
            cur.execute("SHOW CREATE TABLE interviews")
            create_sql = cur.fetchone()['Create Table']
            
            if 'ON DELETE CASCADE' in create_sql:
                print("  ✅ interviews has CASCADE delete constraints")
            else:
                print("  ⚠️  interviews missing CASCADE delete constraints")
            
            cur.close()
            print("\n✅ Deletion functionality test completed")
            
        except Exception as e:
            print(f"❌ Error during deletion test: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    test_deletion_functionality()