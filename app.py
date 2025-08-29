from flask import Flask, render_template
from flask_mysqldb import MySQL
import MySQLdb.cursors
from flask import request, redirect, url_for, flash, jsonify, make_response
from datetime import datetime, date
import json
import uuid
import random
import string

app = Flask(__name__)
app.secret_key = 'lumorange_secret_key'

# Template context processor to add common functions
@app.context_processor
def inject_date_functions():
    return {
        'today': lambda: date.today(),
        'datetime': datetime,
        'date': date
    }

def generate_interview_code():
    """Generate a unique interview code"""
    # Generate a random 3-letter + 3-digit code like INT001, INT002, etc.
    prefix = "INT"
    suffix = str(random.randint(100, 999))
    return f"{prefix}{suffix}"

def get_unique_interview_code():
    """Get a unique interview code that doesn't exist in database"""
    cur = mysql.connection.cursor()
    while True:
        code = generate_interview_code()
        cur.execute("SELECT id FROM interviews WHERE interview_code = %s", (code,))
        if not cur.fetchone():
            cur.close()
            return code

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
    
    return render_template('employee_projects.html', 
                         employee_projects=employee_projects, 
                         employees=employees, 
                         projects=projects)

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

@app.route('/update_salary', methods=['POST'])
def update_salary():
    try:
        salary_id = request.form['salary_id']
        employee_id = request.form['employee_id']
        basic_salary = request.form['basic_salary']
        allowances = request.form['allowances'] or 0
        deductions = request.form['deductions'] or 0
        effective_date = request.form['effective_date']
        
        if not salary_id or not employee_id or not basic_salary or not effective_date:
            flash('All required fields must be filled!', 'danger')
            return redirect(url_for('salaries'))
        
        cur = mysql.connection.cursor()
        
        # Update salary record
        cur.execute("""
            UPDATE salaries 
            SET employee_id = %s, basic_salary = %s, allowances = %s, 
                deductions = %s, effective_date = %s
            WHERE id = %s
        """, (employee_id, basic_salary, allowances, deductions, effective_date, salary_id))
        
        mysql.connection.commit()
        cur.close()
        
        flash('Salary record updated successfully!', 'success')
        
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Error updating salary record: {e}', 'danger')
        
    return redirect(url_for('salaries'))

