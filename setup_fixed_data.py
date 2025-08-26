import mysql.connector

try:
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='gmkr',
        database='lumorange_db'
    )
    cursor = conn.cursor()
    
    # Add sample employees if none exist
    cursor.execute('SELECT COUNT(*) FROM employees')
    employee_count = cursor.fetchone()[0]
    
    if employee_count == 0:
        print('📝 Adding sample employees...')
        sample_employees = [
            ('EMP001', 'Rajesh Kumar', 'Rajesh', 'Kumar', 'rajesh@lumorange.com', '9876543210', 'Manager', 1, 'active'),
            ('EMP002', 'Priya Sharma', 'Priya', 'Sharma', 'priya@lumorange.com', '9876543211', 'Developer', 2, 'active'),
            ('EMP003', 'Amit Singh', 'Amit', 'Singh', 'amit@lumorange.com', '9876543212', 'Analyst', 3, 'active'),
            ('EMP004', 'Neha Gupta', 'Neha', 'Gupta', 'neha@lumorange.com', '9876543213', 'Designer', 1, 'active')
        ]
        
        insert_sql = '''INSERT INTO employees 
                        (employee_id, name, first_name, last_name, email, phone, position, department_id, status) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)'''
        
        cursor.executemany(insert_sql, sample_employees)
        conn.commit()
        print('✅ Sample employees added!')
    else:
        print(f'📋 Found {employee_count} employees in database')
        
    # Check employees again
    cursor.execute('SELECT id, first_name, last_name, email FROM employees LIMIT 5')
    employees = cursor.fetchall()
    
    print('\n✅ Available employees:')
    for emp in employees:
        print(f'   ID: {emp[0]} - {emp[1]} {emp[2]} ({emp[3]})')
        
    # Now add expense data if needed
    cursor.execute('SELECT COUNT(*) FROM expense_reports')
    expense_count = cursor.fetchone()[0]
    
    if expense_count == 0 and employees:
        print('\n💰 Adding sample expense data...')
        employee_id = employees[0][0]  # Use first employee
        
        sample_expenses = [
            (employee_id, '2025-08-20', 'Travel', 'Flight tickets to client meeting in Mumbai', 15000.00, 'Air India', 'approved'),
            (employee_id, '2025-08-22', 'Meals', 'Client dinner meeting at premium restaurant', 3500.00, 'The Leela Palace', 'approved'),
            (employee_id, '2025-08-23', 'Transportation', 'Uber rides for project work and client visits', 850.00, 'Uber', 'submitted'),
            (employee_id, '2025-08-24', 'Office Supplies', 'Stationery and printing for project presentations', 1200.00, 'Staples', 'submitted'),
            (employee_id, '2025-08-25', 'Software', 'Monthly software subscription for project tools', 2500.00, 'Microsoft Office', 'submitted')
        ]
        
        insert_sql = '''INSERT INTO expense_reports 
                        (employee_id, expense_date, category, description, amount, vendor_name, status) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s)'''
        
        cursor.executemany(insert_sql, sample_expenses)
        conn.commit()
        print('✅ Sample expense data added!')
        
    elif expense_count > 0:
        print(f'\n📊 Found {expense_count} expense records in database')
        
    # Final verification
    cursor.execute('SELECT COUNT(*) FROM expense_reports')
    final_count = cursor.fetchone()[0]
    print(f'\n🎉 Total expense records: {final_count}')
    
    conn.close()
    print('\n✨ Database setup complete! Ready to test Expense Management System.')
    
except Exception as e:
    print(f'❌ Error: {e}')
