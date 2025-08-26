#!/usr/bin/env python3
"""
Add sample data with Indian Rupee values to demonstrate dynamic features
"""

import MySQLdb
from datetime import date, datetime

def add_sample_data():
    try:
        # Database connection
        db = MySQLdb.connect(
            host='localhost',
            user='root',
            password='gmkr',  # Change this to your MySQL password
            database='lumorange_db'
        )
        
        cursor = db.cursor()
        
        print("💰 Adding sample data with Indian Rupee values...")
        
        # Sample data with Indian context
        sample_data = [
            # Updated departments with higher INR budgets
            "UPDATE departments SET budget = 2500000 WHERE name = 'IT'",
            "UPDATE departments SET budget = 1200000 WHERE name = 'HR'", 
            "UPDATE departments SET budget = 1800000 WHERE name = 'Finance'",
            
            # Add more realistic Indian employee data
            "INSERT IGNORE INTO employees (employee_id, name, first_name, last_name, email, position, department_id, salary, hire_date, status) VALUES ('EMP002', 'Priya Sharma', 'Priya', 'Sharma', 'priya@lumorange.com', 'HR Manager', 2, 65000, '2024-02-01', 'active')",
            "INSERT IGNORE INTO employees (employee_id, name, first_name, last_name, email, position, department_id, salary, hire_date, status) VALUES ('EMP003', 'Amit Patel', 'Amit', 'Patel', 'amit@lumorange.com', 'Financial Analyst', 3, 55000, '2024-01-20', 'active')",
            "INSERT IGNORE INTO employees (employee_id, name, first_name, last_name, email, position, department_id, salary, hire_date, status) VALUES ('EMP004', 'Sneha Gupta', 'Sneha', 'Gupta', 'sneha@lumorange.com', 'Marketing Executive', 1, 45000, '2024-02-10', 'active')",
            
            # Add more clients
            "INSERT IGNORE INTO clients (name, email, phone, contact_person) VALUES ('StartupXYZ Solutions', 'contact@startupxyz.com', '9876543221', 'Anita Desai')",
            "INSERT IGNORE INTO clients (name, email, phone, contact_person) VALUES ('Global Enterprises Ltd', 'admin@globalent.co.in', '9876543222', 'Rahul Agarwal')",
            
            # Add projects with INR budgets
            "INSERT IGNORE INTO projects (name, description, department_id, client_id, status, budget, progress, start_date, end_date) VALUES ('E-Commerce Platform', 'Complete e-commerce solution with payment gateway', 1, 1, 'In Progress', 1500000, 75, '2024-01-01', '2024-06-30')",
            "INSERT IGNORE INTO projects (name, description, department_id, client_id, status, budget, progress, start_date, end_date) VALUES ('Mobile App Development', 'Cross-platform mobile application', 1, 2, 'In Progress', 800000, 45, '2024-02-01', '2024-05-31')",
            
            # Create invoices with Indian amounts
            "INSERT IGNORE INTO invoices (client_id, invoice_number, invoice_date, due_date, project_id, amount, tax_rate, total_amount, status, notes) VALUES (1, 'INV-0001', '2024-08-01', '2024-08-31', 1, 500000, 18, 590000, 'paid', 'First milestone payment')",
            "INSERT IGNORE INTO invoices (client_id, invoice_number, invoice_date, due_date, project_id, amount, tax_rate, total_amount, status, notes) VALUES (2, 'INV-0002', '2024-08-15', '2024-09-15', 2, 300000, 18, 354000, 'sent', 'Development Phase 1')",
        ]
        
        for data_sql in sample_data:
            try:
                cursor.execute(data_sql)
                print("✅ Added data:", data_sql[:50] + "...")
            except Exception as e:
                print(f"⚠️ Skipped: {str(e)[:50]}...")
        
        db.commit()
        cursor.close()
        db.close()
        
        print("🎉 Sample data with Indian Rupees added successfully!")
        print("💰 Refresh your browser to see the updated dashboard with dynamic data")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    add_sample_data()
