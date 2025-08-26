import mysql.connector

try:
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='gmkr',
        database='lumorange_db'
    )
    cursor = conn.cursor()
    
    print('📋 Checking all employees in database...')
    cursor.execute('SELECT id, name, status FROM employees LIMIT 10')
    employees = cursor.fetchall()
    
    if employees:
        print('✅ Found employees:')
        for emp in employees:
            print(f'   ID: {emp[0]} - {emp[1]} - Status: {emp[2]}')
        
        # Use the first available employee ID (regardless of status for sample data)
        employee_id = employees[0][0]
        print(f'\n🔧 Adding expense data for employee ID: {employee_id}')
        
        # Check if data already exists
        cursor.execute('SELECT COUNT(*) FROM expense_reports')
        existing_count = cursor.fetchone()[0]
        
        if existing_count > 0:
            print(f'📊 Expense data already exists ({existing_count} records). Skipping insertion.')
        else:
            # Add sample data with correct employee ID
            sample_data = [
                (employee_id, '2025-08-20', 'Travel', 'Flight tickets to client meeting', 15000.00, 'Air India', 'approved'),
                (employee_id, '2025-08-22', 'Meals', 'Client dinner meeting', 3500.00, 'The Leela Palace', 'approved'),
                (employee_id, '2025-08-23', 'Transportation', 'Uber rides for project work', 850.00, 'Uber', 'submitted'),
                (employee_id, '2025-08-24', 'Office Supplies', 'Stationery and printing', 1200.00, 'Staples', 'submitted'),
                (employee_id, '2025-08-25', 'Software', 'Monthly software subscription', 2500.00, 'Microsoft', 'submitted')
            ]
            
            insert_sql = '''INSERT INTO expense_reports 
                            (employee_id, expense_date, category, description, amount, vendor_name, status) 
                            VALUES (%s, %s, %s, %s, %s, %s, %s)'''
            
            cursor.executemany(insert_sql, sample_data)
            conn.commit()
            print('✅ Sample expense data added successfully!')
        
        # Verify the final count
        cursor.execute('SELECT COUNT(*) FROM expense_reports')
        count = cursor.fetchone()[0]
        print(f'📊 Total expense records: {count}')
        
    else:
        print('❌ No employees found in database at all!')
        
    conn.close()
    print('\n🎉 Expense data setup complete!')
    
except Exception as e:
    print(f'❌ Error: {e}')
