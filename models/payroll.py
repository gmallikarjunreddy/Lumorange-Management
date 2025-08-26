class PayrollReport:
    def __init__(self, id, month, year, employee_id, basic_salary, allowances, deductions, net_salary, status):
        self.id = id
        self.month = month
        self.year = year
        self.employee_id = employee_id
        self.basic_salary = basic_salary
        self.allowances = allowances
        self.deductions = deductions
        self.net_salary = net_salary
        self.status = status
