from flask import Flask, render_template
from flask_mysqldb import MySQL
import MySQLdb.cursors
from flask import request, redirect, url_for, flash, jsonify
from datetime import datetime, date

app = Flask(__name__)
app.secret_key = 'lumorange_secret_key'

# Template filters
@app.template_filter('days_since_hire')
def days_since_hire_filter(hire_date):
    if not hire_date:
        return 0
    if isinstance(hire_date, str):
        try:
            hire_date = datetime.strptime(hire_date, '%Y-%m-%d').date()
        except:
            return 0
    if isinstance(hire_date, date):
        return (date.today() - hire_date).days
    return 0

# MySQL configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'gmkr'
app.config['MYSQL_DB'] = 'lumorange_db'

mysql = MySQL(app)

@app.route('/')
def index():
    try:
        cur = mysql.connection.cursor()
        
        # Get dashboard statistics with fallback queries
        stats = {}
        
        # Total employees - try different column names
        try:
            cur.execute("SELECT COUNT(*) FROM employees WHERE status = 'active'")
            stats['total_employees'] = cur.fetchone()[0]
        except:
            try:
                cur.execute("SELECT COUNT(*) FROM employees")
                stats['total_employees'] = cur.fetchone()[0]
            except:
                stats['total_employees'] = 0
        
        # Total departments
        try:
            cur.execute("SELECT COUNT(*) FROM departments")
            stats['total_departments'] = cur.fetchone()[0]
        except:
            stats['total_departments'] = 0
        
        # Total projects  
        try:
            cur.execute("SELECT COUNT(*) FROM projects")
            stats['total_projects'] = cur.fetchone()[0]
        except:
            stats['total_projects'] = 0
        
        # Active projects
        try:
            cur.execute("SELECT COUNT(*) FROM projects WHERE status IN ('In Progress', 'Planned')")
            stats['active_projects'] = cur.fetchone()[0]
        except:
            stats['active_projects'] = stats['total_projects']
        
        # Monthly revenue from invoices
        try:
            cur.execute("""SELECT COALESCE(SUM(total_amount), 0) as monthly_revenue 
                           FROM invoices 
                           WHERE MONTH(invoice_date) = MONTH(NOW()) 
                           AND YEAR(invoice_date) = YEAR(NOW())
                           AND status IN ('paid', 'sent')""")
            stats['monthly_revenue'] = cur.fetchone()[0]
        except:
            stats['monthly_revenue'] = 0
        
        # Total revenue this year
        try:
            cur.execute("""SELECT COALESCE(SUM(total_amount), 0) as yearly_revenue 
                           FROM invoices 
                           WHERE YEAR(invoice_date) = YEAR(NOW())
                           AND status IN ('paid', 'sent')""")
            stats['yearly_revenue'] = cur.fetchone()[0]
        except:
            stats['yearly_revenue'] = 0
        
        # Calculate revenue growth percentage
        try:
            cur.execute("""SELECT COALESCE(SUM(total_amount), 0) as prev_month_revenue 
                           FROM invoices 
                           WHERE MONTH(invoice_date) = MONTH(DATE_SUB(NOW(), INTERVAL 1 MONTH))
                           AND YEAR(invoice_date) = YEAR(DATE_SUB(NOW(), INTERVAL 1 MONTH))
                           AND status IN ('paid', 'sent')""")
            prev_month_revenue = cur.fetchone()[0]
            if prev_month_revenue > 0:
                growth_percent = ((stats['monthly_revenue'] - prev_month_revenue) / prev_month_revenue) * 100
                stats['revenue_growth'] = round(growth_percent, 1)
                stats['growth_positive'] = growth_percent > 0
            else:
                stats['revenue_growth'] = 0
                stats['growth_positive'] = True
        except:
            stats['revenue_growth'] = 0
            stats['growth_positive'] = True
        
        # Recent employees (try different column formats)
        try:
            cur.execute("""SELECT COALESCE(CONCAT(first_name, ' ', last_name), name) as full_name, 
                           position, hire_date 
                           FROM employees WHERE status = 'active' 
                           ORDER BY hire_date DESC LIMIT 5""")
            recent_employees = cur.fetchall()
        except:
            try:
                cur.execute("""SELECT name, position, hire_date 
                               FROM employees 
                               ORDER BY hire_date DESC LIMIT 5""")
                recent_employees = cur.fetchall()
            except:
                recent_employees = []
        
        # Department summary
        try:
            cur.execute("""SELECT d.name, COUNT(e.id) as employee_count, COALESCE(d.budget, 0) as budget
                           FROM departments d 
                           LEFT JOIN employees e ON d.id = e.department_id AND e.status = 'active'
                           GROUP BY d.id, d.name, d.budget 
                           ORDER BY employee_count DESC LIMIT 5""")
            department_summary = cur.fetchall()
        except:
            try:
                cur.execute("""SELECT d.name, COUNT(e.id) as employee_count, 0 as budget
                               FROM departments d 
                               LEFT JOIN employees e ON d.id = e.department_id
                               GROUP BY d.id, d.name 
                               ORDER BY employee_count DESC LIMIT 5""")
                department_summary = cur.fetchall()
            except:
                department_summary = []
        
        # Recent activities
        recent_activities = []
        try:
            # Recent employee additions
            cur.execute("""SELECT COALESCE(CONCAT(first_name, ' ', last_name), name) as full_name, 
                           d.name as dept_name, hire_date
                           FROM employees e 
                           LEFT JOIN departments d ON e.department_id = d.id 
                           WHERE e.status = 'active'
                           ORDER BY hire_date DESC LIMIT 2""")
            recent_employees_activity = cur.fetchall()
            
            for emp in recent_employees_activity:
                recent_activities.append({
                    'type': 'employee',
                    'icon': 'fa-user-plus',
                    'color': 'success',
                    'title': 'New employee added',
                    'description': f"{emp[0]} has been added to the {emp[1] or 'Unknown'} Department",
                    'time': emp[2] if emp[2] else 'Recently'
                })
            
            # Recent project updates
            cur.execute("""SELECT p.name, p.status, p.start_date, 
                           COALESCE(p.progress, 0) as progress
                           FROM projects p 
                           ORDER BY p.start_date DESC LIMIT 2""")
            recent_projects = cur.fetchall()
            
            for proj in recent_projects:
                recent_activities.append({
                    'type': 'project',
                    'icon': 'fa-project-diagram',
                    'color': 'primary',
                    'title': 'Project update',
                    'description': f"{proj[0]} - Status: {proj[1]} ({proj[3]}% complete)",
                    'time': proj[2] if proj[2] else 'Recently'
                })
            
            # Recent invoices
            cur.execute("""SELECT i.invoice_number, c.name as client_name, 
                           i.invoice_date, i.status, COALESCE(i.total_amount, 0) as amount
                           FROM invoices i 
                           LEFT JOIN clients c ON i.client_id = c.id 
                           ORDER BY i.invoice_date DESC LIMIT 2""")
            recent_invoices = cur.fetchall()
            
            for inv in recent_invoices:
                recent_activities.append({
                    'type': 'invoice',
                    'icon': 'fa-file-invoice',
                    'color': 'warning',
                    'title': 'Invoice generated',
                    'description': f"{inv[0]} for {inv[1] or 'Unknown Client'} - {format_currency(inv[4])}",
                    'time': inv[2] if inv[2] else 'Recently'
                })
        except:
            # Fallback activities if database queries fail
            recent_activities = [
                {
                    'type': 'system',
                    'icon': 'fa-info-circle',
                    'color': 'info',
                    'title': 'System ready',
                    'description': 'Lumorange Management System is running',
                    'time': 'Now'
                }
            ]
        
        cur.close()
        return render_template('index.html', stats=stats, 
                             recent_employees=recent_employees, 
                             department_summary=department_summary,
                             recent_activities=recent_activities)
    except Exception as e:
        flash(f'Dashboard temporarily unavailable. Please set up the database using database_setup.sql', 'warning')
        return render_template('index.html', stats={'total_employees': 0, 'total_departments': 0, 'total_projects': 0, 'active_projects': 0}, 
                             recent_employees=[], 
                             department_summary=[],
                             recent_activities=[])

