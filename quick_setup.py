#!/usr/bin/env python3
"""
Quick Database Setup Script for Lumorange Management System
Run this script to create the basic database structure if you haven't run the SQL file yet.
"""

import MySQLdb
from datetime import date

def setup_database():
    try:
        # Database connection
        db = MySQLdb.connect(
            host='localhost',
            user='root',
            password='gmkr',  # Change this to your MySQL password
            database='lumorange_db'
        )
        
        cursor = db.cursor()
        
        print("🔧 Setting up basic database structure...")
        
        # Create basic tables with minimal structure for immediate functionality
        tables = [
            """
            CREATE TABLE IF NOT EXISTS departments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                budget DECIMAL(15,2) DEFAULT 0,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS employees (
                id INT AUTO_INCREMENT PRIMARY KEY,
                employee_id VARCHAR(20) UNIQUE,
                name VARCHAR(100) NOT NULL,
                first_name VARCHAR(50),
                last_name VARCHAR(50),
                email VARCHAR(100) UNIQUE NOT NULL,
                phone VARCHAR(20),
                position VARCHAR(100),
                department_id INT,
                salary DECIMAL(10,2) DEFAULT 0,
                hire_date DATE,
                status ENUM('active', 'inactive') DEFAULT 'active',
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS clients (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(150) NOT NULL,
                email VARCHAR(100),
                phone VARCHAR(20),
                address TEXT,
                contact_person VARCHAR(100),
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS projects (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(150) NOT NULL,
                description TEXT,
                department_id INT,
                client_id INT,
                status ENUM('Planned', 'In Progress', 'Completed', 'On Hold') DEFAULT 'Planned',
                budget DECIMAL(15,2) DEFAULT 0,
                progress INT DEFAULT 0,
                start_date DATE,
                end_date DATE,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS invoices (
                id INT AUTO_INCREMENT PRIMARY KEY,
                client_id INT NOT NULL,
                project_id INT,
                invoice_number VARCHAR(50) UNIQUE NOT NULL,
                invoice_date DATE DEFAULT (CURRENT_DATE),
                due_date DATE NOT NULL,
                amount DECIMAL(15,2) NOT NULL,
                subtotal_amount DECIMAL(15,2),
                tax_rate DECIMAL(5,2) DEFAULT 0,
                total_amount DECIMAL(15,2) NOT NULL,
                status ENUM('draft', 'sent', 'paid', 'overdue') DEFAULT 'draft',
                notes TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS employee_projects (
                id INT AUTO_INCREMENT PRIMARY KEY,
                employee_id INT NOT NULL,
                project_id INT NOT NULL,
                role VARCHAR(100) NOT NULL,
                assigned_date DATE DEFAULT (CURRENT_DATE),
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS salaries (
                id INT AUTO_INCREMENT PRIMARY KEY,
                employee_id INT NOT NULL,
                basic_salary DECIMAL(10,2) NOT NULL,
                allowances DECIMAL(10,2) DEFAULT 0,
                deductions DECIMAL(10,2) DEFAULT 0,
                effective_date DATE NOT NULL,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS payroll_reports (
                id INT AUTO_INCREMENT PRIMARY KEY,
                employee_id INT NOT NULL,
                month INT NOT NULL,
                year INT NOT NULL,
                basic_salary DECIMAL(10,2) NOT NULL,
                allowances DECIMAL(10,2) DEFAULT 0,
                deductions DECIMAL(10,2) DEFAULT 0,
                status ENUM('draft', 'processed', 'paid') DEFAULT 'draft',
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        ]
        
        for table_sql in tables:
            cursor.execute(table_sql)
            print("✅ Created table")
        
        # Insert sample data if tables are empty
        cursor.execute("SELECT COUNT(*) FROM departments")
        if cursor.fetchone()[0] == 0:
            print("📊 Adding sample data...")
            
            sample_data = [
                "INSERT INTO departments (name, description, budget) VALUES ('IT', 'Information Technology', 500000), ('HR', 'Human Resources', 200000), ('Finance', 'Finance Department', 300000)",
                "INSERT INTO employees (employee_id, name, first_name, last_name, email, position, department_id, hire_date) VALUES ('EMP001', 'John Doe', 'John', 'Doe', 'john@lumorange.com', 'Developer', 1, CURDATE())",
                "INSERT INTO clients (name, email, contact_person) VALUES ('Tech Corp', 'contact@techcorp.com', 'Jane Smith')",
                "INSERT INTO projects (name, description, department_id, status) VALUES ('Website Project', 'Company website development', 1, 'In Progress')"
            ]
            
            for data_sql in sample_data:
                try:
                    cursor.execute(data_sql)
                except:
                    pass  # Skip if data already exists
        
        db.commit()
        cursor.close()
        db.close()
        
        print("🎉 Database setup completed successfully!")
        print("🚀 Your Lumorange Management System is ready to use!")
        print("📱 Open http://127.0.0.1:5000 in your browser")
        
    except Exception as e:
        print(f"❌ Error setting up database: {e}")
        print("💡 Make sure:")
        print("   1. MySQL server is running")
        print("   2. Database 'lumorange_db' exists")
        print("   3. Update the password in this script")
        print("   4. Run: CREATE DATABASE lumorange_db; in MySQL first")

if __name__ == "__main__":
    setup_database()
