#!/usr/bin/env python3
"""
Test departments functionality and check for errors
"""

import MySQLdb

def test_departments():
    try:
        # Database connection
        db = MySQLdb.connect(
            host='localhost',
            user='root',
            password='gmkr',
            database='lumorange_db'
        )
        
        cursor = db.cursor()
        
        print("🔍 Testing departments functionality...")
        
        # Test the departments query
        print("\n1. Testing departments query...")
        cursor.execute("""SELECT d.id, d.name, d.description, COALESCE(d.budget, 0) as budget, 
                          COUNT(e.id) as employee_count
                          FROM departments d 
                          LEFT JOIN employees e ON d.id = e.department_id AND e.status = 'active'
                          GROUP BY d.id, d.name, d.description, d.budget
                          ORDER BY d.name""")
        departments = cursor.fetchall()
        
        print(f"✅ Found {len(departments)} departments")
        
        for dept in departments:
            print(f"   - {dept[1]}: Budget={dept[3]}, Employees={dept[4]}")
            
        # Test calculations
        print("\n2. Testing calculations...")
        total_budget = sum(dept[3] or 0 for dept in departments)
        total_employees = sum(dept[4] or 0 for dept in departments)
        avg_budget = total_budget / len(departments) if departments else 0
        
        print(f"✅ Total Budget: {total_budget}")
        print(f"✅ Total Employees: {total_employees}")
        print(f"✅ Average Budget: {avg_budget}")
        
        # Test department structure
        print("\n3. Checking department table structure...")
        cursor.execute("DESCRIBE departments")
        columns = cursor.fetchall()
        print("   Columns:", [col[0] for col in columns])
        
        cursor.close()
        db.close()
        
        print("\n🎉 Departments functionality test completed successfully!")
        print("🚀 All department queries working properly")
        
    except Exception as e:
        print(f"❌ Error in departments test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_departments()
