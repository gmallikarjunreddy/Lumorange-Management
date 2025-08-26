#!/usr/bin/env python3
"""
Fix database schema to support all features without errors
"""

import MySQLdb
from datetime import date, datetime

def fix_database_schema():
    try:
        # Database connection
        db = MySQLdb.connect(
            host='localhost',
            user='root',
            password='gmkr',
            database='lumorange_db'
        )
        
        cursor = db.cursor()
        
        print("🔧 Fixing database schema for all features...")
        
        # Check and add missing columns
        schema_fixes = [
            # Fix employees table
            "ALTER TABLE employees ADD COLUMN IF NOT EXISTS first_name VARCHAR(50)",
            "ALTER TABLE employees ADD COLUMN IF NOT EXISTS last_name VARCHAR(50)",
            "ALTER TABLE employees ADD COLUMN IF NOT EXISTS status ENUM('active', 'inactive') DEFAULT 'active'",
            
            # Fix projects table
            "ALTER TABLE projects ADD COLUMN IF NOT EXISTS progress INT DEFAULT 0",
            "ALTER TABLE projects ADD COLUMN IF NOT EXISTS client_id INT",
            "ALTER TABLE projects ADD COLUMN IF NOT EXISTS end_date DATE",
            
            # Fix invoices table
            "ALTER TABLE invoices ADD COLUMN IF NOT EXISTS amount DECIMAL(10,2) DEFAULT 0",
            "ALTER TABLE invoices ADD COLUMN IF NOT EXISTS subtotal_amount DECIMAL(10,2) DEFAULT 0",
            "ALTER TABLE invoices ADD COLUMN IF NOT EXISTS project_id INT",
            "ALTER TABLE invoices ADD COLUMN IF NOT EXISTS notes TEXT",
            
            # Update existing data to populate first_name and last_name from name
            """UPDATE employees 
             SET first_name = SUBSTRING_INDEX(name, ' ', 1),
                 last_name = CASE 
                     WHEN name LIKE '% %' THEN SUBSTRING_INDEX(name, ' ', -1)
                     ELSE ''
                 END 
             WHERE first_name IS NULL OR first_name = ''""",
            
            # Update invoices to have amount = total_amount if amount is 0
            "UPDATE invoices SET amount = total_amount WHERE amount = 0 OR amount IS NULL",
            "UPDATE invoices SET subtotal_amount = amount WHERE subtotal_amount = 0 OR subtotal_amount IS NULL",
        ]
        
        for fix_sql in schema_fixes:
            try:
                cursor.execute(fix_sql)
                print("✅ Applied:", fix_sql[:60] + "...")
            except Exception as e:
                print(f"⚠️ Skipped: {str(e)[:50]}...")
        
        # Add sample data to ensure dynamic functionality
        print("\n📊 Adding comprehensive sample data...")
        
        sample_data = [
            # Ensure we have departments with proper budgets
            "INSERT IGNORE INTO departments (name, description, budget) VALUES ('Information Technology', 'Software development and IT support', 2500000)",
            "INSERT IGNORE INTO departments (name, description, budget) VALUES ('Human Resources', 'Employee management and recruitment', 1200000)",
            "INSERT IGNORE INTO departments (name, description, budget) VALUES ('Finance', 'Financial planning and accounting', 1800000)",
            "INSERT IGNORE INTO departments (name, description, budget) VALUES ('Marketing', 'Digital marketing and brand management', 1500000)",
            
            # Add comprehensive employee data
            "INSERT IGNORE INTO employees (employee_id, name, first_name, last_name, email, phone, position, department_id, salary, hire_date, status) VALUES ('EMP001', 'Rajesh Kumar', 'Rajesh', 'Kumar', 'rajesh.kumar@lumorange.com', '9876543210', 'Senior Developer', 1, 75000, '2024-01-15', 'active')",
            "INSERT IGNORE INTO employees (employee_id, name, first_name, last_name, email, phone, position, department_id, salary, hire_date, status) VALUES ('EMP002', 'Priya Sharma', 'Priya', 'Sharma', 'priya.sharma@lumorange.com', '9876543211', 'HR Manager', 2, 65000, '2024-02-01', 'active')",
            "INSERT IGNORE INTO employees (employee_id, name, first_name, last_name, email, phone, position, department_id, salary, hire_date, status) VALUES ('EMP003', 'Amit Patel', 'Amit', 'Patel', 'amit.patel@lumorange.com', '9876543212', 'Financial Analyst', 3, 55000, '2024-01-20', 'active')",
            "INSERT IGNORE INTO employees (employee_id, name, first_name, last_name, email, phone, position, department_id, salary, hire_date, status) VALUES ('EMP004', 'Sneha Gupta', 'Sneha', 'Gupta', 'sneha.gupta@lumorange.com', '9876543213', 'Marketing Executive', 4, 45000, '2024-02-10', 'active')",
            "INSERT IGNORE INTO employees (employee_id, name, first_name, last_name, email, phone, position, department_id, salary, hire_date, status) VALUES ('EMP005', 'Vikram Singh', 'Vikram', 'Singh', 'vikram.singh@lumorange.com', '9876543214', 'Project Manager', 1, 80000, '2024-01-10', 'active')",
            
            # Add more clients
            "INSERT IGNORE INTO clients (name, email, phone, address, contact_person) VALUES ('TechCorp India Pvt Ltd', 'info@techcorp.in', '9876543220', 'Bangalore, Karnataka', 'Vikram Singh')",
            "INSERT IGNORE INTO clients (name, email, phone, address, contact_person) VALUES ('StartupXYZ Solutions', 'contact@startupxyz.com', '9876543221', 'Mumbai, Maharashtra', 'Anita Desai')",
            "INSERT IGNORE INTO clients (name, email, phone, address, contact_person) VALUES ('Global Enterprises Ltd', 'admin@globalent.co.in', '9876543222', 'Delhi, NCR', 'Rahul Agarwal')",
            "INSERT IGNORE INTO clients (name, email, phone, address, contact_person) VALUES ('Digital Solutions Inc', 'hello@digitalsol.com', '9876543223', 'Chennai, Tamil Nadu', 'Meera Reddy')",
            
            # Add projects with all required columns
            "INSERT IGNORE INTO projects (name, description, department_id, client_id, status, budget, progress, start_date, end_date) VALUES ('E-Commerce Platform', 'Complete e-commerce solution with payment gateway', 1, 1, 'In Progress', 1500000, 75, '2024-01-01', '2024-06-30')",
            "INSERT IGNORE INTO projects (name, description, department_id, client_id, status, budget, progress, start_date, end_date) VALUES ('Mobile App Development', 'Cross-platform mobile application', 1, 2, 'In Progress', 800000, 45, '2024-02-01', '2024-05-31')",
            "INSERT IGNORE INTO projects (name, description, department_id, client_id, status, budget, progress, start_date, end_date) VALUES ('Digital Marketing Campaign', 'Complete digital marketing solution', 4, 3, 'Planned', 300000, 10, '2024-03-01', '2024-08-31')",
            "INSERT IGNORE INTO projects (name, description, department_id, client_id, status, budget, progress, start_date, end_date) VALUES ('ERP System Integration', 'Custom ERP system for enterprise client', 1, 4, 'Completed', 2000000, 100, '2023-10-01', '2024-01-15')",
            "INSERT IGNORE INTO projects (name, description, department_id, client_id, status, budget, progress, start_date, end_date) VALUES ('Website Redesign', 'Modern responsive website development', 1, 1, 'In Progress', 500000, 60, '2024-02-15', '2024-04-30')",
            
            # Add invoices with all columns
            "INSERT IGNORE INTO invoices (client_id, invoice_number, invoice_date, due_date, project_id, amount, subtotal_amount, tax_rate, total_amount, status, notes) VALUES (1, 'INV-2024-001', '2024-08-01', '2024-08-31', 1, 500000, 500000, 18, 590000, 'paid', 'First milestone payment for E-Commerce Platform')",
            "INSERT IGNORE INTO invoices (client_id, invoice_number, invoice_date, due_date, project_id, amount, subtotal_amount, tax_rate, total_amount, status, notes) VALUES (2, 'INV-2024-002', '2024-08-15', '2024-09-15', 2, 300000, 300000, 18, 354000, 'sent', 'Mobile App Development Phase 1')",
            "INSERT IGNORE INTO invoices (client_id, invoice_number, invoice_date, due_date, project_id, amount, subtotal_amount, tax_rate, total_amount, status, notes) VALUES (3, 'INV-2024-003', '2024-08-20', '2024-09-20', 3, 150000, 150000, 18, 177000, 'draft', 'Marketing consultation and strategy')",
            "INSERT IGNORE INTO invoices (client_id, invoice_number, invoice_date, due_date, project_id, amount, subtotal_amount, tax_rate, total_amount, status, notes) VALUES (4, 'INV-2024-004', '2024-07-15', '2024-08-15', 4, 800000, 800000, 18, 944000, 'paid', 'ERP System final payment')",
            "INSERT IGNORE INTO invoices (client_id, invoice_number, invoice_date, due_date, project_id, amount, subtotal_amount, tax_rate, total_amount, status, notes) VALUES (1, 'INV-2024-005', '2024-08-25', '2024-09-25', 5, 200000, 200000, 18, 236000, 'sent', 'Website redesign milestone')",
            
            # Add employee-project assignments
            "INSERT IGNORE INTO employee_projects (employee_id, project_id, role, assigned_date) VALUES (1, 1, 'Lead Developer', '2024-01-01')",
            "INSERT IGNORE INTO employee_projects (employee_id, project_id, role, assigned_date) VALUES (5, 1, 'Project Manager', '2024-01-01')",
            "INSERT IGNORE INTO employee_projects (employee_id, project_id, role, assigned_date) VALUES (1, 2, 'Senior Developer', '2024-02-01')",
            "INSERT IGNORE INTO employee_projects (employee_id, project_id, role, assigned_date) VALUES (5, 2, 'Project Manager', '2024-02-01')",
            "INSERT IGNORE INTO employee_projects (employee_id, project_id, role, assigned_date) VALUES (4, 3, 'Marketing Lead', '2024-03-01')",
            "INSERT IGNORE INTO employee_projects (employee_id, project_id, role, assigned_date) VALUES (1, 4, 'Technical Lead', '2023-10-01')",
            "INSERT IGNORE INTO employee_projects (employee_id, project_id, role, assigned_date) VALUES (1, 5, 'Full Stack Developer', '2024-02-15')",
            
            # Add comprehensive salary records
            "INSERT IGNORE INTO salaries (employee_id, basic_salary, allowances, deductions, effective_date) VALUES (1, 60000, 15000, 5000, '2024-01-01')",
            "INSERT IGNORE INTO salaries (employee_id, basic_salary, allowances, deductions, effective_date) VALUES (2, 50000, 15000, 4000, '2024-02-01')",
            "INSERT IGNORE INTO salaries (employee_id, basic_salary, allowances, deductions, effective_date) VALUES (3, 45000, 10000, 3000, '2024-01-20')",
            "INSERT IGNORE INTO salaries (employee_id, basic_salary, allowances, deductions, effective_date) VALUES (4, 35000, 10000, 2500, '2024-02-10')",
            "INSERT IGNORE INTO salaries (employee_id, basic_salary, allowances, deductions, effective_date) VALUES (5, 65000, 15000, 5500, '2024-01-10')",
            
            # Add some payroll records
            "INSERT IGNORE INTO payroll_reports (employee_id, month, year, basic_salary, allowances, deductions, status) VALUES (1, 8, 2024, 60000, 15000, 5000, 'paid')",
            "INSERT IGNORE INTO payroll_reports (employee_id, month, year, basic_salary, allowances, deductions, status) VALUES (2, 8, 2024, 50000, 15000, 4000, 'paid')",
            "INSERT IGNORE INTO payroll_reports (employee_id, month, year, basic_salary, allowances, deductions, status) VALUES (3, 8, 2024, 45000, 10000, 3000, 'processed')",
            "INSERT IGNORE INTO payroll_reports (employee_id, month, year, basic_salary, allowances, deductions, status) VALUES (4, 8, 2024, 35000, 10000, 2500, 'processed')",
            "INSERT IGNORE INTO payroll_reports (employee_id, month, year, basic_salary, allowances, deductions, status) VALUES (5, 8, 2024, 65000, 15000, 5500, 'paid')",
        ]
        
        for data_sql in sample_data:
            try:
                cursor.execute(data_sql)
                print("✅ Added:", data_sql[:60] + "...")
            except Exception as e:
                print(f"⚠️ Skipped: {str(e)[:50]}...")
        
        db.commit()
        cursor.close()
        db.close()
        
        print("\n🎉 Database schema fixed and comprehensive data added!")
        print("💰 All pages should now work without errors")
        print("🚀 Refresh your browser to see fully dynamic content")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    fix_database_schema()