# Salary API endpoints
@app.route('/api/salary/<int:salary_id>')
def get_salary_details(salary_id):
    try:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("""
            SELECT s.id, s.employee_id, s.basic_salary, s.allowances, s.deductions,
                   (s.basic_salary + COALESCE(s.allowances, 0) - COALESCE(s.deductions, 0)) as net_salary,
                   s.effective_date, s.end_date, s.currency, s.is_active, s.created_date,
                   COALESCE(CONCAT(e.first_name, ' ', e.last_name), e.name) as employee_name,
                   e.email, COALESCE(d.name, 'Not Assigned') as department
            FROM salaries s
            JOIN employees e ON s.employee_id = e.id
            LEFT JOIN departments d ON e.department_id = d.id
            WHERE s.id = %s
        """, (salary_id,))
        salary = cur.fetchone()
        cur.close()
        
        if salary:
            # Convert date objects to strings for JSON serialization
            if salary['effective_date']:
                salary['effective_date_display'] = salary['effective_date'].strftime('%d %b %Y')
                salary['effective_date'] = salary['effective_date'].strftime('%Y-%m-%d')  # ISO format for input
            if salary['end_date']:
                salary['end_date'] = salary['end_date'].strftime('%d %b %Y')
            if salary['created_date']:
                salary['created_date'] = salary['created_date'].strftime('%d %b %Y, %I:%M %p')
            
            return jsonify({'success': True, 'salary': salary})
        else:
            return jsonify({'success': False, 'error': 'Salary record not found'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/salaries/export')
def export_salaries():
    try:
        cur = mysql.connection.cursor()
        cur.execute("""SELECT s.id, 
                       COALESCE(CONCAT(e.first_name, ' ', e.last_name), e.name) as employee_name,
                       s.basic_salary, 
                       COALESCE(s.allowances, 0) as allowances,
                       COALESCE(s.deductions, 0) as deductions,
                       (s.basic_salary + COALESCE(s.allowances, 0) - COALESCE(s.deductions, 0)) as net_salary,
                       s.effective_date, s.currency
                       FROM salaries s 
                       JOIN employees e ON s.employee_id = e.id 
                       WHERE s.is_active = 1
                       ORDER BY s.effective_date DESC""")
        salaries = cur.fetchall()
        cur.close()
        
        # Create CSV response
        output = []
        output.append(['ID', 'Employee', 'Basic Salary', 'Allowances', 'Deductions', 'Net Salary', 'Effective Date', 'Currency'])
        
        for salary in salaries:
            row = [
                f"SAL-{salary[0]}",
                salary[1],
                f"{salary[2]:.2f}",
                f"{salary[3]:.2f}",
                f"{salary[4]:.2f}",
                f"{salary[5]:.2f}",
                salary[6].strftime('%Y-%m-%d') if salary[6] else '',
                salary[7] or 'INR'
            ]
            output.append(row)
        
        # Convert to CSV string
        import io
        import csv
        si = io.StringIO()
        cw = csv.writer(si)
        cw.writerows(output)
        
        # Create response
        response = make_response(si.getvalue())
        response.headers["Content-Disposition"] = "attachment; filename=salary_records.csv"
        response.headers["Content-type"] = "text/csv"
        
        return response
        
    except Exception as e:
        flash(f'Error exporting salary data: {e}', 'danger')
        return redirect(url_for('salaries'))

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

# Template context processor for format_currency
@app.template_filter('format_currency')
def format_currency_filter(amount, currency='INR'):
    """Format currency with proper symbol"""
    if not amount:
        amount = 0
    
    symbols = {
        'INR': '₹',
        'USD': '$',
        'EUR': '€',
        'GBP': '£',
        'CAD': 'C$'
    }
    
    symbol = symbols.get(currency, '₹')
    return f"{symbol}{amount:,.2f}"

@app.template_global()
def format_currency(amount, currency='INR'):
    """Global template function for formatting currency"""
    return format_currency_filter(amount, currency)

@app.route('/invoices')
def invoices():
    try:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Get all invoices with detailed information
        cur.execute("""
            SELECT 
                i.id,
                i.invoice_number,
                i.invoice_date,
                i.due_date,
                i.client_id,
                i.project_id,
                i.subtotal,
                i.tax_rate,
                i.tax_amount,
                i.discount_amount,
                i.total_amount,
                i.currency,
                i.status,
                i.payment_method,
                i.payment_date,
                i.notes,
                i.created_date,
                i.updated_date,
                c.name as client_name
            FROM invoices i 
            JOIN clients c ON i.client_id = c.id 
            ORDER BY i.created_date DESC
        """)
        invoices = cur.fetchall()
        
        # Get clients for filters
        cur.execute("SELECT id, name FROM clients WHERE status = 'active' ORDER BY name")
        clients = cur.fetchall()
        
        # Get projects for the add invoice modal
        cur.execute("SELECT id, name, client_id FROM projects WHERE status != 'completed' ORDER BY name")
        projects = cur.fetchall()
        
        # Calculate statistics
        total_invoices = len(invoices)
        paid_invoices = len([inv for inv in invoices if inv['status'] == 'paid'])
        pending_invoices = len([inv for inv in invoices if inv['status'] in ['sent', 'pending']])
        overdue_invoices = len([inv for inv in invoices if inv['status'] == 'overdue'])
        
        # Calculate financial statistics
        total_revenue = sum(inv['total_amount'] or 0 for inv in invoices if inv['status'] == 'paid')
        outstanding = sum(inv['total_amount'] or 0 for inv in invoices if inv['status'] in ['sent', 'pending', 'overdue'])
        
        # This month's revenue
        from datetime import datetime, timedelta
        current_month = datetime.now().replace(day=1)
        this_month_revenue = sum(
            inv['total_amount'] or 0 for inv in invoices 
            if inv['status'] == 'paid' and inv['payment_date'] and inv['payment_date'] >= current_month
        )
        
        statistics = {
            'total': total_invoices,
            'paid': paid_invoices,
            'pending': pending_invoices,
            'overdue': overdue_invoices,
            'total_revenue': total_revenue,
            'outstanding': outstanding,
            'this_month': this_month_revenue
        }
        
        # Add current date for template calculations
        current_date = datetime.now().date()
        
        cur.close()
        return render_template('invoices.html', 
                             invoices=invoices, 
                             clients=clients,
                             projects=projects,
                             statistics=statistics,
                             current_date=current_date)
    except Exception as e:
        flash(f"Error loading invoices: {e}", 'danger')
        return render_template('invoices.html', 
                             invoices=[], 
                             clients=[],
                             projects=[],
                             statistics={'total': 0, 'paid': 0, 'pending': 0, 'overdue': 0, 'total_revenue': 0, 'outstanding': 0, 'this_month': 0},
                             current_date=datetime.now().date())

@app.route('/invoices/add', methods=['GET', 'POST'])
def add_invoice():
    if request.method == 'POST':
        try:
            # Get form data
            client_id = request.form['client_id']
            project_id = request.form['project_id'] if request.form['project_id'] else None
            invoice_date = request.form['invoice_date']
            due_date = request.form['due_date']
            tax_rate = float(request.form['tax_rate'] or 0)
            discount_amount = float(request.form.get('discount_amount', 0))
            currency = request.form.get('currency', 'INR')
            payment_method = request.form.get('payment_method', 'bank_transfer')
            notes = request.form.get('notes', '')
            terms_conditions = request.form.get('terms_conditions', 'Payment due within 30 days of invoice date.')
            
            if not client_id or not invoice_date or not due_date:
                flash('Client, Invoice Date, and Due Date are required!', 'danger')
                return redirect(url_for('invoices'))
            
            # Calculate subtotal from line items
            descriptions = request.form.getlist('description[]')
            quantities = request.form.getlist('quantity[]')
            unit_prices = request.form.getlist('unit_price[]')
            
            subtotal_amount = 0
            for i in range(len(descriptions)):
                if descriptions[i] and quantities[i] and unit_prices[i]:
                    qty = float(quantities[i] or 0)
                    price = float(unit_prices[i] or 0)
                    subtotal_amount += qty * price
            
            # Calculate amounts
            tax_amount = (subtotal_amount - discount_amount) * (tax_rate / 100)
            total_amount = subtotal_amount + tax_amount - discount_amount
            
            # Generate invoice number
            from datetime import datetime
            cur = mysql.connection.cursor()
            current_year = datetime.now().year
            cur.execute("SELECT COUNT(*) FROM invoices WHERE YEAR(invoice_date) = %s", (current_year,))
            count = cur.fetchone()[0]
            invoice_number = f"INV-{current_year}-{str(count + 1).zfill(4)}"
            
            # Insert invoice
            cur.execute("""
                INSERT INTO invoices 
                (client_id, project_id, invoice_number, invoice_date, due_date, 
                 subtotal, tax_rate, tax_amount, discount_amount, total_amount, 
                 currency, status, payment_method, notes, terms_conditions, created_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'draft', %s, %s, %s, NOW())
            """, (client_id, project_id, invoice_number, invoice_date, due_date,
                  subtotal_amount, tax_rate, tax_amount, discount_amount, total_amount,
                  currency, payment_method, notes, terms_conditions))
            
            mysql.connection.commit()
            cur.close()
            
            flash(f'Invoice {invoice_number} created successfully!', 'success')
            return redirect(url_for('invoices'))
            
        except Exception as e:
            mysql.connection.rollback()
            flash(f"Error creating invoice: {e}", 'danger')
            return redirect(url_for('invoices'))
    
    try:
        # For GET request, just render the invoice form
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Get active clients
        cur.execute("SELECT id, name FROM clients WHERE status = 'active' ORDER BY name")
        clients = cur.fetchall()
        
        # Get active projects for the client (if any client is selected)
        cur.execute("SELECT id, name, client_id FROM projects WHERE status != 'completed' ORDER BY name")
        projects = cur.fetchall()
        
        cur.close()
        return render_template('add_invoice.html', clients=clients, projects=projects)
    except Exception as e:
        flash(f'Error loading invoice form: {e}', 'danger')
        return render_template('add_invoice.html', clients=[], projects=[])

@app.route('/update_invoice', methods=['POST'])
def update_invoice():
    try:
        # Get form data
        invoice_id = request.form['invoice_id']
        client_id = request.form.get('client_id')
        project_id = request.form.get('project_id') if request.form.get('project_id') else None
        invoice_date = request.form.get('invoice_date')
        due_date = request.form.get('due_date')
        subtotal_amount = float(request.form.get('subtotal_amount', 0))
        tax_rate = float(request.form.get('tax_rate', 0))
        discount_amount = float(request.form.get('discount_amount', 0))
        currency = request.form.get('currency', 'INR')
        status = request.form.get('status', 'draft')
        payment_method = request.form.get('payment_method', 'bank_transfer')
        notes = request.form.get('notes', '')
        terms_conditions = request.form.get('terms_conditions', '')
        
        # Calculate amounts
        tax_amount = (subtotal_amount - discount_amount) * (tax_rate / 100)
        total_amount = subtotal_amount + tax_amount - discount_amount
        
        # Set payment date if status is paid
        payment_date = None
        if status == 'paid' and request.form.get('payment_date'):
            payment_date = request.form.get('payment_date')
        elif status == 'paid':
            from datetime import datetime
            payment_date = datetime.now().date()
        
        cur = mysql.connection.cursor()
        
        # Update invoice
        if payment_date:
            cur.execute("""
                UPDATE invoices 
                SET client_id=%s, project_id=%s, invoice_date=%s, due_date=%s, 
                    subtotal=%s, tax_rate=%s, tax_amount=%s, discount_amount=%s, 
                    total_amount=%s, currency=%s, status=%s, payment_method=%s, 
                    notes=%s, terms_conditions=%s, payment_date=%s, updated_date=NOW() 
                WHERE id = %s
            """, (client_id, project_id, invoice_date, due_date, subtotal_amount, 
                  tax_rate, tax_amount, discount_amount, total_amount, currency, 
                  status, payment_method, notes, terms_conditions, payment_date, invoice_id))
        else:
            cur.execute("""
                UPDATE invoices 
                SET client_id=%s, project_id=%s, invoice_date=%s, due_date=%s, 
                    subtotal=%s, tax_rate=%s, tax_amount=%s, discount_amount=%s, 
                    total_amount=%s, currency=%s, status=%s, payment_method=%s, 
                    notes=%s, terms_conditions=%s, updated_date=NOW() 
                WHERE id = %s
            """, (client_id, project_id, invoice_date, due_date, subtotal_amount, 
                  tax_rate, tax_amount, discount_amount, total_amount, currency, 
                  status, payment_method, notes, terms_conditions, invoice_id))
        
        mysql.connection.commit()
        cur.close()
        flash(f'Invoice updated successfully!', 'success')
    except Exception as e:
        flash(f'Error updating invoice: {e}', 'danger')
    return redirect(url_for('invoices'))

@app.route('/invoice/<int:id>')
def get_invoice(id):
    """Get invoice details for editing"""
    try:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("""
            SELECT 
                i.*,
                c.name as client_name,
                p.name as project_name
            FROM invoices i 
            LEFT JOIN clients c ON i.client_id = c.id 
            LEFT JOIN projects p ON i.project_id = p.id 
            WHERE i.id = %s
        """, (id,))
        invoice = cur.fetchone()
        cur.close()
        
        if invoice:
            return jsonify(invoice)
        else:
            return jsonify({'error': 'Invoice not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects/<int:client_id>')
def get_projects_by_client(client_id):
    """Get projects for a specific client"""
    try:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("""
            SELECT id, name 
            FROM projects 
            WHERE client_id = %s AND status != 'completed' 
            ORDER BY name
        """, (client_id,))
        projects = cur.fetchall()
        cur.close()
        return jsonify(projects)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/invoices/bulk', methods=['POST'])
def bulk_invoice_operations():
    """Handle bulk operations on invoices"""
    try:
        action = request.form.get('action')
        invoice_ids = request.form.getlist('invoice_ids[]')
        
        if not action or not invoice_ids:
            flash('No action or invoices selected!', 'warning')
            return redirect(url_for('invoices'))
        
        cur = mysql.connection.cursor()
        
        if action == 'delete':
            # Delete selected invoices
            format_strings = ','.join(['%s'] * len(invoice_ids))
            cur.execute(f"DELETE FROM invoices WHERE id IN ({format_strings})", invoice_ids)
            flash(f'{len(invoice_ids)} invoice(s) deleted successfully!', 'success')
            
        elif action in ['draft', 'sent', 'paid', 'overdue', 'cancelled']:
            # Update status for selected invoices
            format_strings = ','.join(['%s'] * len(invoice_ids))
            cur.execute(f"UPDATE invoices SET status = %s WHERE id IN ({format_strings})", [action] + invoice_ids)
            flash(f'{len(invoice_ids)} invoice(s) updated to {action} status!', 'success')
            
        elif action == 'mark_paid':
            # Mark as paid with current date
            from datetime import datetime
            payment_date = datetime.now().date()
            format_strings = ','.join(['%s'] * len(invoice_ids))
            cur.execute(f"UPDATE invoices SET status = 'paid', payment_date = %s WHERE id IN ({format_strings})", [payment_date] + invoice_ids)
            flash(f'{len(invoice_ids)} invoice(s) marked as paid!', 'success')
        
        mysql.connection.commit()
        cur.close()
        
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Error performing bulk operation: {e}', 'danger')
    
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

# Expense Management routes
@app.route('/expenses')
def expenses():
    try:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Get all expenses with detailed information
        cur.execute("""
            SELECT 
                e.id,
                e.employee_id,
                COALESCE(CONCAT(emp.first_name, ' ', emp.last_name), emp.name) as employee_name,
                e.expense_date,
                e.category,
                e.description,
                e.amount,
                e.currency,
                e.vendor_name,
                e.project_id,
                p.name as project_name,
                e.status,
                e.receipt_path,
                COALESCE(CONCAT(approver.first_name, ' ', approver.last_name), approver.name) as approved_by_name,
                e.approved_date,
                e.rejection_reason,
                e.payment_date,
                e.payment_reference,
                e.created_date,
                e.updated_date
            FROM expense_reports e
            LEFT JOIN employees emp ON e.employee_id = emp.id
            LEFT JOIN employees approver ON e.approved_by = approver.id
            LEFT JOIN projects p ON e.project_id = p.id
            ORDER BY e.created_date DESC
        """)
        expenses = cur.fetchall()
        
        # Get employees for dropdown
        cur.execute("""
            SELECT id, COALESCE(CONCAT(first_name, ' ', last_name), name) as name 
            FROM employees 
            WHERE status = 'active'
            ORDER BY first_name, last_name, name
        """)
        employees = cur.fetchall()
        
        # Get projects for dropdown
        cur.execute("SELECT id, name FROM projects WHERE status != 'completed' ORDER BY name")
        projects = cur.fetchall()
        
        # Calculate comprehensive statistics
        from datetime import datetime, timedelta
        current_month = datetime.now().replace(day=1)
        
        # Total statistics
        cur.execute("SELECT COUNT(*) as count, COALESCE(SUM(amount), 0) as total FROM expense_reports")
        total_stats = cur.fetchone()
        
        # Pending (submitted) statistics  
        cur.execute("SELECT COUNT(*) as count, COALESCE(SUM(amount), 0) as total FROM expense_reports WHERE status = 'submitted'")
        pending_stats = cur.fetchone()
        
        # Approved statistics
        cur.execute("SELECT COUNT(*) as count, COALESCE(SUM(amount), 0) as total FROM expense_reports WHERE status = 'approved'")
        approved_stats = cur.fetchone()
        
        # This month statistics
        cur.execute("SELECT COUNT(*) as count, COALESCE(SUM(amount), 0) as total FROM expense_reports WHERE expense_date >= %s", (current_month,))
        month_stats = cur.fetchone()
        
        cur.close()
        
        statistics = {
            'total': total_stats['count'] if total_stats else 0,
            'total_amount': total_stats['total'] if total_stats else 0,
            'pending': pending_stats['count'] if pending_stats else 0,
            'pending_amount': pending_stats['total'] if pending_stats else 0,
            'approved': approved_stats['count'] if approved_stats else 0,
            'approved_amount': approved_stats['total'] if approved_stats else 0,
            'this_month': month_stats['count'] if month_stats else 0,
            'this_month_amount': month_stats['total'] if month_stats else 0
        }
        
        # Add current date for form defaults
        current_date = datetime.now().date()
        
        return render_template('expenses.html', 
                             expenses=expenses, 
                             employees=employees, 
                             projects=projects, 
                             statistics=statistics,
                             current_date=current_date)
                             
    except Exception as e:
        flash(f'Error loading expenses: {e}', 'danger')
        return render_template('expenses.html', 
                             expenses=[], 
                             employees=[], 
                             projects=[], 
                             statistics={'total': 0, 'total_amount': 0, 'pending': 0, 'pending_amount': 0, 'approved': 0, 'approved_amount': 0, 'this_month': 0, 'this_month_amount': 0},
                             current_date=datetime.now().date())

@app.route('/add_expense', methods=['POST'])
def add_expense():
    try:
        # Get form data
        employee_id = request.form['employee_id']
        expense_date = request.form.get('expense_date', datetime.now().strftime('%Y-%m-%d'))
        category = request.form.get('category', 'other')
        description = request.form.get('description', '')
        amount = float(request.form['amount'])
        currency = request.form.get('currency', 'INR')
        vendor_name = request.form.get('vendor_name', '')
        project_id = request.form.get('project_id') if request.form.get('project_id') else None
        
        if not employee_id or not amount or not category:
            return jsonify({'success': False, 'error': 'Employee, amount, and category are required!'})
        
        # Handle file upload
        receipt_path = None
        if 'receipt' in request.files:
            receipt_file = request.files['receipt']
            if receipt_file.filename != '':
                # Save receipt file (implement file saving logic)
                import os
                from werkzeug.utils import secure_filename
                
                # Create uploads directory if it doesn't exist
                upload_dir = os.path.join('static', 'uploads', 'receipts')
                os.makedirs(upload_dir, exist_ok=True)
                
                filename = secure_filename(receipt_file.filename)
                receipt_path = os.path.join(upload_dir, f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}")
                receipt_file.save(receipt_path)
        
        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO expense_reports 
            (employee_id, expense_date, category, description, amount, currency, 
             vendor_name, project_id, receipt_path, status, created_date) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'submitted', NOW())
        """, (employee_id, expense_date, category, description, amount, currency, 
              vendor_name, project_id, receipt_path))
        
        mysql.connection.commit()
        cur.close()
        
        return jsonify({'success': True, 'message': 'Expense submitted successfully!'})
        
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({'success': False, 'error': f'Error adding expense: {str(e)}'})

# Additional expense routes
@app.route('/api/expense/<int:expense_id>')
def get_expense(expense_id):
    """Get expense details for editing"""
    try:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("""
            SELECT e.*, COALESCE(CONCAT(emp.first_name, ' ', emp.last_name), emp.name) as employee_name
            FROM expense_reports e 
            LEFT JOIN employees emp ON e.employee_id = emp.id 
            WHERE e.id = %s
        """, (expense_id,))
        expense = cur.fetchone()
        cur.close()
        
        if expense:
            return jsonify(expense)
        else:
            return jsonify({'error': 'Expense not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/update_expense', methods=['POST'])
def update_expense():
    try:
        expense_id = request.form['expense_id']
        status = request.form.get('status', 'submitted')
        amount = request.form.get('amount')
        rejection_reason = request.form.get('rejection_reason', '')
        
        cur = mysql.connection.cursor()
        
        # Update expense
        if amount:
            cur.execute("""
                UPDATE expense_reports 
                SET status = %s, amount = %s, rejection_reason = %s, updated_date = NOW()
                WHERE id = %s
            """, (status, amount, rejection_reason, expense_id))
        else:
            cur.execute("""
                UPDATE expense_reports 
                SET status = %s, rejection_reason = %s, updated_date = NOW()
                WHERE id = %s
            """, (status, rejection_reason, expense_id))
        
        # Set approval date if approved
        if status == 'approved':
            cur.execute("""
                UPDATE expense_reports 
                SET approved_date = NOW(), approved_by = 19
                WHERE id = %s
            """, (expense_id,))
        
        # Set payment date if paid
        if status == 'paid':
            cur.execute("""
                UPDATE expense_reports 
                SET payment_date = NOW()
                WHERE id = %s
            """, (expense_id,))
        
        mysql.connection.commit()
        cur.close()
        
        flash(f'Expense updated successfully!', 'success')
        return redirect(url_for('expenses'))
        
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Error updating expense: {e}', 'danger')
        return redirect(url_for('expenses'))

@app.route('/update_expense_status', methods=['POST'])
def update_expense_status():
    try:
        expense_id = request.form['expense_id']
        status = request.form['status']
        rejection_reason = request.form.get('rejection_reason', '')
        
        cur = mysql.connection.cursor()
        
        # Update status
        cur.execute("""
            UPDATE expense_reports 
            SET status = %s, rejection_reason = %s, updated_date = NOW()
            WHERE id = %s
        """, (status, rejection_reason, expense_id))
        
        # Set approval date if approved
        if status == 'approved':
            cur.execute("""
                UPDATE expense_reports 
                SET approved_date = NOW(), approved_by = 19
                WHERE id = %s
            """, (expense_id,))
        
        # Set payment date if paid
        if status == 'paid':
            cur.execute("""
                UPDATE expense_reports 
                SET payment_date = NOW()
                WHERE id = %s
            """, (expense_id,))
        
        mysql.connection.commit()
        cur.close()
        
        return jsonify({'success': True, 'message': f'Expense {status} successfully!'})
        
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({'success': False, 'error': f'Error updating expense: {str(e)}'})

@app.route('/expenses/bulk', methods=['POST'])
def bulk_expense_operations():
    """Handle bulk operations on expenses"""
    try:
        action = request.form.get('action')
        expense_ids = json.loads(request.form.get('expense_ids', '[]'))
        rejection_reason = request.form.get('rejection_reason', '')
        
        if not action or not expense_ids:
            return jsonify({'success': False, 'error': 'No action or expenses selected!'})
        
        cur = mysql.connection.cursor()
        
        if action == 'delete':
            # Delete selected expenses
            format_strings = ','.join(['%s'] * len(expense_ids))
            cur.execute(f"DELETE FROM expense_reports WHERE id IN ({format_strings})", expense_ids)
            message = f'{len(expense_ids)} expense(s) deleted successfully!'
            
        elif action == 'approve':
            # Approve selected expenses
            format_strings = ','.join(['%s'] * len(expense_ids))
            cur.execute(f"""
                UPDATE expense_reports 
                SET status = 'approved', approved_date = NOW(), approved_by = 19, updated_date = NOW()
                WHERE id IN ({format_strings})
            """, expense_ids)
            message = f'{len(expense_ids)} expense(s) approved successfully!'
            
        elif action == 'reject':
            # Reject selected expenses
            format_strings = ','.join(['%s'] * len(expense_ids))
            params = [rejection_reason] + expense_ids
            cur.execute(f"""
                UPDATE expense_reports 
                SET status = 'rejected', rejection_reason = %s, updated_date = NOW()
                WHERE id IN ({format_strings})
            """, params)
            message = f'{len(expense_ids)} expense(s) rejected successfully!'
            
        elif action == 'pay':
            # Mark as paid
            format_strings = ','.join(['%s'] * len(expense_ids))
            cur.execute(f"""
                UPDATE expense_reports 
                SET status = 'paid', payment_date = NOW(), updated_date = NOW()
                WHERE id IN ({format_strings})
            """, expense_ids)
            message = f'{len(expense_ids)} expense(s) marked as paid!'
        
        mysql.connection.commit()
        cur.close()
        
        return jsonify({'success': True, 'message': message})
        
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({'success': False, 'error': f'Error performing bulk operation: {str(e)}'})

@app.route('/expenses/export')
def export_expenses():
    """Export expenses to CSV"""
    try:
        # Get filter parameters
        search = request.args.get('search', '')
        status = request.args.get('status', '')
        employee = request.args.get('employee', '')
        category = request.args.get('category', '')
        
        # Build query with filters
        where_conditions = []
        params = []
        
        if search:
            where_conditions.append("(e.description LIKE %s OR emp.name LIKE %s OR e.vendor_name LIKE %s)")
            search_term = f"%{search}%"
            params.extend([search_term, search_term, search_term])
        
        if status:
            where_conditions.append("e.status = %s")
            params.append(status)
            
        if employee:
            where_conditions.append("e.employee_id = %s")
            params.append(employee)
            
        if category:
            where_conditions.append("e.category = %s")
            params.append(category)
        
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute(f"""
            SELECT 
                e.id,
                COALESCE(CONCAT(emp.first_name, ' ', emp.last_name), emp.name) as employee_name,
                e.expense_date,
                e.category,
                e.description,
                e.amount,
                e.currency,
                e.vendor_name,
                e.status,
                e.created_date
            FROM expense_reports e
            LEFT JOIN employees emp ON e.employee_id = emp.id
            {where_clause}
            ORDER BY e.created_date DESC
        """, params)
        
        expenses = cur.fetchall()
        cur.close()
        
        # Create CSV response
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['ID', 'Employee', 'Date', 'Category', 'Description', 'Amount', 'Currency', 'Vendor', 'Status', 'Created'])
        
        # Write data
        for expense in expenses:
            writer.writerow([
                expense['id'],
                expense['employee_name'],
                expense['expense_date'].strftime('%Y-%m-%d') if expense['expense_date'] else '',
                expense['category'],
                expense['description'],
                expense['amount'],
                expense['currency'] or 'INR',
                expense['vendor_name'] or '',
                expense['status'],
                expense['created_date'].strftime('%Y-%m-%d %H:%M') if expense['created_date'] else ''
            ])
        
        output.seek(0)
        
        from flask import make_response
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=expenses_{datetime.now().strftime("%Y%m%d")}.csv'
        
        return response
        
    except Exception as e:
        flash(f'Error exporting expenses: {e}', 'danger')
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

@app.route('/payroll')
def payroll():
    """Render the payroll management page"""
    try:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Get payroll statistics
        cur.execute("SELECT COUNT(*) as total_runs FROM payroll_runs")
        total_runs = cur.fetchone()['total_runs']
        
        cur.execute("SELECT COUNT(*) as active_employees FROM employees WHERE status = 'active'")
        active_employees = cur.fetchone()['active_employees']
        
        cur.execute("""
            SELECT COALESCE(SUM(basic_salary + COALESCE(allowances, 0)), 0) as monthly_payroll 
            FROM salaries WHERE is_active = 1
        """)
        monthly_payroll = cur.fetchone()['monthly_payroll']
        
        cur.execute("""
            SELECT DATE_FORMAT(MAX(created_date), '%d %b %Y') as last_run 
            FROM payroll_runs
        """)
        last_run_result = cur.fetchone()
        last_run = last_run_result['last_run'] if last_run_result['last_run'] else 'Never'
        
        # Get payroll runs
        cur.execute("""
            SELECT * FROM payroll_runs 
            ORDER BY created_date DESC
        """)
        payroll_runs = cur.fetchall()
        
        stats = {
            'total_runs': total_runs,
            'active_employees': active_employees,
            'monthly_payroll': float(monthly_payroll or 0),
            'last_run': last_run
        }
        
        cur.close()
        
        return render_template('payroll.html', 
                             stats=stats, 
                             payroll_runs=payroll_runs,
                             today=datetime.now().date())
        
    except Exception as e:
        print(f"Error loading payroll page: {e}")
        stats = {'total_runs': 0, 'active_employees': 0, 'monthly_payroll': 0, 'last_run': 'Never'}
        return render_template('payroll.html', stats=stats, payroll_runs=[], today=datetime.now().date())

@app.route('/payroll/create', methods=['POST'])
def create_payroll_run():
    """Create a new payroll run"""
    try:
        run_name = request.form.get('runName')
        pay_date = request.form.get('payDate')
        pay_period_start = request.form.get('payPeriodStart')
        pay_period_end = request.form.get('payPeriodEnd')
        notes = request.form.get('notes', '')
        
        if not all([run_name, pay_date, pay_period_start, pay_period_end]):
            flash('All required fields must be filled!', 'danger')
            return redirect(url_for('payroll'))
        
        cur = mysql.connection.cursor()
        
        # Create payroll run
        cur.execute("""
            INSERT INTO payroll_runs (run_name, pay_date, pay_period_start, pay_period_end, notes, processed_by)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (run_name, pay_date, pay_period_start, pay_period_end, notes, 'Admin'))
        
        payroll_run_id = cur.lastrowid
        
        # Get all active employees with their current salaries
        cur.execute("""
            SELECT e.id as employee_id, s.id as salary_id, s.basic_salary, s.allowances, 
                   (s.basic_salary + COALESCE(s.allowances, 0)) as gross_pay,
                   COALESCE(s.deductions, 0) as deductions,
                   (s.basic_salary + COALESCE(s.allowances, 0) - COALESCE(s.deductions, 0)) as net_pay
            FROM employees e
            JOIN salaries s ON e.id = s.employee_id
            WHERE e.status = 'active' AND s.is_active = 1
        """)
        
        employees = cur.fetchall()
        
        total_employees = len(employees)
        total_gross_pay = 0
        total_deductions = 0
        total_net_pay = 0
        
        # Create payroll entries for each employee
        for emp in employees:
            cur.execute("""
                INSERT INTO payroll_entries 
                (payroll_run_id, employee_id, salary_id, basic_salary, allowances, gross_pay, 
                 total_deductions, net_pay)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (payroll_run_id, emp[0], emp[1], emp[2], emp[3] or 0, emp[4], emp[5], emp[6]))
            
            total_gross_pay += float(emp[4])
            total_deductions += float(emp[5])
            total_net_pay += float(emp[6])
        
        # Update payroll run totals
        cur.execute("""
            UPDATE payroll_runs 
            SET total_employees = %s, total_gross_pay = %s, total_deductions = %s, total_net_pay = %s
            WHERE id = %s
        """, (total_employees, total_gross_pay, total_deductions, total_net_pay, payroll_run_id))
        
        mysql.connection.commit()
        cur.close()
        
        flash(f'Payroll run "{run_name}" created successfully with {total_employees} employees!', 'success')
        
    except Exception as e:
        mysql.connection.rollback()
        print(f"Error creating payroll run: {e}")
        flash(f'Error creating payroll run: {str(e)}', 'danger')
    
    return redirect(url_for('payroll'))

@app.route('/payroll/<int:payroll_id>')
def payroll_details(payroll_id):
    """View detailed payroll run information"""
    try:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Get payroll run details
        cur.execute("""
            SELECT * FROM payroll_runs WHERE id = %s
        """, (payroll_id,))
        payroll_run = cur.fetchone()
        
        if not payroll_run:
            flash('Payroll run not found!', 'danger')
            return redirect(url_for('payroll'))
        
        # Get payroll entries with employee details
        cur.execute("""
            SELECT pe.*, e.name as employee_name, e.email, e.employee_id as emp_code,
                   COALESCE(CONCAT(e.first_name, ' ', e.last_name), e.name) as full_name
            FROM payroll_entries pe
            JOIN employees e ON pe.employee_id = e.id
            WHERE pe.payroll_run_id = %s
            ORDER BY e.name
        """, (payroll_id,))
        payroll_entries = cur.fetchall()
        
        cur.close()
        
        return render_template('payroll_details.html', 
                             payroll_run=payroll_run, 
                             payroll_entries=payroll_entries)
        
    except Exception as e:
        print(f"Error loading payroll details: {e}")
        flash('Error loading payroll details!', 'danger')
        return redirect(url_for('payroll'))

@app.route('/payroll/<int:payroll_id>/edit', methods=['GET', 'POST'])
def edit_payroll_run(payroll_id):
    """Edit payroll run (only if status is draft)"""
    try:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        if request.method == 'POST':
            run_name = request.form.get('runName')
            pay_date = request.form.get('payDate')
            pay_period_start = request.form.get('payPeriodStart')
            pay_period_end = request.form.get('payPeriodEnd')
            notes = request.form.get('notes', '')
            
            if not all([run_name, pay_date, pay_period_start, pay_period_end]):
                flash('All required fields must be filled!', 'danger')
                return redirect(url_for('payroll_details', payroll_id=payroll_id))
            
            # Check if payroll is still in draft status
            cur.execute("SELECT status FROM payroll_runs WHERE id = %s", (payroll_id,))
            status_result = cur.fetchone()
            
            if not status_result or status_result['status'] != 'draft':
                flash('Only draft payroll runs can be edited!', 'danger')
                return redirect(url_for('payroll_details', payroll_id=payroll_id))
            
            # Update payroll run
            cur.execute("""
                UPDATE payroll_runs 
                SET run_name = %s, pay_date = %s, pay_period_start = %s, 
                    pay_period_end = %s, notes = %s, updated_date = NOW()
                WHERE id = %s
            """, (run_name, pay_date, pay_period_start, pay_period_end, notes, payroll_id))
            
            mysql.connection.commit()
            cur.close()
            
            flash('Payroll run updated successfully!', 'success')
            return redirect(url_for('payroll_details', payroll_id=payroll_id))
        
        else:
            # GET request - show edit form
            cur.execute("SELECT * FROM payroll_runs WHERE id = %s", (payroll_id,))
            payroll_run = cur.fetchone()
            
            if not payroll_run:
                flash('Payroll run not found!', 'danger')
                return redirect(url_for('payroll'))
            
            if payroll_run['status'] != 'draft':
                flash('Only draft payroll runs can be edited!', 'warning')
                return redirect(url_for('payroll_details', payroll_id=payroll_id))
            
            cur.close()
            return render_template('payroll_edit.html', payroll_run=payroll_run)
            
    except Exception as e:
        mysql.connection.rollback()
        print(f"Error editing payroll run: {e}")
        flash('Error editing payroll run!', 'danger')
        return redirect(url_for('payroll'))

@app.route('/payroll/<int:payroll_id>/delete', methods=['POST'])
def delete_payroll_run(payroll_id):
    """Delete payroll run and all associated entries"""
    try:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Check if payroll run exists and get its status
        cur.execute("SELECT run_name, status FROM payroll_runs WHERE id = %s", (payroll_id,))
        payroll_run = cur.fetchone()
        
        if not payroll_run:
            flash('Payroll run not found!', 'danger')
            return redirect(url_for('payroll'))
        
        # Only allow deletion of draft runs
        if payroll_run['status'] != 'draft':
            flash('Only draft payroll runs can be deleted!', 'warning')
            return redirect(url_for('payroll'))
        
        # Delete payroll entries first (due to foreign key constraint)
        cur.execute("DELETE FROM payroll_entries WHERE payroll_run_id = %s", (payroll_id,))
        
        # Delete the payroll run
        cur.execute("DELETE FROM payroll_runs WHERE id = %s", (payroll_id,))
        
        mysql.connection.commit()
        cur.close()
        
        flash(f'Payroll run "{payroll_run["run_name"]}" deleted successfully!', 'success')
        
    except Exception as e:
        mysql.connection.rollback()
        print(f"Error deleting payroll run: {e}")
        flash('Error deleting payroll run!', 'danger')
    
    return redirect(url_for('payroll'))

@app.route('/payroll/<int:payroll_id>/status/<new_status>')
def update_payroll_status(payroll_id, new_status):
    """Update payroll run status"""
    try:
        if new_status not in ['draft', 'processing', 'completed', 'cancelled']:
            flash('Invalid status!', 'danger')
            return redirect(url_for('payroll'))
        
        cur = mysql.connection.cursor()
        
        cur.execute("""
            UPDATE payroll_runs 
            SET status = %s, updated_date = NOW()
            WHERE id = %s
        """, (new_status, payroll_id))
        
        mysql.connection.commit()
        cur.close()
        
        flash(f'Payroll status updated to {new_status.title()}!', 'success')
        
    except Exception as e:
        mysql.connection.rollback()
        print(f"Error updating payroll status: {e}")
        flash('Error updating payroll status!', 'danger')
    
    return redirect(url_for('payroll'))

@app.route('/payroll/<int:payroll_id>/download')
def download_payroll_report(payroll_id):
    """Download payroll report as PDF or Excel"""
    try:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Get payroll run details
        cur.execute("SELECT * FROM payroll_runs WHERE id = %s", (payroll_id,))
        payroll_run = cur.fetchone()
        
        if not payroll_run:
            flash('Payroll run not found!', 'danger')
            return redirect(url_for('payroll'))
        
        # Get payroll entries with employee details
        cur.execute("""
            SELECT pe.*, e.name as employee_name, e.email, e.employee_id as emp_code,
                   COALESCE(CONCAT(e.first_name, ' ', e.last_name), e.name) as full_name
            FROM payroll_entries pe
            JOIN employees e ON pe.employee_id = e.id
            WHERE pe.payroll_run_id = %s
            ORDER BY e.name
        """, (payroll_id,))
        payroll_entries = cur.fetchall()
        
        cur.close()
        
        # For now, redirect to details page with a message
        # In a real implementation, you would generate PDF/Excel here
        flash(f'Download functionality for "{payroll_run["run_name"]}" will be available soon!', 'info')
        return redirect(url_for('payroll_details', payroll_id=payroll_id))
        
    except Exception as e:
        print(f"Error downloading payroll report: {e}")
        flash('Error preparing download!', 'danger')
        return redirect(url_for('payroll'))

@app.route('/payroll/export')
def export_payroll_data():
    """Export all payroll data"""
    try:
        # For now, show a message that export is coming soon
        flash('Export functionality will be available soon!', 'info')
        return redirect(url_for('payroll'))
        
    except Exception as e:
        print(f"Error exporting payroll data: {e}")
        flash('Error preparing export!', 'danger')
        return redirect(url_for('payroll'))

# =====================================================
# RECRUITMENT & INTERVIEW MANAGEMENT SYSTEM
# =====================================================

@app.route('/recruitment')
def recruitment_dashboard():
    """Recruitment Dashboard with Analytics"""
    try:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Get recruitment analytics
        cur.execute("""
            SELECT 
                COUNT(DISTINCT jp.id) as total_positions,
                COUNT(DISTINCT CASE WHEN jp.status = 'Open' THEN jp.id END) as open_positions,
                COUNT(DISTINCT ja.id) as total_applications,
                COUNT(DISTINCT CASE WHEN ja.status IN ('Applied', 'Under Review', 'Shortlisted') THEN ja.id END) as active_applications,
                COUNT(DISTINCT i.id) as total_interviews,
                COUNT(DISTINCT CASE WHEN i.status = 'Scheduled' THEN i.id END) as scheduled_interviews,
                COUNT(DISTINCT jo.id) as total_offers,
                COUNT(DISTINCT CASE WHEN jo.status = 'Sent' THEN jo.id END) as pending_offers
            FROM job_positions jp
            LEFT JOIN job_applications ja ON jp.id = ja.job_position_id
            LEFT JOIN interviews i ON ja.id = i.application_id
            LEFT JOIN job_offers jo ON ja.id = jo.application_id
        """)
        analytics = cur.fetchone()
        
        # Get recent applications
        cur.execute("""
            SELECT ja.*, c.first_name, c.last_name, c.email, jp.position_title,
                   COALESCE(d.name, 'No Department') as department_name,
                   DATE(ja.application_date) as app_date
            FROM job_applications ja
            JOIN candidates c ON ja.candidate_id = c.id
            JOIN job_positions jp ON ja.job_position_id = jp.id
            LEFT JOIN departments d ON jp.department_id = d.id
            ORDER BY ja.application_date DESC
            LIMIT 10
        """)
        recent_applications = cur.fetchall()
        
        # Get upcoming interviews
        cur.execute("""
            SELECT i.*, c.first_name, c.last_name, jp.position_title, it.type_name,
                   DATE(i.scheduled_date) as interview_date,
                   TIME(i.scheduled_time) as interview_time
            FROM interviews i
            JOIN job_applications ja ON i.application_id = ja.id
            JOIN candidates c ON ja.candidate_id = c.id
            JOIN job_positions jp ON ja.job_position_id = jp.id
            JOIN interview_types it ON i.interview_type_id = it.id
            WHERE i.scheduled_date >= CURDATE() AND i.status = 'Scheduled'
            ORDER BY i.scheduled_date ASC, i.scheduled_time ASC
            LIMIT 10
        """)
        upcoming_interviews = cur.fetchall()
        
        # Get pipeline statistics
        cur.execute("""
            SELECT 
                ja.status,
                COUNT(*) as count
            FROM job_applications ja
            WHERE ja.status IN ('Applied', 'Under Review', 'Shortlisted', 'Interview Scheduled', 'Interviewed', 'Selected', 'Offer Extended')
            GROUP BY ja.status
            ORDER BY FIELD(ja.status, 'Applied', 'Under Review', 'Shortlisted', 'Interview Scheduled', 'Interviewed', 'Selected', 'Offer Extended')
        """)
        pipeline_stats = cur.fetchall()
        
        cur.close()
        
        return render_template('recruitment_dashboard.html', 
                             analytics=analytics or {},
                             recent_applications=recent_applications or [],
                             upcoming_interviews=upcoming_interviews or [],
                             pipeline_stats=pipeline_stats or [])
    
    except Exception as e:
        flash(f'Error loading recruitment dashboard: {str(e)}', 'danger')
        return render_template('recruitment_dashboard.html', 
                             analytics={}, recent_applications=[], 
                             upcoming_interviews=[], pipeline_stats=[])

@app.route('/candidates')
def candidates():
    """Candidates Listing"""
    try:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Get search parameters
        search = request.args.get('search', '')
        status = request.args.get('status', '')
        source = request.args.get('source', '')
        
        # Build query
        query = """
            SELECT c.*, 
                   COUNT(ja.id) as application_count,
                   COUNT(CASE WHEN ja.status = 'Selected' THEN 1 END) as selected_count
            FROM candidates c
            LEFT JOIN job_applications ja ON c.id = ja.candidate_id
            WHERE 1=1
        """
        params = []
        
        if search:
            query += " AND (c.first_name LIKE %s OR c.last_name LIKE %s OR c.email LIKE %s OR c.current_company LIKE %s)"
            params.extend([f'%{search}%', f'%{search}%', f'%{search}%', f'%{search}%'])
            
        if status:
            query += " AND c.status = %s"
            params.append(status)
            
        if source:
            query += " AND c.source = %s"
            params.append(source)
            
        query += " GROUP BY c.id ORDER BY c.created_at DESC"
        
        cur.execute(query, params)
        candidates_list = cur.fetchall()
        
        cur.close()
        
        return render_template('candidates.html', 
                             candidates=candidates_list or [],
                             search=search,
                             selected_status=status,
                             selected_source=source)
    
    except Exception as e:
        flash(f'Error loading candidates: {str(e)}', 'danger')
        return render_template('candidates.html', candidates=[])

@app.route('/candidates/add', methods=['GET', 'POST'])
def add_candidate():
    """Add New Candidate or Edit Existing"""
    edit_id = request.args.get('edit')
    candidate = None
    
    # If editing, fetch the candidate
    if edit_id:
        try:
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cur.execute("SELECT * FROM candidates WHERE id = %s", (edit_id,))
            candidate = cur.fetchone()
            cur.close()
            
            if not candidate:
                flash('Candidate not found!', 'danger')
                return redirect(url_for('candidates'))
        except Exception as e:
            flash(f'Error loading candidate: {str(e)}', 'danger')
            return redirect(url_for('candidates'))
    
    if request.method == 'POST':
        try:
            cur = mysql.connection.cursor()
            
            if edit_id:
                # Update existing candidate
                cur.execute("""
                    UPDATE candidates SET 
                        first_name = %s, last_name = %s, email = %s, phone = %s,
                        current_company = %s, current_position = %s, current_salary = %s, 
                        expected_salary = %s, total_experience = %s, skills = %s, 
                        source = %s, notes = %s
                    WHERE id = %s
                """, (
                    request.form['first_name'],
                    request.form['last_name'], 
                    request.form['email'],
                    request.form['phone'],
                    request.form.get('current_company'),
                    request.form.get('current_position'),
                    float(request.form['current_salary']) if request.form.get('current_salary') else None,
                    float(request.form['expected_salary']) if request.form.get('expected_salary') else None,
                    float(request.form['total_experience']) if request.form.get('total_experience') else None,
                    request.form.get('skills'),
                    request.form['source'],
                    request.form.get('notes'),
                    edit_id
                ))
                flash('Candidate updated successfully!', 'success')
            else:
                # Generate candidate ID
                cur.execute("SELECT COUNT(*) as count FROM candidates")
                result = cur.fetchone()
                count = result[0] if result else 0
                candidate_id = f"CAND{str(count + 1).zfill(6)}"
                
                # Insert candidate
                cur.execute("""
                    INSERT INTO candidates (candidate_id, first_name, last_name, email, phone, 
                                          current_company, current_position, current_salary, expected_salary,
                                          total_experience, skills, source, notes)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    candidate_id,
                    request.form['first_name'],
                    request.form['last_name'], 
                    request.form['email'],
                    request.form['phone'],
                    request.form.get('current_company'),
                    request.form.get('current_position'),
                    float(request.form['current_salary']) if request.form.get('current_salary') else None,
                    float(request.form['expected_salary']) if request.form.get('expected_salary') else None,
                    float(request.form['total_experience']) if request.form.get('total_experience') else None,
                    request.form.get('skills'),
                    request.form['source'],
                    request.form.get('notes')
                ))
                flash('Candidate added successfully!', 'success')
            
            mysql.connection.commit()
            cur.close()
            
            return redirect(url_for('candidates'))
            
        except Exception as e:
            mysql.connection.rollback()
            flash(f'Error {"updating" if edit_id else "adding"} candidate: {str(e)}', 'danger')
    
    return render_template('candidate_form.html', candidate=candidate)

