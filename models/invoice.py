class Invoice:
    def __init__(self, id, client_id, invoice_number, invoice_date, due_date, project_id, amount, tax_rate, total_amount, status, notes):
        self.id = id
        self.client_id = client_id
        self.invoice_number = invoice_number
        self.invoice_date = invoice_date
        self.due_date = due_date
        self.project_id = project_id
        self.amount = amount
        self.tax_rate = tax_rate
        self.total_amount = total_amount
        self.status = status
        self.notes = notes
