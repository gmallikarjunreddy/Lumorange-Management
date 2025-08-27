#!/usr/bin/env python3

import MySQLdb
from datetime import datetime, timedelta
import random

# Database connection
try:
    db = MySQLdb.connect(
        host='localhost',
        user='root',
        passwd='gmkr',
        db='lumorange_db'
    )
    cur = db.cursor()
    print("Connected to database successfully!")
    
    # First check if we have employees
    cur.execute("SELECT COUNT(*) FROM employees")
    employee_count = cur.fetchone()[0]
    
    if employee_count == 0:
        print("No employees found. Creating sample employees first...")
        
        # Insert sample employees
        employees_data = [
            ('John', 'Doe', 'john.doe@company.com', '9876543210', 'Software Engineer', 'Engineering', 75000, 'active'),
            ('Jane', 'Smith', 'jane.smith@company.com', '9876543211', 'Project Manager', 'Management', 85000, 'active'),
            ('Mike', 'Johnson', 'mike.johnson@company.com', '9876543212', 'Designer', 'Design', 65000, 'active'),
            ('Sarah', 'Wilson', 'sarah.wilson@company.com', '9876543213', 'Marketing Specialist', 'Marketing', 55000, 'active'),
            ('David', 'Brown', 'david.brown@company.com', '9876543214', 'Sales Executive', 'Sales', 60000, 'active')
        ]
        
        for emp in employees_data:
            cur.execute("""
                INSERT INTO employees 
                (first_name, last_name, email, phone, position, department, salary, status, created_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """, emp)
        
        db.commit()
        print(f"Created {len(employees_data)} sample employees.")
    
    # Get employee IDs
    cur.execute("SELECT id FROM employees WHERE status = 'active' LIMIT 5")
    employee_ids = [row[0] for row in cur.fetchall()]
    
    # Create sample expense data
    expense_categories = ['travel', 'meals', 'accommodation', 'transport', 'supplies', 'marketing', 'training', 'equipment', 'other']
    expense_statuses = ['submitted', 'approved', 'paid', 'rejected']
    vendors = ['Amazon', 'Uber', 'Hotel Taj', 'Indian Railways', 'Flipkart', 'Zomato', 'BookMyShow', 'Google Ads', 'Microsoft', 'Apple Store']
    
    # Generate expense data for the last 3 months
    base_date = datetime.now() - timedelta(days=90)
    
    expenses_data = []
    for i in range(50):  # Create 50 sample expenses
        employee_id = random.choice(employee_ids)
        expense_date = base_date + timedelta(days=random.randint(0, 90))
        category = random.choice(expense_categories)
        amount = round(random.uniform(500, 15000), 2)
        currency = 'INR'
        vendor_name = random.choice(vendors)
        status = random.choice(expense_statuses)
        
        # Create appropriate descriptions based on category
        descriptions = {
            'travel': f'Business travel expenses for client meeting in {random.choice(["Mumbai", "Delhi", "Bangalore", "Chennai"])}',
            'meals': f'Team lunch during project meeting',
            'accommodation': f'Hotel stay for {random.randint(1,3)} nights during business trip',
            'transport': f'Cab fare for client meetings and office commute',
            'supplies': f'Office supplies and stationery for team',
            'marketing': f'Marketing campaign expenses for {random.choice(["social media", "print ads", "digital marketing"])}',
            'training': f'Training course registration fee for professional development',
            'equipment': f'Purchase of {random.choice(["laptop accessories", "mobile phone", "headphones", "keyboard"])}',
            'other': f'Miscellaneous business expense'
        }
        
        description = descriptions.get(category, 'Business expense')
        
        expenses_data.append((
            employee_id,
            expense_date.strftime('%Y-%m-%d'),
            category,
            description,
            amount,
            currency,
            vendor_name,
            status
        ))
    
    # Insert expense data
    print("Inserting sample expense data...")
    for expense in expenses_data:
        cur.execute("""
            INSERT INTO expense_reports 
            (employee_id, expense_date, category, description, amount, currency, vendor_name, status, created_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
        """, expense)
    
    # Update some expenses with approval and payment dates
    cur.execute("SELECT id FROM expense_reports WHERE status = 'approved'")
    approved_ids = [row[0] for row in cur.fetchall()]
    
    for expense_id in approved_ids:
        approval_date = base_date + timedelta(days=random.randint(0, 85))
        cur.execute("""
            UPDATE expense_reports 
            SET approved_date = %s, approved_by = %s 
            WHERE id = %s
        """, (approval_date.strftime('%Y-%m-%d %H:%M:%S'), random.choice(employee_ids), expense_id))
    
    # Update paid expenses with payment dates  
    cur.execute("SELECT id FROM expense_reports WHERE status = 'paid'")
    paid_ids = [row[0] for row in cur.fetchall()]
    
    for expense_id in paid_ids:
        payment_date = base_date + timedelta(days=random.randint(0, 80))
        cur.execute("""
            UPDATE expense_reports 
            SET payment_date = %s, payment_reference = %s 
            WHERE id = %s
        """, (payment_date.strftime('%Y-%m-%d %H:%M:%S'), f'PAY-{random.randint(10000, 99999)}', expense_id))
    
    # Add rejection reasons for rejected expenses
    cur.execute("SELECT id FROM expense_reports WHERE status = 'rejected'")
    rejected_ids = [row[0] for row in cur.fetchall()]
    
    rejection_reasons = [
        'Receipt not provided',
        'Amount exceeds policy limit',
        'Not a business expense',
        'Duplicate claim',
        'Insufficient documentation'
    ]
    
    for expense_id in rejected_ids:
        reason = random.choice(rejection_reasons)
        cur.execute("""
            UPDATE expense_reports 
            SET rejection_reason = %s 
            WHERE id = %s
        """, (reason, expense_id))
    
    db.commit()
    
    # Display summary
    cur.execute("SELECT COUNT(*) FROM expense_reports")
    total_expenses = cur.fetchone()[0]
    
    cur.execute("SELECT status, COUNT(*), SUM(amount) FROM expense_reports GROUP BY status")
    status_summary = cur.fetchall()
    
    print(f"\n✅ Sample expense data created successfully!")
    print(f"Total expenses: {total_expenses}")
    print("\nStatus Summary:")
    for status, count, total_amount in status_summary:
        print(f"  {status.capitalize()}: {count} expenses, ₹{total_amount:,.2f}")
    
    cur.close()
    db.close()
    
except MySQLdb.Error as e:
    print(f"Database error: {e}")
except Exception as e:
    print(f"Error: {e}")