@app.route('/job_positions')
def job_positions():
    """Job Positions Listing"""
    try:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Get search parameters
        search = request.args.get('search', '')
        department = request.args.get('department', '')
        status = request.args.get('status', '')
        
        # Build query
        query = """
            SELECT jp.*, COALESCE(d.name, 'No Department') as department_name,
                   COUNT(ja.id) as application_count,
                   COUNT(CASE WHEN ja.status = 'Selected' THEN 1 END) as selected_count
            FROM job_positions jp
            LEFT JOIN departments d ON jp.department_id = d.id
            LEFT JOIN job_applications ja ON jp.id = ja.job_position_id
            WHERE 1=1
        """
        params = []
        
        if search:
            query += " AND (jp.position_title LIKE %s OR jp.job_description LIKE %s)"
            params.extend([f'%{search}%', f'%{search}%'])
            
        if department:
            query += " AND jp.department_id = %s"
            params.append(department)
            
        if status:
            query += " AND jp.status = %s"
            params.append(status)
            
        query += " GROUP BY jp.id ORDER BY jp.created_at DESC"
        
        cur.execute(query, params)
        positions = cur.fetchall()
        
        # Get departments for filter
        cur.execute("SELECT * FROM departments ORDER BY name")
        departments = cur.fetchall()
        
        cur.close()
        
        return render_template('job_positions.html', 
                             positions=positions or [],
                             departments=departments or [],
                             search=search,
                             selected_department=department,
                             selected_status=status)
    
    except Exception as e:
        flash(f'Error loading job positions: {str(e)}', 'danger')
        return render_template('job_positions.html', positions=[], departments=[])