# Employee CRUD routes
@app.route('/employees', methods=['GET', 'POST'])
def employees():
    if request.method == 'POST':
        try:
            first_name = request.form['first_name']
            last_name = request.form['last_name']
            email = request.form['email']
            phone = request.form.get('phone', '')
            department_id = request.form['department_id']
            position = request.form['position']
            birth_date = request.form.get('birth_date')
            status = request.form.get('status', 'active')
            address = request.form.get('address', '')
            emergency_contact = request.form.get('emergency_contact', '')
            emergency_phone = request.form.get('emergency_phone', '')
            
            # Handle empty birth_date
            if not birth_date:
                birth_date = None
            
            # Generate unique employee ID
            cur = mysql.connection.cursor()
            
            # Find the highest existing employee ID number
            cur.execute("SELECT employee_id FROM employees WHERE employee_id LIKE 'EMP%' ORDER BY employee_id DESC LIMIT 1")
            result = cur.fetchone()
            
            if result:
                # Extract number from last employee ID (e.g., 'EMP002' -> 2)
                last_num = int(result[0][3:])
                new_num = last_num + 1
            else:
                # No employees exist yet, start with 1
                new_num = 1
            
            # Keep trying until we find a unique ID
            while True:
                employee_id = f"EMP{new_num:03d}"
                cur.execute("SELECT employee_id FROM employees WHERE employee_id = %s", (employee_id,))
                if not cur.fetchone():
                    break
                new_num += 1
            
            cur.execute("""INSERT INTO employees 
                          (employee_id, first_name, last_name, name, email, phone, 
                           department_id, position, birth_date, status, address, 
                           emergency_contact, emergency_phone, hire_date) 
                          VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURDATE())""",
                        (employee_id, first_name, last_name, f"{first_name} {last_name}", 
                         email, phone, department_id, position, birth_date, status, 
                         address, emergency_contact, emergency_phone))
            mysql.connection.commit()
            cur.close()
            flash(f'Employee "{first_name} {last_name}" added successfully!', 'success')
        except Exception as e:
            flash(f"Error adding employee: {e}", 'danger')
        return redirect(url_for('employees'))

    try:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("""
            SELECT 
                e.id,
                e.employee_id,
                e.first_name,
                e.last_name,
                CONCAT(e.first_name, ' ', e.last_name) as name,
                e.email,
                e.phone,
                e.address,
                e.birth_date,
                e.emergency_contact,
                e.emergency_phone,
                d.id as department_id,
                d.name as department_name,
                e.position,
                e.hire_date,
                COALESCE(e.status, 'active') as status,
                DATEDIFF(CURDATE(), e.hire_date) as days_since_hire
            FROM employees e
            LEFT JOIN departments d ON e.department_id = d.id
            ORDER BY e.first_name, e.last_name
        """)
        employees = cur.fetchall()

        cur.execute("SELECT id as department_id, name FROM departments ORDER BY name")
        departments = cur.fetchall()
        
        # Calculate summary statistics
        total_employees = len(employees)
        active_employees = len([emp for emp in employees if emp['status'] == 'active'])
        
        # Get departments count
        cur.execute("SELECT COUNT(*) FROM departments")
        total_departments = cur.fetchone()['COUNT(*)']
        
        # Get new hires this month
        cur.execute("""SELECT COUNT(*) FROM employees 
                       WHERE MONTH(hire_date) = MONTH(CURDATE()) 
                       AND YEAR(hire_date) = YEAR(CURDATE())""")
        new_hires_month = cur.fetchone()['COUNT(*)']
        
        cur.close()
        
        return render_template('employees_new.html', 
                             employees=employees, 
                             departments=departments,
                             total_employees=total_employees,
                             active_employees=active_employees,
                             total_departments=total_departments,
                             new_hires_month=new_hires_month)
    except Exception as e:
        flash(f"Error loading employees: {e}", 'danger')
        return render_template('employees_new.html', 
                             employees=[], 
                             departments=[],
                             total_employees=0,
                             active_employees=0,
                             total_departments=0,
                             new_hires_month=0)

@app.route('/employees/update', methods=['POST'])
def update_employee():
    try:
        employee_id = request.form['employee_id']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        phone = request.form.get('phone', '')
        department_id = request.form['department_id']
        position = request.form['position']
        birth_date = request.form.get('birth_date')
        status = request.form.get('status', 'active')
        address = request.form.get('address', '')
        emergency_contact = request.form.get('emergency_contact', '')
        emergency_phone = request.form.get('emergency_phone', '')
        
        # Handle empty birth_date
        if not birth_date:
            birth_date = None
        
        cur = mysql.connection.cursor()
        cur.execute("""UPDATE employees SET 
                       first_name = %s, 
                       last_name = %s, 
                       name = %s, 
                       email = %s, 
                       phone = %s,
                       department_id = %s, 
                       position = %s,
                       birth_date = %s,
                       status = %s,
                       address = %s,
                       emergency_contact = %s,
                       emergency_phone = %s
                       WHERE employee_id = %s""",
                    (first_name, last_name, f"{first_name} {last_name}", email, phone,
                     department_id, position, birth_date, status, address, 
                     emergency_contact, emergency_phone, employee_id))
        mysql.connection.commit()
        cur.close()
        flash(f'Employee "{first_name} {last_name}" updated successfully!', 'success')
    except Exception as e:
        flash(f'Error updating employee: {e}', 'danger')
    
    return redirect(url_for('employees'))

