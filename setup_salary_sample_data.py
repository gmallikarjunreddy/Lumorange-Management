#!/usr/bin/env python3

import MySQLdb
import random
from datetime import datetime, timedelta

def setup_salary_sample_data():
    try:
        # Connect to database
        db = MySQLdb.connect(
            host="localhost",
            user="root",
            passwd="gmkr",
            db="lumorange_db"
        )
        cursor = db.cursor()
        
        print("Setting up salary sample data...")
        
        # Get existing employees
        cursor.execute("SELECT id, name FROM employees")
        employees = cursor.fetchall()
        
        if not employees:
            print("No employees found. Please add employees first.")
            return
        
        print(f"Found {len(employees)} employees")
        
        # Clear existing salary data to avoid duplicates
        cursor.execute("DELETE FROM salaries WHERE employee_id IN (SELECT id FROM employees)")
        db.commit()
        print("Cleared existing salary data")
        
        # Sample salary data for each employee
        salary_ranges = {
            'senior': {'basic': (80000, 120000), 'allowances': (15000, 25000), 'deductions': (8000, 15000)},
            'mid': {'basic': (50000, 80000), 'allowances': (8000, 15000), 'deductions': (5000, 12000)},
            'junior': {'basic': (25000, 50000), 'allowances': (5000, 10000), 'deductions': (3000, 8000)}
        }
        
        positions = ['senior', 'mid', 'junior']
        
        for i, employee in enumerate(employees):
            employee_id = employee[0]
            employee_name = employee[1]
            
            # Assign position randomly but with some logic
            position = positions[i % len(positions)]
            salary_range = salary_ranges[position]
            
            # Generate salary components
            basic_salary = round(random.uniform(*salary_range['basic']), 2)
            allowances = round(random.uniform(*salary_range['allowances']), 2)
            deductions = round(random.uniform(*salary_range['deductions']), 2)
            
            # Effective date (sometime in the last 2 years)
            effective_date = datetime.now() - timedelta(days=random.randint(0, 730))
            
            # Insert salary record
            cursor.execute("""
                INSERT INTO salaries 
                (employee_id, basic_salary, allowances, deductions, effective_date, currency, is_active, created_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                employee_id,
                basic_salary,
                allowances,
                deductions,
                effective_date.strftime('%Y-%m-%d'),
                'INR',
                1,
                datetime.now()
            ))
            
            print(f"Created salary record for {employee_name}: ₹{basic_salary + allowances - deductions:,.2f}/month")
        
        # Add a few historical salary records (salary revisions)
        if len(employees) >= 2:
            # Add salary revision for first employee
            employee_id = employees[0][0]
            
            # Previous salary (6 months ago)
            previous_date = datetime.now() - timedelta(days=180)
            old_basic = round(random.uniform(40000, 70000), 2)
            old_allowances = round(random.uniform(5000, 12000), 2)
            old_deductions = round(random.uniform(3000, 8000), 2)
            
            cursor.execute("""
                INSERT INTO salaries 
                (employee_id, basic_salary, allowances, deductions, effective_date, end_date, currency, is_active, created_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                employee_id,
                old_basic,
                old_allowances,
                old_deductions,
                previous_date.strftime('%Y-%m-%d'),
                (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
                'INR',
                0,  # Not active anymore
                previous_date
            ))
            
            print(f"Added historical salary record for employee {employee_id}")
        
        db.commit()
        
        # Display summary
        cursor.execute("""
            SELECT COUNT(*) as total_records,
                   SUM(basic_salary + COALESCE(allowances, 0) - COALESCE(deductions, 0)) as total_payroll,
                   AVG(basic_salary + COALESCE(allowances, 0) - COALESCE(deductions, 0)) as avg_salary
            FROM salaries WHERE is_active = 1
        """)
        summary = cursor.fetchone()
        
        print("\n" + "="*50)
        print("SALARY SAMPLE DATA SETUP COMPLETE!")
        print("="*50)
        print(f"Total active salary records: {summary[0]}")
        print(f"Total monthly payroll: ₹{summary[1]:,.2f}")
        print(f"Average salary: ₹{summary[2]:,.2f}")
        print(f"Annual payroll cost: ₹{summary[1] * 12:,.2f}")
        
        cursor.close()
        db.close()
        
        print("\nSample salary data has been successfully created!")
        print("You can now test the salary management features.")
        
    except Exception as e:
        print(f"Error setting up salary sample data: {e}")
        if 'db' in locals():
            db.rollback()
            db.close()

if __name__ == "__main__":
    setup_salary_sample_data()