@app.route('/job_positions/add', methods=['GET', 'POST'])
def add_job_position():
    """Add New Job Position"""
    if request.method == 'POST':
        try:
            cur = mysql.connection.cursor()
            
            cur.execute("""
                INSERT INTO job_positions (position_title, department_id, job_description, required_skills,
                                         experience_level, employment_type, salary_min, salary_max, location,
                                         posted_date, closing_date, created_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                request.form['position_title'],
                request.form['department_id'] if request.form['department_id'] else None,
                request.form['job_description'],
                request.form['required_skills'],
                request.form['experience_level'],
                request.form['employment_type'],
                float(request.form['salary_min']) if request.form['salary_min'] else None,
                float(request.form['salary_max']) if request.form['salary_max'] else None,
                request.form['location'],
                request.form['posted_date'],
                request.form['closing_date'] if request.form['closing_date'] else None,
                'admin'  # Replace with actual user session
            ))
            
            mysql.connection.commit()
            cur.close()
            
            flash('Job position created successfully!', 'success')
            return redirect(url_for('job_positions'))
            
        except Exception as e:
            mysql.connection.rollback()
            flash(f'Error creating job position: {str(e)}', 'danger')
    
    # GET request - show form
    try:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT * FROM departments ORDER BY name")
        departments = cur.fetchall()
        cur.close()
        
        return render_template('job_position_form.html', departments=departments or [], position=None)
    
    except Exception as e:
        flash(f'Error loading form: {str(e)}', 'danger')
        return render_template('job_position_form.html', departments=[], position=None)

@app.route('/interviews')
def interviews():
    """Interviews Listing"""
    try:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Get filter parameters
        status = request.args.get('status', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        
        # Build query
        query = """
            SELECT i.*, c.first_name, c.last_name, c.email, jp.position_title,
                   it.type_name, COALESCE(d.name, 'No Department') as department_name,
                   DATE(i.scheduled_date) as interview_date,
                   TIME(i.scheduled_time) as interview_time
            FROM interviews i
            JOIN job_applications ja ON i.application_id = ja.id
            JOIN candidates c ON ja.candidate_id = c.id
            JOIN job_positions jp ON ja.job_position_id = jp.id
            LEFT JOIN departments d ON jp.department_id = d.id
            JOIN interview_types it ON i.interview_type_id = it.id
            WHERE 1=1
        """
        params = []
        
        if status:
            query += " AND i.status = %s"
            params.append(status)
            
        if date_from:
            query += " AND i.scheduled_date >= %s"
            params.append(date_from)
            
        if date_to:
            query += " AND i.scheduled_date <= %s"
            params.append(date_to)
            
        query += " ORDER BY i.scheduled_date DESC, i.scheduled_time DESC"
        
        cur.execute(query, params)
        interviews_list = cur.fetchall()
        
        cur.close()
        
        return render_template('interviews.html', 
                             interviews=interviews_list or [],
                             selected_status=status,
                             date_from=date_from,
                             date_to=date_to)
    
    except Exception as e:
        flash(f'Error loading interviews: {str(e)}', 'danger')
        return render_template('interviews.html', interviews=[])

@app.route('/schedule_interview', methods=['GET', 'POST'])
@app.route('/edit_interview/<int:interview_id>', methods=['GET', 'POST'])
def schedule_interview(interview_id=None):
    """Schedule or Edit Interview"""
    try:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        if request.method == 'POST':
            action = request.form.get('action')
            
            if action == 'delete' and interview_id:
                # Delete interview
                cur.execute("DELETE FROM interviews WHERE id = %s", (interview_id,))
                mysql.connection.commit()
                flash('Interview deleted successfully!', 'success')
                return redirect(url_for('interviews'))
            
            elif action == 'schedule':
                # Get form data
                application_id = request.form.get('application_id')
                interview_type_id = request.form.get('interview_type_id')
                interview_round = request.form.get('interview_round')
                scheduled_date = request.form.get('scheduled_date')
                scheduled_time = request.form.get('scheduled_time')
                duration_minutes = request.form.get('duration_minutes')
                interview_mode = request.form.get('interview_mode')
                meeting_room = request.form.get('meeting_room')
                meeting_link = request.form.get('meeting_link')
                interviewer_notes = request.form.get('interviewer_notes')
                
                if interview_id:
                    # Update existing interview
                    query = """
                        UPDATE interviews SET
                        application_id = %s, interview_type_id = %s, interview_round = %s,
                        scheduled_date = %s, scheduled_time = %s, duration_minutes = %s,
                        interview_mode = %s, meeting_room = %s, meeting_link = %s,
                        interviewer_notes = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """
                    params = (application_id, interview_type_id, interview_round,
                             scheduled_date, scheduled_time, duration_minutes,
                             interview_mode, meeting_room, meeting_link,
                             interviewer_notes, interview_id)
                    
                    cur.execute(query, params)
                    flash('Interview updated successfully!', 'success')
                else:
                    # Create new interview - generate unique interview code
                    interview_code = get_unique_interview_code()
                    
                    query = """
                        INSERT INTO interviews (
                            interview_code, application_id, interview_type_id, interview_round,
                            scheduled_date, scheduled_time, duration_minutes,
                            interview_mode, meeting_room, meeting_link,
                            interviewer_notes, status, created_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Scheduled', CURRENT_TIMESTAMP)
                    """
                    params = (interview_code, application_id, interview_type_id, interview_round,
                             scheduled_date, scheduled_time, duration_minutes,
                             interview_mode, meeting_room, meeting_link,
                             interviewer_notes)
                    
                    cur.execute(query, params)
                    flash('Interview scheduled successfully!', 'success')
                
                mysql.connection.commit()
                return redirect(url_for('interviews'))
        
        # GET request - load form
        interview = None
        if interview_id:
            cur.execute("SELECT * FROM interviews WHERE id = %s", (interview_id,))
            interview = cur.fetchone()
            if not interview:
                flash('Interview not found!', 'error')
                return redirect(url_for('interviews'))
        
        # Load job applications with candidate and position details
        cur.execute("""
            SELECT ja.id, 
                   CONCAT(c.first_name, ' ', c.last_name) as candidate_name,
                   c.email as candidate_email,
                   jp.position_title,
                   COALESCE(d.name, 'No Department') as department_name
            FROM job_applications ja
            JOIN candidates c ON ja.candidate_id = c.id
            JOIN job_positions jp ON ja.job_position_id = jp.id
            LEFT JOIN departments d ON jp.department_id = d.id
            WHERE ja.status IN ('Applied', 'Under Review', 'Interview Scheduled')
            ORDER BY ja.application_date DESC
        """)
        applications = cur.fetchall()
        
        # Load interview types
        cur.execute("SELECT * FROM interview_types ORDER BY type_name")
        interview_types = cur.fetchall()
        
        cur.close()
        
        return render_template('interview_form.html',
                             interview=interview,
                             applications=applications,
                             interview_types=interview_types)
    
    except Exception as e:
        flash(f'Error loading interview form: {str(e)}', 'danger')
        return redirect(url_for('interviews'))

@app.route('/applications')
def applications():
    """Job Applications Listing"""
    try:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Get filter parameters
        status = request.args.get('status', '')
        position = request.args.get('position', '')
        date_from = request.args.get('date_from', '')
        
        # Build query
        query = """
            SELECT ja.*, 
                   c.first_name, c.last_name, c.email, c.phone, c.current_company, 
                   c.total_experience, c.skills, c.resume_path,
                   jp.position_title, 
                   COALESCE(d.name, 'No Department') as department_name
            FROM job_applications ja
            JOIN candidates c ON ja.candidate_id = c.id
            JOIN job_positions jp ON ja.job_position_id = jp.id
            LEFT JOIN departments d ON jp.department_id = d.id
            WHERE 1=1
        """
        params = []
        
        if status:
            query += " AND ja.status = %s"
            params.append(status)
            
        if position:
            query += " AND ja.job_position_id = %s"
            params.append(position)
            
        if date_from:
            query += " AND ja.application_date >= %s"
            params.append(date_from)
            
        query += " ORDER BY ja.application_date DESC"
        
        cur.execute(query, params)
        applications_list = cur.fetchall()
        
        # Get all positions for filter dropdown
        cur.execute("SELECT id, position_title FROM job_positions WHERE status = 'Open' ORDER BY position_title")
        positions = cur.fetchall()
        
        cur.close()
        
        return render_template('applications.html',
                             applications=applications_list or [],
                             positions=positions or [],
                             selected_status=status,
                             selected_position=position,
                             date_from=date_from)
    
    except Exception as e:
        flash(f'Error loading applications: {str(e)}', 'danger')
        return render_template('applications.html', applications=[], positions=[])

@app.route('/update_application_status', methods=['POST'])
def update_application_status():
    """Update Job Application Status via AJAX"""
    try:
        application_id = request.form.get('application_id')
        new_status = request.form.get('status')
        
        cur = mysql.connection.cursor()
        cur.execute("""
            UPDATE job_applications 
            SET status = %s, updated_at = CURRENT_TIMESTAMP 
            WHERE id = %s
        """, (new_status, application_id))
        mysql.connection.commit()
        cur.close()
        
        return jsonify({'success': True, 'message': 'Status updated successfully'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/recruitment_reports')
def recruitment_reports():
    """Recruitment Analytics and Reports"""
    try:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Get key metrics
        # Total applications
        cur.execute("SELECT COUNT(*) as total FROM job_applications")
        total_applications = cur.fetchone()['total']
        
        # Applications under review
        cur.execute("SELECT COUNT(*) as count FROM job_applications WHERE status = 'Under Review'")
        applications_under_review = cur.fetchone()['count']
        
        # Interviews scheduled
        cur.execute("SELECT COUNT(*) as count FROM interviews WHERE status = 'Scheduled'")
        interviews_scheduled = cur.fetchone()['count']
        
        # Offers extended
        cur.execute("SELECT COUNT(*) as count FROM job_applications WHERE status = 'Offer Extended'")
        offers_extended = cur.fetchone()['count']
        
        # Hires made
        cur.execute("SELECT COUNT(*) as count FROM job_applications WHERE status = 'Hired'")
        hires_made = cur.fetchone()['count']
        
        # Calculate rates
        conversion_rate = (hires_made / total_applications * 100) if total_applications > 0 else 0
        interview_success_rate = (offers_extended / interviews_scheduled * 100) if interviews_scheduled > 0 else 0
        offer_acceptance_rate = (hires_made / offers_extended * 100) if offers_extended > 0 else 0
        
        # Average time to hire (mock data for now)
        average_time_to_hire = 21
        
        # Top performing positions
        cur.execute("""
            SELECT jp.position_title, 
                   COALESCE(d.name, 'No Department') as department_name,
                   COUNT(ja.id) as application_count,
                   SUM(CASE WHEN ja.status = 'Interview Scheduled' THEN 1 ELSE 0 END) as interview_count,
                   SUM(CASE WHEN ja.status = 'Offer Extended' THEN 1 ELSE 0 END) as offer_count,
                   SUM(CASE WHEN ja.status = 'Hired' THEN 1 ELSE 0 END) as hire_count
            FROM job_positions jp
            LEFT JOIN job_applications ja ON jp.id = ja.job_position_id
            LEFT JOIN departments d ON jp.department_id = d.id
            GROUP BY jp.id, jp.position_title, d.name
            HAVING COUNT(ja.id) > 0
            ORDER BY hire_count DESC, application_count DESC
            LIMIT 10
        """)
        top_positions = cur.fetchall()
        
        # Recent activities (mock data)
        recent_activities = [
            {
                'icon': 'user-plus',
                'color': 'success',
                'title': 'New Application Received',
                'description': 'John Doe applied for Software Developer position',
                'timestamp': datetime.now()
            },
            {
                'icon': 'calendar-check',
                'color': 'info',
                'title': 'Interview Scheduled',
                'description': 'Interview scheduled with Sarah Smith for Marketing Manager',
                'timestamp': datetime.now()
            },
            {
                'icon': 'handshake',
                'color': 'warning',
                'title': 'Offer Extended',
                'description': 'Offer extended to Mike Johnson for HR Manager position',
                'timestamp': datetime.now()
            }
        ]
        
        cur.close()
        
        return render_template('recruitment_reports.html',
                             total_applications=total_applications,
                             applications_under_review=applications_under_review,
                             interviews_scheduled=interviews_scheduled,
                             offers_extended=offers_extended,
                             hires_made=hires_made,
                             conversion_rate=round(conversion_rate, 1),
                             interview_success_rate=round(interview_success_rate, 1),
                             offer_acceptance_rate=round(offer_acceptance_rate, 1),
                             average_time_to_hire=average_time_to_hire,
                             top_positions=top_positions,
                             recent_activities=recent_activities)
    
    except Exception as e:
        flash(f'Error loading reports: {str(e)}', 'danger')
        return render_template('recruitment_reports.html',
                             total_applications=0,
                             applications_under_review=0,
                             interviews_scheduled=0,
                             offers_extended=0,
                             hires_made=0,
                             conversion_rate=0,
                             interview_success_rate=0,
                             offer_acceptance_rate=0,
                             average_time_to_hire=0,
                             top_positions=[],
                             recent_activities=[])

@app.route('/offers')
def offers():
    """Job Offers Management"""
    return render_template('offers.html', title='Job Offers')

@app.route('/video_interview/<int:interview_id>')
def video_interview(interview_id):
    """Video Interview Room"""
    try:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Get interview details
        cur.execute("""
            SELECT i.*, 
                   CONCAT(c.first_name, ' ', c.last_name) as candidate_name,
                   c.email as candidate_email,
                   jp.position_title,
                   it.type_name as interview_type,
                   DATE(i.scheduled_date) as interview_date,
                   TIME(i.scheduled_time) as interview_time
            FROM interviews i
            JOIN job_applications ja ON i.application_id = ja.id
            JOIN candidates c ON ja.candidate_id = c.id
            JOIN job_positions jp ON ja.job_position_id = jp.id
            JOIN interview_types it ON i.interview_type_id = it.id
            WHERE i.id = %s
        """, (interview_id,))
        
        interview = cur.fetchone()
        if not interview:
            flash('Interview not found!', 'error')
            return redirect(url_for('interviews'))
        
        # Generate meeting ID and URL
        import uuid
        meeting_id = f"interview-{interview_id}-{str(uuid.uuid4())[:8]}"
        meeting_url = f"https://meet.jit.si/{meeting_id}"
        
        # Update meeting link in database
        cur.execute("""
            UPDATE interviews 
            SET meeting_link = %s, status = 'In Progress' 
            WHERE id = %s
        """, (meeting_url, interview_id))
        mysql.connection.commit()
        
        cur.close()
        
        return render_template('video_interview.html',
                             interview=interview,
                             meeting_id=meeting_id,
                             meeting_url=meeting_url)
    
    except Exception as e:
        flash(f'Error loading video interview: {str(e)}', 'danger')
        return redirect(url_for('interviews'))

@app.route('/update_interview_status/<int:interview_id>', methods=['POST'])
def update_interview_status(interview_id):
    """Update Interview Status via AJAX"""
    try:
        status = request.form.get('status')
        
        cur = mysql.connection.cursor()
        cur.execute("""
            UPDATE interviews 
            SET status = %s, updated_at = CURRENT_TIMESTAMP 
            WHERE id = %s
        """, (status, interview_id))
        mysql.connection.commit()
        cur.close()
        
        return jsonify({'success': True})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/update_interview_notes/<int:interview_id>', methods=['POST'])
def update_interview_notes(interview_id):
    """Update Interview Notes and Feedback"""
    try:
        notes = request.form.get('notes', '')
        overall_score = request.form.get('overall_score')
        recommendation = request.form.get('recommendation')
        
        # Convert empty string to None for decimal fields
        if overall_score == '' or overall_score is None:
            overall_score = None
        else:
            try:
                overall_score = float(overall_score)
            except (ValueError, TypeError):
                overall_score = None
        
        # Handle recommendation field
        if recommendation == '' or recommendation is None:
            recommendation = None
        
        cur = mysql.connection.cursor()
        cur.execute("""
            UPDATE interviews 
            SET interviewer_notes = %s, overall_score = %s, recommendation = %s,
                status = 'Completed', updated_at = CURRENT_TIMESTAMP 
            WHERE id = %s
        """, (notes, overall_score, recommendation, interview_id))
        mysql.connection.commit()
        cur.close()
        
        flash('Interview notes saved successfully!', 'success')
        return redirect(url_for('interviews'))
    
    except Exception as e:
        flash(f'Error saving notes: {str(e)}', 'danger')
        return redirect(url_for('video_interview', interview_id=interview_id))

@app.route('/auto_save_notes/<int:interview_id>', methods=['POST'])
def auto_save_notes(interview_id):
    """Auto-save Interview Notes via AJAX"""
    try:
        notes = request.form.get('notes')
        
        cur = mysql.connection.cursor()
        cur.execute("""
            UPDATE interviews 
            SET interviewer_notes = %s, updated_at = CURRENT_TIMESTAMP 
            WHERE id = %s
        """, (notes, interview_id))
        mysql.connection.commit()
        cur.close()
        
        return jsonify({'success': True})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

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

# Route aliases for compatibility
@app.route('/add_candidate')
def add_candidate_alias():
    """Redirect to candidates/add"""
    return redirect(url_for('add_candidate'))

@app.route('/add_job_position')
def add_job_position_alias():
    """Redirect to job_positions/add"""
    return redirect(url_for('add_job_position'))

# Interview action routes
@app.route('/start_interview/<int:interview_id>')
def start_interview(interview_id):
    """Start Interview - Redirect to Video Interview"""
    return redirect(url_for('video_interview', interview_id=interview_id))

@app.route('/reschedule_interview/<int:interview_id>')
def reschedule_interview(interview_id):
    """Reschedule Interview"""
    # Redirect to interview form for editing
    return redirect(url_for('interviews') + f'?edit={interview_id}')

@app.route('/cancel_interview/<int:interview_id>', methods=['POST'])
def cancel_interview(interview_id):
    """Cancel Interview"""
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            UPDATE interviews 
            SET status = 'Cancelled', updated_at = CURRENT_TIMESTAMP 
            WHERE id = %s
        """, (interview_id,))
        mysql.connection.commit()
        cur.close()
        
        flash('Interview cancelled successfully!', 'success')
        return jsonify({'success': True})
    
    except Exception as e:
        flash(f'Error cancelling interview: {str(e)}', 'danger')
        return jsonify({'success': False, 'message': str(e)})

@app.route('/complete_interview/<int:interview_id>', methods=['POST'])
def complete_interview(interview_id):
    """Complete Interview"""
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            UPDATE interviews 
            SET status = 'Completed', updated_at = CURRENT_TIMESTAMP 
            WHERE id = %s
        """, (interview_id,))
        mysql.connection.commit()
        cur.close()
        
        flash('Interview marked as completed!', 'success')
        return jsonify({'success': True})
    
    except Exception as e:
        flash(f'Error completing interview: {str(e)}', 'danger')
        return jsonify({'success': False, 'message': str(e)})

@app.route('/view_feedback/<int:interview_id>')
def view_feedback(interview_id):
    """View Interview Feedback"""
    try:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("""
            SELECT i.*, c.first_name, c.last_name, jp.position_title,
                   it.type_name as interview_type
            FROM interviews i
            JOIN job_applications ja ON i.application_id = ja.id
            JOIN candidates c ON ja.candidate_id = c.id
            JOIN job_positions jp ON ja.job_position_id = jp.id
            JOIN interview_types it ON i.interview_type_id = it.id
            WHERE i.id = %s
        """, (interview_id,))
        interview = cur.fetchone()
        cur.close()
        
        if not interview:
            flash('Interview not found!', 'danger')
            return redirect(url_for('interviews'))
        
        return render_template('interview_feedback.html', interview=interview)
    
    except Exception as e:
        flash(f'Error loading interview feedback: {str(e)}', 'danger')
        return redirect(url_for('interviews'))

@app.route('/download_report/<int:interview_id>')
def download_report(interview_id):
    """Download Interview Report"""
    flash('Interview report download feature coming soon!', 'info')
    return redirect(url_for('interviews'))

@app.route('/view_details/<int:interview_id>')
def view_details(interview_id):
    """View Interview Details"""
    try:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("""
            SELECT i.*, c.first_name, c.last_name, c.email, c.phone,
                   jp.position_title, jp.job_description,
                   it.type_name as interview_type,
                   COALESCE(d.name, 'No Department') as department_name
            FROM interviews i
            JOIN job_applications ja ON i.application_id = ja.id
            JOIN candidates c ON ja.candidate_id = c.id
            JOIN job_positions jp ON ja.job_position_id = jp.id
            JOIN interview_types it ON i.interview_type_id = it.id
            LEFT JOIN departments d ON jp.department_id = d.id
            WHERE i.id = %s
        """, (interview_id,))
        interview = cur.fetchone()
        cur.close()
        
        if not interview:
            flash('Interview not found!', 'danger')
            return redirect(url_for('interviews'))
        
        return render_template('interview_details.html', interview=interview)
    
    except Exception as e:
        flash(f'Error loading interview details: {str(e)}', 'danger')
        return redirect(url_for('interviews'))

# Application action routes
@app.route('/update_status/<int:application_id>/<status>', methods=['POST'])
def update_status(application_id, status):
    """Update Application Status"""
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            UPDATE job_applications 
            SET status = %s, updated_at = CURRENT_TIMESTAMP 
            WHERE id = %s
        """, (status, application_id))
        mysql.connection.commit()
        cur.close()
        
        return jsonify({'success': True, 'message': f'Status updated to {status}'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/download_resume/<int:application_id>')
def download_resume(application_id):
    """Download Candidate Resume"""
    flash('Resume download feature coming soon!', 'info')
    return redirect(url_for('applications'))

@app.route('/send_message/<int:application_id>')
def send_message(application_id):
    """Send Message to Candidate"""
    flash('Messaging feature coming soon!', 'info')
    return redirect(url_for('applications'))

@app.route('/view_profile/<int:candidate_id>')
def view_profile(candidate_id):
    """View Candidate Profile"""
    try:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("""
            SELECT c.*, 
                   COUNT(ja.id) as total_applications,
                   COUNT(CASE WHEN ja.status = 'Selected' THEN 1 END) as successful_applications
            FROM candidates c
            LEFT JOIN job_applications ja ON c.id = ja.candidate_id
            WHERE c.id = %s
            GROUP BY c.id
        """, (candidate_id,))
        candidate = cur.fetchone()
        
        # Get candidate's application history
        cur.execute("""
            SELECT ja.*, jp.position_title, jp.department_id,
                   COALESCE(d.name, 'No Department') as department_name
            FROM job_applications ja
            JOIN job_positions jp ON ja.job_position_id = jp.id
            LEFT JOIN departments d ON jp.department_id = d.id
            WHERE ja.candidate_id = %s
            ORDER BY ja.application_date DESC
        """, (candidate_id,))
        applications = cur.fetchall()
        
        cur.close()
        
        if not candidate:
            flash('Candidate not found!', 'danger')
            return redirect(url_for('candidates'))
        
        return render_template('candidate_profile.html', candidate=candidate, applications=applications)
    
    except Exception as e:
        flash(f'Error loading candidate profile: {str(e)}', 'danger')
        return redirect(url_for('candidates'))

@app.route('/candidate_action', methods=['POST'])
def candidate_action():
    """Handle candidate actions via AJAX"""
    try:
        data = request.get_json()
        action = data.get('action')
        candidate_id = data.get('candidate_id')
        
        if not action or not candidate_id:
            return jsonify({'success': False, 'message': 'Missing required parameters'})
        
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        if action == 'update_status':
            status = data.get('status')
            if not status:
                return jsonify({'success': False, 'message': 'Status is required'})
            
            cur.execute("UPDATE candidates SET status = %s WHERE id = %s", (status, candidate_id))
            mysql.connection.commit()
            
            return jsonify({'success': True, 'message': 'Status updated successfully'})
        
        elif action == 'send_message':
            message = data.get('message')
            if not message:
                return jsonify({'success': False, 'message': 'Message is required'})
            
            # Here you would typically integrate with an email service or messaging system
            # For now, we'll just log the action and return success
            print(f"Message to candidate {candidate_id}: {message}")
            
            return jsonify({'success': True, 'message': 'Message sent successfully'})
        
        elif action == 'delete':
            # Check if candidate has any applications and show warning
            cur.execute("SELECT COUNT(*) as app_count FROM job_applications WHERE candidate_id = %s", (candidate_id,))
            app_count = cur.fetchone()['app_count']
            
            # Check if candidate has any interviews through applications
            cur.execute("""
                SELECT COUNT(*) as interview_count 
                FROM interviews i 
                JOIN job_applications ja ON i.application_id = ja.id 
                WHERE ja.candidate_id = %s
            """, (candidate_id,))
            interview_count = cur.fetchone()['interview_count']
            
            # Get candidate name for the confirmation message
            cur.execute("SELECT first_name, last_name FROM candidates WHERE id = %s", (candidate_id,))
            candidate_info = cur.fetchone()
            
            if not candidate_info:
                return jsonify({'success': False, 'message': 'Candidate not found'})
            
            candidate_name = f"{candidate_info['first_name']} {candidate_info['last_name']}"
            
            # Delete the candidate (CASCADE will handle related records)
            cur.execute("DELETE FROM candidates WHERE id = %s", (candidate_id,))
            mysql.connection.commit()
            
            # Prepare success message with details
            message = f'Candidate "{candidate_name}" deleted successfully'
            if app_count > 0 or interview_count > 0:
                details = []
                if app_count > 0:
                    details.append(f"{app_count} application(s)")
                if interview_count > 0:
                    details.append(f"{interview_count} interview(s)")
                message += f" (along with {" and ".join(details)})"
            
            return jsonify({'success': True, 'message': message})
        
        else:
            return jsonify({'success': False, 'message': 'Invalid action'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})
    
    finally:
        if 'cur' in locals():
            cur.close()

if __name__ == '__main__':
    app.run(debug=True)