@app.route('/employees/delete/<string:employee_id>')
def delete_employee(employee_id):
    try:
        cur = mysql.connection.cursor()
        
        # Get employee name for message
        cur.execute("SELECT CONCAT(first_name, ' ', last_name) FROM employees WHERE employee_id = %s", (employee_id,))
        emp_result = cur.fetchone()
        emp_name = emp_result[0] if emp_result else 'Unknown Employee'
        
        # Check for dependencies (salaries, payroll, assignments)
        dependencies = []
        
        # Check salaries
        cur.execute("SELECT COUNT(*) FROM salaries WHERE employee_id = %s", (employee_id,))
        if cur.fetchone()[0] > 0:
            dependencies.append("salary records")
        
        # Check payroll
        cur.execute("SELECT COUNT(*) FROM payroll_reports WHERE employee_id = %s", (employee_id,))
        if cur.fetchone()[0] > 0:
            dependencies.append("payroll records")
            
        # Check project assignments
        cur.execute("SELECT COUNT(*) FROM employee_projects WHERE employee_id = %s", (employee_id,))
        if cur.fetchone()[0] > 0:
            dependencies.append("project assignments")
            
        # Check expense reports
        cur.execute("SELECT COUNT(*) FROM expense_reports WHERE employee_id = %s", (employee_id,))
        if cur.fetchone()[0] > 0:
            dependencies.append("expense reports")
        
        if dependencies:
            flash(f'Cannot delete employee "{emp_name}": Has active {", ".join(dependencies)}. Please remove these records first or set employee status to inactive.', 'danger')
        else:
            # Safe to delete
            cur.execute("DELETE FROM employees WHERE employee_id = %s", (employee_id,))
            mysql.connection.commit()
            flash(f'Employee "{emp_name}" deleted successfully!', 'success')
            
        cur.close()
        
    except Exception as e:
        flash(f'Error deleting employee: {e}', 'danger')
        
    return redirect(url_for('employees'))

# Department CRUD routes
@app.route('/departments')
def departments():
    try:
        cur = mysql.connection.cursor()
        cur.execute("""SELECT d.id, d.name, d.description, COALESCE(d.budget, 0) as budget, 
                       COUNT(e.id) as employee_count, 
                       COALESCE(DATE_FORMAT(d.created_date, '%%Y-%%m-%%d'), 'N/A') as created_date
                       FROM departments d 
                       LEFT JOIN employees e ON d.id = e.department_id AND e.status = 'active'
                       GROUP BY d.id, d.name, d.description, d.budget, d.created_date
                       ORDER BY d.name""")
        departments = cur.fetchall()
        
        # Calculate summary statistics
        total_employees = sum(dept[4] for dept in departments)
        total_budget = sum(dept[3] for dept in departments if dept[3])
        avg_budget = total_budget / len(departments) if departments else 0
        
        cur.close()
        return render_template('departments.html', 
                             departments=departments,
                             total_employees=total_employees,
                             total_budget=total_budget,
                             avg_budget=avg_budget)
    except Exception as e:
        flash(f'Error loading departments: {e}', 'danger')
        return render_template('departments.html', 
                             departments=[],
                             total_employees=0,
                             total_budget=0,
                             avg_budget=0)

@app.route('/add_department', methods=['POST'])
def add_department():
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    budget = request.form.get('budget', 0)
    
    if not name:
        flash('Department name is required!', 'danger')
        return redirect(url_for('departments'))
    
    # Convert budget to proper format
    try:
        budget = float(budget) if budget else 0
    except (ValueError, TypeError):
        budget = 0
        
    try:
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO departments (name, description, budget) VALUES (%s, %s, %s)", (name, description, budget))
        mysql.connection.commit()
        cur.close()
        flash(f'Department "{name}" added successfully!', 'success')
    except Exception as e:
        flash(f'Error adding department: {e}', 'danger')
    
    return redirect(url_for('departments'))

@app.route('/update_department', methods=['POST'])
def update_department():
    try:
        department_id = request.form['department_id']
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        budget = request.form.get('budget', 0)
        
        if not name:
            flash('Department name is required!', 'danger')
            return redirect(url_for('departments'))
        
        # Convert budget to proper format
        try:
            budget = float(budget) if budget else 0
        except (ValueError, TypeError):
            budget = 0
            
        cur = mysql.connection.cursor()
        cur.execute("UPDATE departments SET name = %s, description = %s, budget = %s WHERE id = %s", 
                   (name, description, budget, department_id))
        mysql.connection.commit()
        cur.close()
        flash(f'Department "{name}" updated successfully!', 'success')
    except Exception as e:
        flash(f'Error updating department: {e}', 'danger')
    
    return redirect(url_for('departments'))

@app.route('/delete_department/<int:id>')
def delete_department(id):
    try:
        cur = mysql.connection.cursor()
        
        # First check if department has employees
        cur.execute("SELECT COUNT(*) FROM employees WHERE department_id = %s", (id,))
        employee_count = cur.fetchone()[0]
        
        if employee_count > 0:
            flash(f'Cannot delete department: {employee_count} employees are still assigned to this department. Please reassign or remove employees first.', 'danger')
            cur.close()
            return redirect(url_for('departments'))
        
        # Get department name for success message
        cur.execute("SELECT name FROM departments WHERE id = %s", (id,))
        dept_result = cur.fetchone()
        dept_name = dept_result[0] if dept_result else 'Unknown Department'
        
        # Safe to delete department
        cur.execute("DELETE FROM departments WHERE id = %s", (id,))
        mysql.connection.commit()
        cur.close()
        
        flash(f'Department "{dept_name}" deleted successfully!', 'success')
        
    except Exception as e:
        flash(f'Error deleting department: {e}', 'danger')
    
    return redirect(url_for('departments'))

# API endpoints for enhanced departments functionality
@app.route('/api/department/<int:dept_id>/employees')
def api_department_employees(dept_id):
    try:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # First check if the department exists
        cur.execute("SELECT id, name FROM departments WHERE id = %s", (dept_id,))
        department = cur.fetchone()
        
        if not department:
            cur.close()
            return {'error': f'Department with ID {dept_id} not found'}, 404
        
        # Get employees for the department
        cur.execute("""SELECT 
                          CONCAT(e.first_name, ' ', e.last_name) as name,
                          e.position,
                          e.email,
                          DATE_FORMAT(e.hire_date, '%%Y-%%m-%%d') as hire_date,
                          e.id,
                          e.status
                       FROM employees e 
                       WHERE e.department_id = %s AND e.status = 'active'
                       ORDER BY e.first_name, e.last_name""", (dept_id,))
        employees = cur.fetchall()
        cur.close()
        
        return {
            'success': True,
            'department': department,
            'employees': employees,
            'count': len(employees)
        }
        
    except Exception as e:
        print(f"Error in api_department_employees: {str(e)}")  # Server-side logging
        return {'error': f'Database error: {str(e)}'}, 500

@app.route('/api/department/<int:dept_id>/details')
def api_department_details(dept_id):
    try:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Get department info
        cur.execute("""SELECT d.*, COUNT(e.id) as employee_count,
                          AVG(CASE WHEN s.basic_salary IS NOT NULL THEN s.basic_salary ELSE 0 END) as avg_salary
                       FROM departments d
                       LEFT JOIN employees e ON d.id = e.department_id AND e.status = 'active'
                       LEFT JOIN salaries s ON e.id = s.employee_id
                       WHERE d.id = %s
                       GROUP BY d.id""", (dept_id,))
        dept_details = cur.fetchone()
        
        cur.close()
        return {'department': dept_details}
    except Exception as e:
        return {'error': str(e)}, 400

