#!/usr/bin/env python3
"""
Check current database structure and create proper fixes
"""

import MySQLdb

def check_and_fix_database():
    try:
        # Database connection
        db = MySQLdb.connect(
            host='localhost',
            user='root',
            password='gmkr',
            database='lumorange_db'
        )
        
        cursor = db.cursor()
        
        print("🔍 Checking current database structure...")
        
        # Check existing tables and columns
        tables = ['employees', 'departments', 'projects', 'clients', 'invoices', 'employee_projects', 'salaries', 'payroll_reports']
        
        for table in tables:
            print(f"\n📋 Table: {table}")
            try:
                cursor.execute(f"DESCRIBE {table}")
                columns = cursor.fetchall()
                existing_columns = [col[0] for col in columns]
                print(f"   Columns: {', '.join(existing_columns)}")
            except Exception as e:
                print(f"   ❌ Table doesn't exist: {e}")
        
        print("\n🔧 Applying missing column fixes...")
        
        # Safe column additions - only add if doesn't exist
        fixes = [
            # Employees table fixes
            ("employees", "first_name", "VARCHAR(50)"),
            ("employees", "last_name", "VARCHAR(50)"),
            ("employees", "status", "ENUM('active', 'inactive') DEFAULT 'active'"),
            
            # Projects table fixes  
            ("projects", "progress", "INT DEFAULT 0"),
            ("projects", "client_id", "INT"),
            ("projects", "end_date", "DATE"),
            
            # Invoices table fixes
            ("projects", "budget", "DECIMAL(15,2) DEFAULT 0"),
            ("invoices", "amount", "DECIMAL(10,2) DEFAULT 0"),
            ("invoices", "subtotal_amount", "DECIMAL(10,2) DEFAULT 0"),
            ("invoices", "project_id", "INT"),
            ("invoices", "notes", "TEXT"),
            
            # Employee projects fixes
            ("employee_projects", "assigned_date", "DATE DEFAULT (CURRENT_DATE)"),
            
            # Salaries fixes
            ("salaries", "allowances", "DECIMAL(10,2) DEFAULT 0"),
            ("salaries", "deductions", "DECIMAL(10,2) DEFAULT 0"),
        ]
        
        for table, column, definition in fixes:
            try:
                # Check if column exists
                cursor.execute(f"SHOW COLUMNS FROM {table} LIKE '{column}'")
                if not cursor.fetchone():
                    cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
                    print(f"✅ Added {table}.{column}")
                else:
                    print(f"⚪ {table}.{column} already exists")
            except Exception as e:
                print(f"⚠️ Could not add {table}.{column}: {str(e)[:50]}...")
        
        # Update existing data
        print("\n📊 Updating existing data...")
        
        updates = [
            # Split name into first_name and last_name if they exist
            """UPDATE employees 
             SET first_name = COALESCE(SUBSTRING_INDEX(name, ' ', 1), name),
                 last_name = CASE 
                     WHEN name LIKE '% %' THEN SUBSTRING_INDEX(name, ' ', -1)
                     ELSE ''
                 END 
             WHERE (first_name IS NULL OR first_name = '') AND name IS NOT NULL""",
             
            # Set default status
            "UPDATE employees SET status = 'active' WHERE status IS NULL",
            
            # Update invoices
            "UPDATE invoices SET amount = COALESCE(total_amount, 0) WHERE (amount IS NULL OR amount = 0) AND total_amount > 0",
            "UPDATE invoices SET subtotal_amount = COALESCE(amount, total_amount, 0) WHERE subtotal_amount IS NULL OR subtotal_amount = 0",
        ]
        
        for update_sql in updates:
            try:
                cursor.execute(update_sql)
                print("✅ Updated data")
            except Exception as e:
                print(f"⚠️ Update skipped: {str(e)[:50]}...")
        
        db.commit()
        cursor.close()
        db.close()
        
        print("\n🎉 Database structure check and fixes completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_and_fix_database()
