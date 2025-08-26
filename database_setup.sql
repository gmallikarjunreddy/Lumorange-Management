-- Lumorange Management System Database Schema
-- Execute this SQL script to create the required database structure

USE lumorange_db;

-- Drop existing tables if they exist (in reverse order due to foreign keys)
DROP TABLE IF EXISTS expense_reports;
DROP TABLE IF EXISTS performance_reviews;  
DROP TABLE IF EXISTS leave_requests;
DROP TABLE IF EXISTS attendance;
DROP TABLE IF EXISTS payroll_reports;
DROP TABLE IF EXISTS employee_projects;
DROP TABLE IF EXISTS invoices;
DROP TABLE IF EXISTS projects;
DROP TABLE IF EXISTS salaries;
DROP TABLE IF EXISTS employees;
DROP TABLE IF EXISTS clients;
DROP TABLE IF EXISTS departments;

-- Create departments table
CREATE TABLE departments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    budget DECIMAL(15,2) DEFAULT 0,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Create clients table
CREATE TABLE clients (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    email VARCHAR(100),
    phone VARCHAR(20),
    address TEXT,
    contact_person VARCHAR(100),
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Create employees table
CREATE TABLE employees (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id VARCHAR(20) UNIQUE NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
    position VARCHAR(100),
    department_id INT,
    salary DECIMAL(10,2) DEFAULT 0,
    hire_date DATE,
    status ENUM('active', 'inactive', 'terminated') DEFAULT 'active',
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE SET NULL
);

-- Create projects table  
CREATE TABLE projects (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    description TEXT,
    department_id INT,
    client_id INT,
    status ENUM('Planned', 'In Progress', 'Completed', 'On Hold', 'Cancelled') DEFAULT 'Planned',
    budget DECIMAL(15,2) DEFAULT 0,
    progress INT DEFAULT 0,
    start_date DATE,
    end_date DATE,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE SET NULL,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE SET NULL
);

-- Create salaries table
CREATE TABLE salaries (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id INT NOT NULL,
    basic_salary DECIMAL(10,2) NOT NULL,
    allowances DECIMAL(10,2) DEFAULT 0,
    deductions DECIMAL(10,2) DEFAULT 0,
    net_salary DECIMAL(10,2) GENERATED ALWAYS AS (basic_salary + allowances - deductions) STORED,
    effective_date DATE NOT NULL,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
);

-- Create invoices table
CREATE TABLE invoices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    client_id INT NOT NULL,
    project_id INT,
    invoice_number VARCHAR(50) UNIQUE NOT NULL,
    invoice_date DATE DEFAULT (CURRENT_DATE),
    due_date DATE NOT NULL,
    subtotal_amount DECIMAL(15,2) NOT NULL,
    tax_rate DECIMAL(5,2) DEFAULT 0,
    tax_amount DECIMAL(15,2) GENERATED ALWAYS AS (subtotal_amount * tax_rate / 100) STORED,
    total_amount DECIMAL(15,2) GENERATED ALWAYS AS (subtotal_amount + (subtotal_amount * tax_rate / 100)) STORED,
    status ENUM('draft', 'sent', 'paid', 'overdue', 'cancelled') DEFAULT 'draft',
    notes TEXT,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL
);

-- Create employee_projects table (assignment table)
CREATE TABLE employee_projects (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id INT NOT NULL,
    project_id INT NOT NULL,
    role VARCHAR(100) NOT NULL,
    assigned_date DATE DEFAULT (CURRENT_DATE),
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    UNIQUE KEY unique_assignment (employee_id, project_id)
);

-- Create payroll_reports table
CREATE TABLE payroll_reports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id INT NOT NULL,
    month INT NOT NULL,
    year INT NOT NULL,
    basic_salary DECIMAL(10,2) NOT NULL,
    allowances DECIMAL(10,2) DEFAULT 0,
    deductions DECIMAL(10,2) DEFAULT 0,
    net_salary DECIMAL(10,2) GENERATED ALWAYS AS (basic_salary + allowances - deductions) STORED,
    status ENUM('draft', 'processed', 'paid') DEFAULT 'draft',
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
    UNIQUE KEY unique_payroll (employee_id, month, year)
);