@app.route('/api/departments/bulk-budget-update', methods=['POST'])
def api_bulk_budget_update():
    try:
        data = request.get_json()
        department_ids = data.get('department_ids', [])
        budget = data.get('budget', 0)
        
        if not department_ids:
            return {'success': False, 'message': 'No departments selected'}, 400
        
        cur = mysql.connection.cursor()
        placeholders = ','.join(['%s'] * len(department_ids))
        query = f"UPDATE departments SET budget = %s WHERE id IN ({placeholders})"
        cur.execute(query, [budget] + department_ids)
        mysql.connection.commit()
        cur.close()
        
        return {'success': True, 'message': f'Updated {len(department_ids)} departments'}
    except Exception as e:
        return {'success': False, 'message': str(e)}, 400

@app.route('/api/departments/bulk-delete', methods=['POST'])
def api_bulk_delete():
    try:
        data = request.get_json()
        department_ids = data.get('department_ids', [])
        
        if not department_ids:
            return {'success': False, 'message': 'No departments selected'}, 400
        
        cur = mysql.connection.cursor()
        
        # Check if any departments have employees
        placeholders = ','.join(['%s'] * len(department_ids))
        cur.execute(f"SELECT id, name FROM departments d WHERE d.id IN ({placeholders}) AND EXISTS (SELECT 1 FROM employees e WHERE e.department_id = d.id)", department_ids)
        departments_with_employees = cur.fetchall()
        
        if departments_with_employees:
            dept_names = [dept[1] for dept in departments_with_employees]
            return {'success': False, 'message': f'Cannot delete departments with employees: {", ".join(dept_names)}'}, 400
        
        # Safe to delete
        cur.execute(f"DELETE FROM departments WHERE id IN ({placeholders})", department_ids)
        mysql.connection.commit()
        cur.close()
        
        return {'success': True, 'message': f'Deleted {len(department_ids)} departments'}
    except Exception as e:
        return {'success': False, 'message': str(e)}, 400# Project CRUD routes
@app.route('/projects')
def projects():
    try:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Get comprehensive project data with statistics
        cur.execute("""
            SELECT 
                p.id,
                p.name,
                p.description,
                p.client_id,
                p.department_id,
                p.project_manager_id,
                p.start_date,
                p.end_date,
                p.budget,
                p.actual_cost,
                p.status,
                p.priority,
                p.created_date,
                p.updated_date,
                p.progress,
                d.name as department_name,
                c.name as client_name,
                CONCAT(pm.first_name, ' ', pm.last_name) as project_manager_name,
                DATEDIFF(CURDATE(), p.start_date) as days_running,
                CASE 
                    WHEN p.end_date IS NULL THEN 0
                    ELSE DATEDIFF(p.end_date, CURDATE())
                END as days_remaining,
                (SELECT COUNT(*) FROM employee_projects ep WHERE ep.project_id = p.id) as team_size
            FROM projects p 
            LEFT JOIN departments d ON p.department_id = d.id
            LEFT JOIN clients c ON p.client_id = c.id
            LEFT JOIN employees pm ON p.project_manager_id = pm.id
            ORDER BY p.created_date DESC
        """)
        projects = cur.fetchall()
        
        # Calculate summary statistics
        total_projects = len(projects)
        active_projects = len([p for p in projects if p['status'] == 'active'])
        completed_projects = len([p for p in projects if p['status'] == 'completed'])
        
        # Calculate total budget and actual costs
        total_budget = sum(float(p['budget'] or 0) for p in projects)
        total_actual_cost = sum(float(p['actual_cost'] or 0) for p in projects)
        
        # Get average progress
        active_project_progress = [p['progress'] for p in projects if p['status'] == 'active' and p['progress'] is not None]
        avg_progress = sum(active_project_progress) / len(active_project_progress) if active_project_progress else 0
        
        # Get high priority projects count
        high_priority_projects = len([p for p in projects if p['priority'] == 'high'])
        
        # Get departments for dropdown
        cur.execute("SELECT id, name FROM departments ORDER BY name")
        departments = cur.fetchall()
        
        # Get clients for dropdown  
        cur.execute("SELECT id, name FROM clients ORDER BY name")
        clients = cur.fetchall()
        
        # Get employees for project manager dropdown
        cur.execute("SELECT id, CONCAT(first_name, ' ', last_name) as name FROM employees WHERE status = 'active' ORDER BY first_name")
        employees = cur.fetchall()
        
        cur.close()
        
        return render_template('projects_clean.html', 
                             projects=projects, 
                             departments=departments, 
                             clients=clients,
                             employees=employees,
                             total_projects=total_projects,
                             active_projects=active_projects,
                             completed_projects=completed_projects,
                             total_budget=total_budget,
                             total_actual_cost=total_actual_cost,
                             avg_progress=round(avg_progress, 1),
                             high_priority_projects=high_priority_projects)
    except Exception as e:
        flash(f"Error loading projects: {e}", 'danger')
        return render_template('projects_new.html', 
                             projects=[], 
                             departments=[], 
                             clients=[],
                             employees=[],
                             total_projects=0,
                             active_projects=0,
                             completed_projects=0,
                             total_budget=0,
                             total_actual_cost=0,
                             avg_progress=0,
                             high_priority_projects=0)

@app.route('/add_project', methods=['POST'])
def add_project():
    try:
        name = request.form['name']
        description = request.form.get('description', '')
        department_id = request.form['department_id']
        client_id = request.form.get('client_id') or None
        project_manager_id = request.form.get('project_manager_id') or None
        status = request.form.get('status', 'planning')
        priority = request.form.get('priority', 'medium')
        budget = request.form.get('budget', 0)
        progress = request.form.get('progress', 0)
        start_date = request.form['start_date']
        end_date = request.form.get('end_date') or None
        
        # Validate status against allowed ENUM values
        allowed_statuses = ['planning', 'active', 'on_hold', 'completed', 'cancelled']
        if status not in allowed_statuses:
            status = 'planning'
            
        # Validate priority against allowed ENUM values
        allowed_priorities = ['low', 'medium', 'high', 'urgent']
        if priority not in allowed_priorities:
            priority = 'medium'
        
        # Validate and convert numeric fields
        try:
            budget = float(budget) if budget else 0.0
            progress = int(progress) if progress else 0
            progress = max(0, min(100, progress))
        except (ValueError, TypeError):
            budget = 0.0
            progress = 0
        
        if not name or not department_id or not start_date:
            flash('Name, Department, and Start Date are required!', 'danger')
            return redirect(url_for('projects'))
            
        cur = mysql.connection.cursor()
        cur.execute("""INSERT INTO projects (name, description, department_id, client_id, 
                       project_manager_id, status, priority, budget, progress, start_date, end_date) 
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""", 
                       (name, description, department_id, client_id, project_manager_id, 
                        status, priority, budget, progress, start_date, end_date))
        mysql.connection.commit()
        cur.close()
        flash(f'Project "{name}" added successfully!', 'success')
    except Exception as e:
        flash(f'Error adding project: {e}', 'danger')
    return redirect(url_for('projects'))

