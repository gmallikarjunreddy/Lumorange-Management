# Lumorange Management System

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- MySQL Server
- pip (Python package installer)

### Database Setup

1. **Create Database**
   ```sql
   CREATE DATABASE lumorange_db;
   ```

2. **Run Database Schema**
   Execute the `database_setup.sql` file in MySQL:
   ```bash
   mysql -u root -p lumorange_db < database_setup.sql
   ```

3. **Update Database Credentials**
   Edit `app.py` and update the MySQL configuration:
   ```python
   app.config['MYSQL_HOST'] = 'localhost'
   app.config['MYSQL_USER'] = 'root'
   app.config['MYSQL_PASSWORD'] = 'your_password'
   app.config['MYSQL_DB'] = 'lumorange_db'
   ```

### Installation

1. **Install Dependencies**
   ```bash
   pip install flask flask-mysqldb
   ```

2. **Run Application**
   ```bash
   python app.py
   ```

3. **Access Application**
   Open your browser and go to: `http://localhost:5000`

## 📊 Features

### ✅ Current Features
- **Dashboard** - Overview with real-time statistics
- **Employee Management** - Add, view, manage employees
- **Department Management** - Organize company structure
- **Project Management** - Track project progress and assignments
- **Client Management** - Manage client relationships
- **Invoice Management** - Create and track invoices
- **Payroll System** - Generate monthly payroll reports
- **Salary Management** - Track employee salaries
- **Employee-Project Assignments** - Assign employees to projects

### 🎨 UI/UX Features
- **Modern Design** - Purple gradient theme with clean interface
- **Responsive Layout** - Works on desktop, tablet, and mobile
- **Real-time Stats** - Dynamic dashboard with live data
- **Search Functionality** - Search across all data tables
- **Modal Forms** - Clean popup forms for data entry
- **Loading States** - Visual feedback during operations
- **Error Handling** - User-friendly error pages and messages
- **Connection Status** - Real-time database connection indicator

## 🛠️ Database Schema

The system uses 13 interconnected tables:

1. **departments** - Company departments
2. **employees** - Employee information
3. **clients** - Client/customer data
4. **projects** - Project management
5. **salaries** - Employee salary records
6. **invoices** - Client invoicing
7. **employee_projects** - Project assignments
8. **payroll_reports** - Monthly payroll
9. **attendance** - Employee attendance tracking
10. **leave_requests** - Leave management
11. **performance_reviews** - Employee evaluations
12. **expense_reports** - Expense tracking
13. **clients** - Customer management

## 🔧 Configuration

### Database Connection
The application uses Flask-MySQLdb for database connectivity. Make sure your MySQL server is running and the credentials in `app.py` are correct.

### Debug Mode
The application runs in debug mode by default. For production, change:
```python
app.run(debug=False)
```

## 📱 Pages

- **/** - Dashboard with statistics and overview
- **/employees** - Employee management
- **/departments** - Department management  
- **/projects** - Project management
- **/clients** - Client management
- **/invoices** - Invoice management
- **/salaries** - Salary management
- **/payroll** - Payroll reports
- **/employee_projects** - Project assignments

## 🚨 Troubleshooting

### Database Connection Issues
1. Ensure MySQL server is running
2. Check database credentials in `app.py`
3. Verify database `lumorange_db` exists
4. Run the `database_setup.sql` script

### Common Errors
- **Column doesn't exist**: Run `database_setup.sql` to create proper schema
- **404 errors**: Ensure all template files exist in `templates/` folder
- **500 errors**: Check Flask console for detailed error messages

### Performance Tips
- Use connection pooling for production
- Add database indexes for large datasets
- Implement caching for frequently accessed data
- Use pagination for large result sets

## 🎯 Next Steps

### Planned Features
- **Attendance Tracking** - Clock in/out functionality
- **Leave Management** - Leave request workflow
- **Performance Reviews** - Employee evaluation system
- **Expense Tracking** - Business expense management
- **Reports & Analytics** - Advanced reporting features
- **User Authentication** - Login and role-based access
- **Email Notifications** - Automated email alerts
- **API Integration** - REST API for external integrations

---

**Lumorange Management System** - Built with Flask, MySQL, and Bootstrap 5