-- Create attendance table
CREATE TABLE attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id INT NOT NULL,
    date DATE NOT NULL,
    check_in TIME,
    check_out TIME,
    break_duration INT DEFAULT 0, -- in minutes
    total_hours DECIMAL(4,2) DEFAULT 0,
    status ENUM('present', 'absent', 'late', 'half_day') DEFAULT 'present',
    notes TEXT,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
    UNIQUE KEY unique_attendance (employee_id, date)
);

-- Create leave_requests table
CREATE TABLE leave_requests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id INT NOT NULL,
    leave_type ENUM('sick', 'casual', 'annual', 'maternity', 'paternity', 'emergency') NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    days_requested INT NOT NULL,
    reason TEXT,
    status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
    approved_by INT,
    approved_date DATE,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
    FOREIGN KEY (approved_by) REFERENCES employees(id) ON DELETE SET NULL
);

-- Create performance_reviews table
CREATE TABLE performance_reviews (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id INT NOT NULL,
    reviewer_id INT NOT NULL,
    review_period_start DATE NOT NULL,
    review_period_end DATE NOT NULL,
    overall_rating ENUM('excellent', 'good', 'satisfactory', 'needs_improvement', 'unsatisfactory') NOT NULL,
    goals_achieved TEXT,
    areas_for_improvement TEXT,
    comments TEXT,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
    FOREIGN KEY (reviewer_id) REFERENCES employees(id) ON DELETE CASCADE
);

-- Create expense_reports table
CREATE TABLE expense_reports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id INT NOT NULL,
    expense_date DATE NOT NULL,
    category ENUM('travel', 'food', 'supplies', 'training', 'utilities', 'other') NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    description TEXT NOT NULL,
    receipt_url VARCHAR(255),
    status ENUM('pending', 'approved', 'rejected', 'reimbursed') DEFAULT 'pending',
    approved_by INT,
    approved_date DATE,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
    FOREIGN KEY (approved_by) REFERENCES employees(id) ON DELETE SET NULL
);

-- Insert sample data
INSERT INTO departments (name, description, budget) VALUES
('Information Technology', 'Handles all IT operations and development', 500000.00),
('Human Resources', 'Manages employee relations and policies', 200000.00),
('Finance', 'Handles company finances and accounting', 300000.00),
('Marketing', 'Manages marketing and promotional activities', 250000.00);

INSERT INTO clients (name, email, phone, contact_person, address) VALUES
('Tech Solutions Inc', 'contact@techsolutions.com', '+1-555-0101', 'John Smith', '123 Tech Street, Silicon Valley, CA'),
('Global Marketing Co', 'info@globalmarketing.com', '+1-555-0102', 'Sarah Johnson', '456 Marketing Ave, New York, NY'),
('Finance Partners LLC', 'hello@financepartners.com', '+1-555-0103', 'Mike Brown', '789 Finance Blvd, Chicago, IL');

INSERT INTO employees (employee_id, first_name, last_name, email, phone, position, department_id, salary, hire_date) VALUES
('EMP001', 'Alice', 'Johnson', 'alice.johnson@lumorange.com', '+1-555-1001', 'Senior Developer', 1, 85000.00, '2024-01-15'),
('EMP002', 'Bob', 'Smith', 'bob.smith@lumorange.com', '+1-555-1002', 'HR Manager', 2, 75000.00, '2024-02-01'),
('EMP003', 'Carol', 'Davis', 'carol.davis@lumorange.com', '+1-555-1003', 'Financial Analyst', 3, 70000.00, '2024-03-10'),
('EMP004', 'David', 'Wilson', 'david.wilson@lumorange.com', '+1-555-1004', 'Marketing Specialist', 4, 65000.00, '2024-04-05');

INSERT INTO projects (name, description, department_id, client_id, status, budget, progress, start_date, end_date) VALUES
('Website Redesign', 'Complete redesign of client website', 1, 1, 'In Progress', 50000.00, 65, '2024-06-01', '2024-12-31'),
('HR System Implementation', 'New HR management system setup', 2, NULL, 'Planned', 75000.00, 0, '2024-09-01', '2025-03-31'),
('Financial Audit', 'Annual financial audit and compliance check', 3, 3, 'Completed', 25000.00, 100, '2024-01-01', '2024-06-30'),
('Marketing Campaign', 'Q4 marketing campaign for product launch', 4, 2, 'In Progress', 40000.00, 45, '2024-07-01', '2024-11-30');

-- Show tables created
SHOW TABLES;

SELECT 'Database schema created successfully!' as status;