@app.route('/update_project', methods=['POST'])
def update_project():
    try:
        project_id = request.form['project_id']
        name = request.form['name']
        description = request.form.get('description', '')
        department_id = request.form['department_id']
        client_id = request.form.get('client_id') or None
        project_manager_id = request.form.get('project_manager_id') or None
        status = request.form.get('status', 'planning')
        priority = request.form.get('priority', 'medium')
        budget = request.form.get('budget', 0)
        actual_cost = request.form.get('actual_cost', 0)
        progress = request.form.get('progress', 0)
        start_date = request.form['start_date']
        end_date = request.form.get('end_date') or None
        
        # Validate ENUM values
        allowed_statuses = ['planning', 'active', 'on_hold', 'completed', 'cancelled']
        if status not in allowed_statuses:
            status = 'planning'
            
        allowed_priorities = ['low', 'medium', 'high', 'urgent']
        if priority not in allowed_priorities:
            priority = 'medium'
        
        # Validate numeric fields
        try:
            budget = float(budget) if budget else 0.0
            actual_cost = float(actual_cost) if actual_cost else 0.0
            progress = int(progress) if progress else 0
            progress = max(0, min(100, progress))
        except (ValueError, TypeError):
            budget = 0.0
            actual_cost = 0.0
            progress = 0
        
        cur = mysql.connection.cursor()
        cur.execute("""UPDATE projects SET name = %s, description = %s, department_id = %s,
                       client_id = %s, project_manager_id = %s, status = %s, priority = %s,
                       budget = %s, actual_cost = %s, progress = %s, start_date = %s, end_date = %s
                       WHERE id = %s""", 
                   (name, description, department_id, client_id, project_manager_id, 
                    status, priority, budget, actual_cost, progress, start_date, end_date, project_id))
        mysql.connection.commit()
        cur.close()
        flash(f'Project "{name}" updated successfully!', 'success')
    except Exception as e:
        flash(f'Error updating project: {e}', 'danger')
    return redirect(url_for('projects'))

@app.route('/delete_project/<int:id>')
def delete_project(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM projects WHERE id = %s", (id,))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('projects'))

# Employee-Project Assignment CRUD routes
@app.route('/employee_projects')
def employee_projects():
    cur = mysql.connection.cursor()
    cur.execute("""SELECT ep.id, ep.employee_id, ep.project_id, ep.role, 
                   COALESCE(CONCAT(e.first_name, ' ', e.last_name), e.name) as employee_name,
                   p.name as project_name, d.name as department_name,
                   COALESCE(ep.assigned_date, ep.start_date, ep.created_date) as assigned_date
                   FROM employee_projects ep
                   LEFT JOIN employees e ON ep.employee_id = e.id
                   LEFT JOIN projects p ON ep.project_id = p.id  
                   LEFT JOIN departments d ON e.department_id = d.id
                   WHERE COALESCE(ep.is_active, 1) = 1
                   ORDER BY ep.created_date DESC""")
    employee_projects = cur.fetchall()
    
    # Get employees for dropdown
    cur.execute("""SELECT id, COALESCE(CONCAT(first_name, ' ', last_name), name) as name, position 
                   FROM employees WHERE status = 'active' ORDER BY first_name, last_name, name""")
    employees = cur.fetchall()
    
    # Get projects for dropdown
    cur.execute("SELECT id, name FROM projects ORDER BY name")
    projects = cur.fetchall()
    
    cur.close()
    
    from datetime import date
    today = date.today().strftime('%Y-%m-%d')
    
    return render_template('employee_projects.html', 
                         employee_projects=employee_projects, 
                         employees=employees, 
                         projects=projects,
                         today=today)

@app.route('/assign_employee_project', methods=['POST'])
def assign_employee_project():
    employee_id = request.form['employee_id']
    project_id = request.form['project_id']
    role = request.form['role']
    assigned_date = request.form.get('assigned_date', 'CURDATE()')
    
    if not employee_id or not project_id or not role:
        flash('All fields are required!', 'danger')
        return redirect(url_for('employee_projects'))
    try:
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO employee_projects (employee_id, project_id, role, assigned_date) VALUES (%s, %s, %s, %s)", 
                   (employee_id, project_id, role, assigned_date))
        mysql.connection.commit()
        cur.close()
        flash('Assignment added successfully!', 'success')
    except Exception as e:
        flash(f'Error assigning employee to project: {e}', 'danger')
    return redirect(url_for('employee_projects'))

