# 💰 **EXPENSE MANAGEMENT SYSTEM - DATABASE SETUP**

## Creating the expense_reports table with comprehensive fields

```sql
CREATE TABLE expense_reports (
    id INT PRIMARY KEY AUTO_INCREMENT,
    employee_id INT NOT NULL,
    expense_date DATE NOT NULL,
    category VARCHAR(100) NOT NULL,
    description TEXT,
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'INR',
    receipt_path VARCHAR(255),
    vendor_name VARCHAR(100),
    project_id INT,
    status ENUM('submitted', 'approved', 'rejected', 'paid') DEFAULT 'submitted',
    approved_by INT,
    approved_date DATETIME,
    rejection_reason TEXT,
    payment_date DATETIME,
    payment_reference VARCHAR(100),
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(id),
    FOREIGN KEY (approved_by) REFERENCES employees(id),
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

-- Sample expense categories
INSERT INTO expense_reports (employee_id, expense_date, category, description, amount, vendor_name, status) VALUES
(4, '2025-08-20', 'Travel', 'Flight tickets to client meeting', 15000.00, 'Air India', 'approved'),
(4, '2025-08-22', 'Meals', 'Client dinner meeting', 3500.00, 'The Leela Palace', 'approved'),
(4, '2025-08-23', 'Transportation', 'Uber rides for project work', 850.00, 'Uber', 'submitted'),
(4, '2025-08-24', 'Office Supplies', 'Stationery and printing', 1200.00, 'Staples', 'submitted'),
(4, '2025-08-25', 'Software', 'Monthly software subscription', 2500.00, 'Microsoft', 'pending');
```
