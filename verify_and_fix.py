import mysql.connector

try:
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='gmkr',
        database='lumorange_db'
    )
    cursor = conn.cursor()
    
    print('🔍 Checking current database state...')
    
    # Check departments
    cursor.execute('SELECT id, name FROM departments')
    departments = cursor.fetchall()
    print(f'\n🏢 Departments ({len(departments)}):')
    for dept in departments:
        print(f'   ID: {dept[0]} - {dept[1]}')
    
    # Check employees  
    cursor.execute('SELECT id, name FROM employees')
    employees = cursor.fetchall()
    print(f'\n👥 Employees ({len(employees)}):')
    for emp in employees:
        print(f'   ID: {emp[0]} - {emp[1]}')
    
    # Check expenses
    cursor.execute('SELECT id, category, amount FROM expense_reports')
    expenses = cursor.fetchall()
    print(f'\n💰 Expenses ({len(expenses)}):')
    for exp in expenses:
        print(f'   ID: {exp[0]} - {exp[1]} - ₹{exp[2]}')
    
    # If we have departments but no employees, let's add employees with correct dept IDs
    if departments and not employees:
        print('\n📝 Adding employees with correct department IDs...')
        dept_id = departments[0][0]  # Use first department ID
        
        sample_employees = [
            ('EMP001', 'Rajesh Kumar', 'Rajesh', 'Kumar', 'rajesh@lumorange.com', '9876543210', 'Manager', dept_id, 'active'),
            ('EMP002', 'Priya Sharma', 'Priya', 'Sharma', 'priya@lumorange.com', '9876543211', 'Developer', dept_id, 'active'),
            ('EMP003', 'Amit Singh', 'Amit', 'Singh', 'amit@lumorange.com', '9876543212', 'Analyst', dept_id, 'active'),
            ('EMP004', 'Neha Gupta', 'Neha', 'Gupta', 'neha@lumorange.com', '9876543213', 'Designer', dept_id, 'active')
        ]
        
        insert_sql = '''INSERT INTO employees 
                        (employee_id, name, first_name, last_name, email, phone, position, department_id, status) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)'''
        
        cursor.executemany(insert_sql, sample_employees)
        conn.commit()
        print('✅ Employees added successfully!')
        
        # Recheck employees
        cursor.execute('SELECT id, name FROM employees')
        employees = cursor.fetchall()
        print(f'\n👥 Updated Employees ({len(employees)}):')
        for emp in employees:
            print(f'   ID: {emp[0]} - {emp[1]}')
    
    # If we have employees but no expenses, add expenses
    if employees and not expenses:
        print('\n💰 Adding expense data...')
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
        print('✅ Expense data added successfully!')
        
        # Recheck expenses
        cursor.execute('SELECT id, category, amount FROM expense_reports')
        expenses = cursor.fetchall()
        print(f'\n💰 Updated Expenses ({len(expenses)}):')
        for exp in expenses:
            print(f'   ID: {exp[0]} - {exp[1]} - ₹{exp[2]}')
        
    conn.close()
    print('\n🎉 Database setup verification complete!')
    
except Exception as e:
    print(f'❌ Error: {e}')