@app.route('/delete_employee_project/<int:id>')
def delete_employee_project(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM employee_projects WHERE id = %s", (id,))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('employee_projects'))

# Client CRUD routes
@app.route('/clients')
def clients():
    cur = mysql.connection.cursor()
    cur.execute("""SELECT id, name, email, phone, address, contact_person, 
                   company_type, website, tax_id, payment_terms, status, 
                   created_date, updated_date FROM clients ORDER BY created_date DESC""")
    clients = cur.fetchall()
    
    # Calculate statistics
    total_clients = len(clients)
    active_clients = len([c for c in clients if c[10] == 'active'])
    inactive_clients = total_clients - active_clients
    
    # Calculate new clients this month
    from datetime import datetime, timedelta
    current_month = datetime.now().replace(day=1)
    new_this_month = len([c for c in clients if c[11] and c[11] >= current_month])
    
    # Get unique company types for filter
    company_types = list(set([c[6] for c in clients if c[6]]))
    
    statistics = {
        'total': total_clients,
        'active': active_clients,
        'inactive': inactive_clients,
        'new_this_month': new_this_month
    }
    
    cur.close()
    return render_template('clients.html', clients=clients, statistics=statistics, company_types=company_types)

@app.route('/add_client', methods=['POST'])
def add_client():
    name = request.form['name']
    email = request.form['email']
    phone = request.form['phone']
    address = request.form['address']
    contact_person = request.form['contact_person']
    company_type = request.form['company_type']
    website = request.form['website']
    tax_id = request.form['tax_id']
    payment_terms = request.form['payment_terms']
    status = 'active' if 'status' in request.form else 'inactive'
    
    if not name:
        flash('Client name is required!', 'danger')
        return redirect(url_for('clients'))
    
    try:
        cur = mysql.connection.cursor()
        cur.execute("""INSERT INTO clients (name, email, phone, address, contact_person, 
                       company_type, website, tax_id, payment_terms, status) 
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""", 
                   (name, email, phone, address, contact_person, company_type, 
                    website, tax_id, payment_terms, status))
        mysql.connection.commit()
        cur.close()
        flash('Client added successfully!', 'success')
    except Exception as e:
        flash(f'Error adding client: {e}', 'danger')
    return redirect(url_for('clients'))

@app.route('/update_client', methods=['POST'])
def update_client():
    try:
        client_id = request.form['client_id']
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        address = request.form['address']
        contact_person = request.form['contact_person']
        company_type = request.form['company_type']
        website = request.form['website']
        tax_id = request.form['tax_id']
        payment_terms = request.form['payment_terms']
        status = 'active' if 'status' in request.form else 'inactive'
        
        cur = mysql.connection.cursor()
        cur.execute("""UPDATE clients SET name = %s, email = %s, phone = %s, 
                       address = %s, contact_person = %s, company_type = %s, 
                       website = %s, tax_id = %s, payment_terms = %s, status = %s,
                       updated_date = NOW() WHERE id = %s""",
                    (name, email, phone, address, contact_person, company_type,
                     website, tax_id, payment_terms, status, client_id))
        mysql.connection.commit()
        cur.close()
        flash(f'Client "{name}" updated successfully!', 'success')
    except Exception as e:
        flash(f"Error updating client: {e}", 'danger')
    return redirect(url_for('clients'))

@app.route('/delete_client/<int:id>')
def delete_client(id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM clients WHERE id = %s", (id,))
        mysql.connection.commit()
        cur.close()
        flash('Client deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting client: {e}', 'danger')
    return redirect(url_for('clients'))

@app.route('/toggle_client_status', methods=['POST'])
def toggle_client_status():
    try:
        data = request.get_json()
        client_id = data['client_id']
        status = data['status']
        
        cur = mysql.connection.cursor()
        cur.execute("UPDATE clients SET status = %s, updated_date = NOW() WHERE id = %s", 
                   (status, client_id))
        mysql.connection.commit()
        cur.close()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# Salary CRUD routes
@app.route('/salaries')
def salaries():
    cur = mysql.connection.cursor()
    cur.execute("""SELECT s.id, 
                   COALESCE(CONCAT(e.first_name, ' ', e.last_name), e.name) as employee_name,
                   s.basic_salary, 
                   COALESCE(s.allowances, 0) as allowances,
                   COALESCE(s.deductions, 0) as deductions,
                   (s.basic_salary + COALESCE(s.allowances, 0) - COALESCE(s.deductions, 0)) as net_salary,
                   s.effective_date 
                   FROM salaries s 
                   JOIN employees e ON s.employee_id = e.id 
                   WHERE s.is_active = 1
                   ORDER BY s.effective_date DESC""")
    salaries = cur.fetchall()
    
    # Get employees for dropdown
    cur.execute("""SELECT id, COALESCE(CONCAT(first_name, ' ', last_name), name) as name 
                   FROM employees WHERE status = 'active' ORDER BY first_name, last_name, name""")
    employees = cur.fetchall()
    
    cur.close()
    return render_template('salaries.html', salaries=salaries, employees=employees)

@app.route('/add_salary', methods=['POST'])
def add_salary():
    employee_id = request.form['employee_id']
    basic_salary = request.form['basic_salary']
    allowances = request.form['allowances'] or 0
    deductions = request.form['deductions'] or 0
    effective_date = request.form['effective_date']
    if not employee_id or not basic_salary or not effective_date:
        flash('Employee ID, Basic Salary, and Effective Date are required!', 'danger')
        return redirect(url_for('salaries'))
    try:
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO salaries (employee_id, basic_salary, allowances, deductions, effective_date) VALUES (%s, %s, %s, %s, %s)", 
                   (employee_id, basic_salary, allowances, deductions, effective_date))
        mysql.connection.commit()
        cur.close()
        flash('Salary record added successfully!', 'success')
    except Exception as e:
        flash(f'Error adding salary record: {e}', 'danger')
    return redirect(url_for('salaries'))

@app.route('/delete_salary/<int:id>')
def delete_salary(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM salaries WHERE id = %s", (id,))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('salaries'))

# Payroll Reports routes
@app.route('/payroll')
def payroll():
    cur = mysql.connection.cursor()
    cur.execute("""SELECT pr.id, 
                   COALESCE(CONCAT(e.first_name, ' ', e.last_name), e.name) as employee_name,
                   pr.month, pr.year, pr.basic_salary, 
                   COALESCE(pr.total_allowances, 0) as allowances,
                   COALESCE(pr.total_deductions, 0) as deductions,
                   COALESCE(pr.net_salary, pr.basic_salary) as net_salary, 
                   pr.status 
                   FROM payroll_reports pr 
                   JOIN employees e ON pr.employee_id = e.id 
                   ORDER BY pr.year DESC, pr.month DESC""")
    payroll_reports = cur.fetchall()
    
    # Get employees for payroll generation
    cur.execute("""SELECT id, COALESCE(CONCAT(first_name, ' ', last_name), name) as name 
                   FROM employees WHERE status = 'active' ORDER BY first_name, last_name, name""")
    employees = cur.fetchall()
    
    cur.close()
    return render_template('payroll.html', payroll_reports=payroll_reports, employees=employees)

@app.route('/generate_payroll', methods=['POST'])
def generate_payroll():
    month = request.form['month']
    year = request.form['year']
    if not month or not year:
        flash('Month and Year are required!', 'danger')
        return redirect(url_for('payroll'))
    
    try:
        cur = mysql.connection.cursor()
        # Get all employees with their latest salary
        cur.execute("""SELECT e.id, e.name, 
                       COALESCE(s.basic_salary, 0) as basic_salary,
                       COALESCE(s.allowances, 0) as allowances,
                       COALESCE(s.deductions, 0) as deductions
                       FROM employees e 
                       LEFT JOIN salaries s ON e.id = s.employee_id 
                       WHERE s.effective_date = (
                           SELECT MAX(s2.effective_date) 
                           FROM salaries s2 
                           WHERE s2.employee_id = e.id 
                           AND s2.effective_date <= LAST_DAY(STR_TO_DATE(CONCAT(%s, '-', %s), '%%Y-%%m'))
                       )""", (year, month))
        
        employees = cur.fetchall()
        generated_count = 0
        
        for emp in employees:
            employee_id, name, basic_salary, allowances, deductions = emp
            net_salary = basic_salary + allowances - deductions
            
            # Check if payroll already exists for this employee and month
            cur.execute("SELECT id FROM payroll_reports WHERE employee_id = %s AND month = %s AND year = %s", 
                       (employee_id, month, year))
            existing = cur.fetchone()
            
            if not existing:
                cur.execute("""INSERT INTO payroll_reports 
                              (month, year, employee_id, basic_salary, allowances, deductions, net_salary, status) 
                              VALUES (%s, %s, %s, %s, %s, %s, %s, 'draft')""", 
                           (month, year, employee_id, basic_salary, allowances, deductions, net_salary))
                generated_count += 1
        
        mysql.connection.commit()
        cur.close()
        flash(f'Payroll generated for {generated_count} employees for {month}/{year}!', 'success')
    except Exception as e:
        flash(f'Error generating payroll: {e}', 'danger')
    
    return redirect(url_for('payroll'))

@app.route('/update_payroll_status/<int:id>/<status>')
def update_payroll_status(id, status):
    try:
        cur = mysql.connection.cursor()
        cur.execute("UPDATE payroll_reports SET status = %s WHERE id = %s", (status, id))
        mysql.connection.commit()
        cur.close()
        flash(f'Payroll status updated to {status}!', 'success')
    except Exception as e:
        flash(f'Error updating payroll status: {e}', 'danger')
    return redirect(url_for('payroll'))

@app.route('/delete_payroll/<int:id>')
def delete_payroll(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM payroll_reports WHERE id = %s", (id,))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('payroll'))

# Invoice routes
@app.route('/invoices/<int:invoice_id>')
def invoice_details(invoice_id):
    try:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Get main invoice details
        cur.execute("""
            SELECT 
                i.id as invoice_id, i.invoice_number, i.invoice_date, i.due_date, i.status,
                i.subtotal_amount as subtotal, i.tax_amount as tax, i.total_amount as total,
                c.name as client_name, c.email as client_email, c.address as client_address,
                p.name as project_name
            FROM invoices i
            JOIN clients c ON i.client_id = c.id
            LEFT JOIN projects p ON i.project_id = p.id
            WHERE i.id = %s
        """, (invoice_id,))
        invoice = cur.fetchone()

        if not invoice:
            flash('Invoice not found.', 'danger')
            return redirect(url_for('invoices'))

        # For now, create simple items from invoice data
        items = [{
            'description': f"Project: {invoice['project_name']}" if invoice['project_name'] else "General Services",
            'total': invoice['subtotal']
        }]
        
        cur.close()
        return render_template('invoice_details.html', invoice=invoice, items=items)

    except Exception as e:
        flash(f"Error loading invoice details: {e}", 'danger')
        return redirect(url_for('invoices'))

@app.route('/invoices')
def invoices():
    try:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("""
            SELECT 
                i.id as invoice_id, 
                c.name as client_name, 
                i.invoice_number, 
                i.invoice_date, 
                i.due_date, 
                p.name as project_name, 
                i.total_amount as total, 
                i.status 
            FROM invoices i 
            JOIN clients c ON i.client_id = c.id 
            LEFT JOIN projects p ON i.project_id = p.id 
            ORDER BY i.invoice_date DESC
        """)
        invoices = cur.fetchall()
        cur.close()
        return render_template('invoices.html', invoices=invoices)
    except Exception as e:
        flash(f"Error loading invoices: {e}", 'danger')
        return render_template('invoices.html', invoices=[])

@app.route('/invoices/add', methods=['GET', 'POST'])
def add_invoice():
    if request.method == 'POST':
        client_id = request.form['client_id']
        project_id = request.form['project_id'] if request.form['project_id'] else None
        amount = request.form['amount']
        tax_rate = request.form['tax_rate'] or 0
        due_date = request.form['due_date']
        notes = request.form['notes']
        
        if not client_id or not amount or not due_date:
            flash('Client, Amount, and Due Date are required!', 'danger')
            return redirect(url_for('invoices'))
        
        try:
            cur = mysql.connection.cursor()
            
            # Generate invoice number
            cur.execute("SELECT COUNT(*) FROM invoices")
            invoice_count = cur.fetchone()[0]
            invoice_number = f"INV-{(invoice_count + 1):04d}"
            
            # Calculate total amount
            amount_val = float(amount)
            tax_rate_val = float(tax_rate)
            tax_amount = amount_val * (tax_rate_val / 100)
            total_amount = amount_val + tax_amount;
            
            cur.execute("""INSERT INTO invoices 
                          (client_id, invoice_number, invoice_date, due_date, project_id, 
                           amount, tax_rate, total_amount, status, notes) 
                          VALUES (%s, %s, CURDATE(), %s, %s, %s, %s, %s, 'draft', %s)""", 
                       (client_id, invoice_number, due_date, project_id, amount, tax_rate, total_amount, notes))
            
            mysql.connection.commit()
            cur.close()
            flash(f'Invoice {invoice_number} created successfully!', 'success')
        except Exception as e:
            flash(f'Error creating invoice: {e}', 'danger')
        
        return redirect(url_for('invoices'))
    
    try:
        # For GET request, just render the invoice form
        cur = mysql.connection.cursor()
        
        # Get active clients
        cur.execute("SELECT id, name FROM clients WHERE status = 'active' ORDER BY name")
        clients = cur.fetchall()
        
        # Get active projects for the client (if any client is selected)
        selected_client_id = request.args.get('client_id')
        projects = []
        if selected_client_id:
            cur.execute("SELECT id, name FROM projects WHERE client_id = %s AND status != 'completed' ORDER BY name", (selected_client_id,))
            projects = cur.fetchall()
        
        cur.close()
        return render_template('add_invoice.html', clients=clients, projects=projects)
    except Exception as e:
        flash(f'Error loading invoice form: {e}', 'danger')
        return render_template('add_invoice.html', clients=[], projects=[])

@app.route('/update_invoice', methods=['POST'])
def update_invoice():
    try:
        invoice_id = request.form['invoice_id']
        status = request.form['status']
        
        cur = mysql.connection.cursor()
        cur.execute("UPDATE invoices SET status = %s WHERE id = %s", (status, invoice_id))
        mysql.connection.commit()
        cur.close()
        flash(f'Invoice status updated to {status}!', 'success')
    except Exception as e:
        flash(f'Error updating invoice: {e}', 'danger')
    return redirect(url_for('invoices'))

@app.route('/update_invoice_status/<int:id>/<status>')
def update_invoice_status(id, status):
    try:
        cur = mysql.connection.cursor()
        cur.execute("UPDATE invoices SET status = %s WHERE id = %s", (status, id))
        mysql.connection.commit()
        cur.close()
        flash(f'Invoice status updated to {status}!', 'success')
    except Exception as e:
        flash(f'Error updating invoice status: {e}', 'danger')
    return redirect(url_for('invoices'))

@app.route('/delete_invoice/<int:id>')
def delete_invoice(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM invoices WHERE id = %s", (id,))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('invoices'))

# Error handlers for better UX
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

# Removing the global exception handler to prevent redirect loops
# @app.errorhandler(Exception)
# def handle_exception(e):
#     flash(f'An unexpected error occurred: {str(e)}', 'danger')
#     return redirect(url_for('index'))

# Helper function to check database connection
def check_db_connection():
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT 1")
        cur.close()
        return True
    except:
        return False

# Helper function to format currency in Indian Rupees
def format_currency(amount):
    """Format amount as Indian Rupees"""
    if amount is None or amount == 0:
        return "₹0"
    
    # Convert to float if it's a string
    try:
        amount = float(amount)
    except (ValueError, TypeError):
        return "₹0"
    
    # Format with Indian number system (lakhs, crores)
    if amount >= 10000000:  # 1 crore
        return f"₹{amount/10000000:.1f}Cr"
    elif amount >= 100000:  # 1 lakh
        return f"₹{amount/100000:.1f}L"
    elif amount >= 1000:
        return f"₹{amount/1000:.1f}K"
    else:
        return f"₹{amount:,.0f}"

# Expense Management routes
@app.route('/expenses')
def expenses():
    try:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("""SELECT e.id, 
                       COALESCE(CONCAT(emp.first_name, ' ', emp.last_name), emp.name) as employee_name,
                       e.expense_date as report_date,
                       e.category,
                       e.description,
                       e.amount as total_amount,
                       e.vendor_name,
                       e.status,
                       COALESCE(CONCAT(approver.first_name, ' ', approver.last_name), approver.name) as approved_by_name,
                       e.approved_date,
                       e.created_date
                       FROM expense_reports e
                       LEFT JOIN employees emp ON e.employee_id = emp.id
                       LEFT JOIN employees approver ON e.approved_by = approver.id
                       ORDER BY e.created_date DESC""")
        expenses = cur.fetchall()
        
        # Get employees for dropdown
        cur.execute("""SELECT id, COALESCE(CONCAT(first_name, ' ', last_name), name) as name 
                       FROM employees ORDER BY first_name, last_name, name""")
        employees = cur.fetchall()
        
        # Get projects for dropdown
        cur.execute("SELECT id, name FROM projects ORDER BY name")
        projects = cur.fetchall()
        
        # Calculate summary statistics
        cur.execute("SELECT COUNT(*) as count, COALESCE(SUM(amount), 0) as total FROM expense_reports WHERE status = 'submitted'")
        pending_stats = cur.fetchone()
        
        cur.execute("SELECT COUNT(*) as count, COALESCE(SUM(amount), 0) as total FROM expense_reports WHERE status = 'approved'")
        approved_stats = cur.fetchone()
        
        cur.close()
        
        stats = {
            'pending_count': pending_stats['count'] if pending_stats else 0,
            'pending_amount': pending_stats['total'] if pending_stats else 0,
            'approved_count': approved_stats['count'] if approved_stats else 0,
            'approved_amount': approved_stats['total'] if approved_stats else 0
        }
        
        return render_template('expenses.html', expenses=expenses, employees=employees, projects=projects, stats=stats)
    except Exception as e:
        flash(f'Error loading expenses: {e}', 'danger')
        return render_template('expenses.html', expenses=[], employees=[], projects=[], stats={})

@app.route('/add_expense', methods=['POST'])
def add_expense():
    try:
        employee_id = request.form['employee_id']
        expense_date = request.form.get('expense_date', datetime.now().strftime('%Y-%m-%d'))
        category = request.form.get('category', 'other')
        description = request.form['description']
        amount = request.form['total_amount']  # Changed from 'amount' to 'total_amount'
        vendor_name = request.form.get('vendor_name', '')
        project_id = request.form.get('project_id') if request.form.get('project_id') else None
        
        if not employee_id or not description or not amount:
            flash('Employee, description, and amount are required!', 'danger')
            return redirect(url_for('expenses'))
        
        cur = mysql.connection.cursor()
        cur.execute("""INSERT INTO expense_reports 
                       (employee_id, expense_date, category, description, amount, vendor_name, project_id, status) 
                       VALUES (%s, %s, %s, %s, %s, %s, %s, 'submitted')""", 
                   (employee_id, expense_date, category, description, amount, vendor_name, project_id))
        mysql.connection.commit()
        cur.close()
        flash('Expense report submitted successfully!', 'success')
    except Exception as e:
        flash(f'Error adding expense: {e}', 'danger')
    
    return redirect(url_for('expenses'))

@app.route('/approve_expense/<int:id>')
def approve_expense(id):
    try:
        cur = mysql.connection.cursor()
        # For now, we'll use the first available employee as approver
        cur.execute("SELECT id FROM employees LIMIT 1")
        approver_result = cur.fetchone()
        approver_id = approver_result[0] if approver_result else 1
        
        cur.execute("""UPDATE expense_reports 
                       SET status = 'approved', approved_by = %s, approved_date = NOW() 
                       WHERE id = %s""", (approver_id, id))
        mysql.connection.commit()
        
        if cur.rowcount > 0:
            flash('Expense approved successfully!', 'success')
        else:
            flash('Expense not found!', 'danger')
        
        cur.close()
    except Exception as e:
        flash(f'Error approving expense: {e}', 'danger')
    
    return redirect(url_for('expenses'))

@app.route('/reject_expense/<int:id>', methods=['POST'])
def reject_expense(id):
    try:
        rejection_reason = request.form.get('rejection_reason', 'No reason provided')
        
        cur = mysql.connection.cursor()
        cur.execute("SELECT id FROM employees LIMIT 1")
        approver_result = cur.fetchone()
        approver_id = approver_result[0] if approver_result else 1
        
        cur.execute("""UPDATE expense_reports 
                       SET status = 'rejected', approved_by = %s, approved_date = NOW(), rejection_reason = %s 
                       WHERE id = %s""", (approver_id, rejection_reason, id))
        mysql.connection.commit()
        
        if cur.rowcount > 0:
            flash(f'Expense rejected: {rejection_reason}', 'warning')
        else:
            flash('Expense not found!', 'danger')
        
        cur.close()
    except Exception as e:
        flash(f'Error rejecting expense: {e}', 'danger')
    
    return redirect(url_for('expenses'))

@app.route('/mark_expense_paid/<int:id>')
def mark_expense_paid(id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("""UPDATE expense_reports 
                       SET status = 'paid', payment_date = NOW(), payment_reference = CONCAT('PAY-', id, '-', DATE_FORMAT(NOW(), '%%Y%%m%%d'))
                       WHERE id = %s AND status = 'approved'""", (id,))
        mysql.connection.commit()
        
        if cur.rowcount > 0:
            flash('Expense marked as paid successfully!', 'success')
        else:
            flash('Expense not found or not approved!', 'danger')
        
        cur.close()
    except Exception as e:
        flash(f'Error marking expense as paid: {e}', 'danger')
    
    return redirect(url_for('expenses'))

@app.route('/delete_expense/<int:id>')
def delete_expense(id):
    try:
        cur = mysql.connection.cursor()
        
        # Check if expense can be deleted (only submitted expenses)
        cur.execute("SELECT status FROM expense_reports WHERE id = %s", (id,))
        expense = cur.fetchone()
        
        if not expense:
            flash('Expense not found!', 'danger')
        elif expense[0] in ['approved', 'paid']:
            flash('Cannot delete approved or paid expenses!', 'danger')
        else:
            cur.execute("DELETE FROM expense_reports WHERE id = %s", (id,))
            mysql.connection.commit()
            flash('Expense deleted successfully!', 'success')
        
        cur.close()
    except Exception as e:
        flash(f'Error deleting expense: {e}', 'danger')
    
    return redirect(url_for('expenses'))

@app.route('/agreements')
def agreements():
    """Render the agreements page for legal documents"""
    return render_template('agreements.html')

# Context processor to add global variables
@app.context_processor
def inject_globals():
    return {
        'current_year': 2025,
        'app_name': 'Lumorange Management',
        'db_connected': check_db_connection(),
        'currency_symbol': '₹',
        'currency_name': 'Indian Rupee',
        'format_currency': format_currency
    }

if __name__ == '__main__':
    app.run(debug=True)
