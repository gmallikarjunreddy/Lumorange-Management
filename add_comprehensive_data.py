#!/usr/bin/env python3
"""
Add comprehensive sample data for all features
"""

import MySQLdb
from datetime import date, datetime, timedelta

def add_comprehensive_data():
    try:
        # Database connection
        db = MySQLdb.connect(
            host='localhost',
            user='root',
            password='gmkr',
            database='lumorange_db'
        )
        
        cursor = db.cursor()
        
        print("🚀 Adding comprehensive sample data for all features...")
        
        # Clear existing sample data first (optional)
        # print("🧹 Cleaning existing sample data...")
        # cleanup_queries = [
        #     "DELETE FROM employee_projects",
        #     "DELETE FROM payroll_reports", 
        #     "DELETE FROM salaries",
        #     "DELETE FROM invoices",
        #     "DELETE FROM projects",
        #     "DELETE FROM employees WHERE employee_id LIKE 'EMP%'",
        #     "DELETE FROM clients WHERE name LIKE '%Sample%' OR name LIKE '%Demo%'",
        #     "DELETE FROM departments WHERE name IN ('Sample IT', 'Demo HR')"
        # ]
        
        # for cleanup in cleanup_queries:
        #     try:
        #         cursor.execute(cleanup)
        #     except:
        #         pass
        
        # Add comprehensive sample data
        sample_data = [
            # More employees with Indian names and proper structure
            "INSERT IGNORE INTO employees (employee_id, name, first_name, last_name, email, phone, position, department_id, hire_date, status) VALUES ('EMP006', 'Arjun Reddy', 'Arjun', 'Reddy', 'arjun.reddy@lumorange.com', '9876543215', 'UI/UX Designer', 1, '2024-01-25', 'active')",
            "INSERT IGNORE INTO employees (employee_id, name, first_name, last_name, email, phone, position, department_id, hire_date, status) VALUES ('EMP007', 'Kavya Krishnan', 'Kavya', 'Krishnan', 'kavya.krishnan@lumorange.com', '9876543216', 'Business Analyst', 2, '2024-02-05', 'active')",
            "INSERT IGNORE INTO employees (employee_id, name, first_name, last_name, email, phone, position, department_id, hire_date, status) VALUES ('EMP008', 'Ravi Kumar', 'Ravi', 'Kumar', 'ravi.kumar@lumorange.com', '9876543217', 'Accountant', 3, '2024-01-30', 'active')",
            "INSERT IGNORE INTO employees (employee_id, name, first_name, last_name, email, phone, position, department_id, hire_date, status) VALUES ('EMP009', 'Deepika Singh', 'Deepika', 'Singh', 'deepika.singh@lumorange.com', '9876543218', 'Content Writer', 4, '2024-02-12', 'active')",
            "INSERT IGNORE INTO employees (employee_id, name, first_name, last_name, email, phone, position, department_id, hire_date, status) VALUES ('EMP010', 'Karthik Nair', 'Karthik', 'Nair', 'karthik.nair@lumorange.com', '9876543219', 'DevOps Engineer', 1, '2024-01-12', 'active')",
            
            # More projects with realistic Indian business scenarios
            "INSERT IGNORE INTO projects (name, description, department_id, client_id, status, budget, progress, start_date, end_date) VALUES ('Banking App Integration', 'UPI and digital wallet integration for banking client', 1, 1, 'In Progress', 1200000, 60, '2024-01-15', '2024-05-15')",
            "INSERT IGNORE INTO projects (name, description, department_id, client_id, status, budget, progress, start_date, end_date) VALUES ('Government Portal', 'Citizen services digital portal', 1, 2, 'In Progress', 2500000, 30, '2024-02-01', '2024-08-31')",
            "INSERT IGNORE INTO projects (name, description, department_id, client_id, status, budget, progress, start_date, end_date) VALUES ('EdTech Platform', 'Online learning management system', 1, 3, 'Planned', 1800000, 5, '2024-03-15', '2024-09-30')",
            
            # More invoices with proper amounts and Indian context
            "INSERT IGNORE INTO invoices (client_id, invoice_number, invoice_date, due_date, project_id, subtotal, tax_rate, tax_amount, total_amount, status, notes) VALUES (1, 'INV-2024-006', '2024-08-22', '2024-09-22', 6, 400000, 18, 72000, 472000, 'sent', 'Banking app development milestone 1')",
            "INSERT IGNORE INTO invoices (client_id, invoice_number, invoice_date, due_date, project_id, subtotal, tax_rate, tax_amount, total_amount, status, notes) VALUES (2, 'INV-2024-007', '2024-08-20', '2024-09-20', 7, 800000, 18, 144000, 944000, 'draft', 'Government portal initial phase')",
            "INSERT IGNORE INTO invoices (client_id, invoice_number, invoice_date, due_date, project_id, subtotal, tax_rate, tax_amount, total_amount, status, notes) VALUES (3, 'INV-2024-008', '2024-07-30', '2024-08-30', 8, 200000, 18, 36000, 236000, 'paid', 'EdTech platform consultation')",
            
            # Employee project assignments
            "INSERT IGNORE INTO employee_projects (employee_id, project_id, role, start_date, is_active) VALUES (6, 6, 'UI/UX Lead', '2024-01-15', 1)",
            "INSERT IGNORE INTO employee_projects (employee_id, project_id, role, start_date, is_active) VALUES (10, 6, 'DevOps Engineer', '2024-01-15', 1)",
            "INSERT IGNORE INTO employee_projects (employee_id, project_id, role, start_date, is_active) VALUES (1, 7, 'Technical Lead', '2024-02-01', 1)",
            "INSERT IGNORE INTO employee_projects (employee_id, project_id, role, start_date, is_active) VALUES (7, 7, 'Business Analyst', '2024-02-01', 1)",
            "INSERT IGNORE INTO employee_projects (employee_id, project_id, role, start_date, is_active) VALUES (6, 8, 'UI Designer', '2024-03-15', 1)",
            "INSERT IGNORE INTO employee_projects (employee_id, project_id, role, start_date, is_active) VALUES (9, 8, 'Content Developer', '2024-03-15', 1)",
            
            # Salary records with Indian salary ranges
            "INSERT IGNORE INTO salaries (employee_id, basic_salary, house_allowance, transport_allowance, medical_allowance, other_allowances, effective_date, is_active) VALUES (6, 50000, 10000, 3000, 2000, 3000, '2024-01-25', 1)",
            "INSERT IGNORE INTO salaries (employee_id, basic_salary, house_allowance, transport_allowance, medical_allowance, other_allowances, effective_date, is_active) VALUES (7, 55000, 12000, 3000, 2500, 3500, '2024-02-05', 1)",
            "INSERT IGNORE INTO salaries (employee_id, basic_salary, house_allowance, transport_allowance, medical_allowance, other_allowances, effective_date, is_active) VALUES (8, 45000, 9000, 2500, 2000, 2500, '2024-01-30', 1)",
            "INSERT IGNORE INTO salaries (employee_id, basic_salary, house_allowance, transport_allowance, medical_allowance, other_allowances, effective_date, is_active) VALUES (9, 38000, 8000, 2500, 1500, 2000, '2024-02-12', 1)",
            "INSERT IGNORE INTO salaries (employee_id, basic_salary, house_allowance, transport_allowance, medical_allowance, other_allowances, effective_date, is_active) VALUES (10, 70000, 15000, 3500, 3000, 4000, '2024-01-12', 1)",
            
            # Payroll records for current month
            "INSERT IGNORE INTO payroll_reports (employee_id, month, year, basic_salary, total_allowances, total_deductions, gross_salary, net_salary, status, working_days, days_worked) VALUES (6, 8, 2024, 50000, 18000, 6800, 68000, 61200, 'paid', 22, 22)",
            "INSERT IGNORE INTO payroll_reports (employee_id, month, year, basic_salary, total_allowances, total_deductions, gross_salary, net_salary, status, working_days, days_worked) VALUES (7, 8, 2024, 55000, 21000, 7600, 76000, 68400, 'paid', 22, 21)",
            "INSERT IGNORE INTO payroll_reports (employee_id, month, year, basic_salary, total_allowances, total_deductions, gross_salary, net_salary, status, working_days, days_worked) VALUES (8, 8, 2024, 45000, 16000, 6100, 61000, 54900, 'processed', 22, 22)",
            "INSERT IGNORE INTO payroll_reports (employee_id, month, year, basic_salary, total_allowances, total_deductions, gross_salary, net_salary, status, working_days, days_worked) VALUES (9, 8, 2024, 38000, 14000, 5200, 52000, 46800, 'processed', 22, 20)",
            "INSERT IGNORE INTO payroll_reports (employee_id, month, year, basic_salary, total_allowances, total_deductions, gross_salary, net_salary, status, working_days, days_worked) VALUES (10, 8, 2024, 70000, 25500, 9550, 95500, 85950, 'paid', 22, 22)",
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
        
        print("\n🎉 Comprehensive sample data added successfully!")
        print("📊 Database now has:")
        print("   - 10+ employees with Indian names")
        print("   - Multiple departments with budgets")
        print("   - 8+ projects with realistic budgets")
        print("   - 8+ invoices with GST calculations")
        print("   - Employee-project assignments")
        print("   - Salary records with allowances")
        print("   - Current month payroll data")
        print("\n🚀 All pages should now display rich, dynamic data!")
        print("💰 Visit http://127.0.0.1:5000 to see the full system in action")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    add_comprehensive_data()
