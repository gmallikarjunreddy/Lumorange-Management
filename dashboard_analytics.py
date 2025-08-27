"""
Enhanced Dashboard Analytics for Lumorange Management System
Provides comprehensive business intelligence and reporting
"""

from datetime import datetime, timedelta, date
from collections import defaultdict
import calendar

class DashboardAnalytics:
    """Advanced analytics for the dashboard"""
    
    def __init__(self, mysql_connection):
        self.mysql = mysql_connection
    
    def get_comprehensive_stats(self):
        """Get comprehensive dashboard statistics"""
        cur = self.mysql.connection.cursor()
        
        stats = {}
        
        try:
            # Basic Counts
            stats.update(self._get_basic_counts(cur))
            
            # Financial Metrics
            stats.update(self._get_financial_metrics(cur))
            
            # Trend Analysis
            stats.update(self._get_trend_analysis(cur))
            
            # Performance Metrics
            stats.update(self._get_performance_metrics(cur))
            
            # Recent Activities
            stats.update(self._get_recent_activities(cur))
            
            # Alerts and Notifications
            stats.update(self._get_alerts(cur))
            
        except Exception as e:
            print(f"Error getting dashboard stats: {e}")
        finally:
            cur.close()
        
        return stats
    
    def _get_basic_counts(self, cur):
        """Get basic entity counts"""
        stats = {}
        
        # Employee statistics
        cur.execute("SELECT COUNT(*) FROM employees WHERE status = 'active'")
        stats['active_employees'] = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM employees")
        stats['total_employees'] = cur.fetchone()[0]
        
        # Client statistics
        cur.execute("SELECT COUNT(*) FROM clients WHERE status = 'active'")
        stats['active_clients'] = cur.fetchone()[0]
        
        # Project statistics
        cur.execute("SELECT COUNT(*) FROM projects WHERE status = 'active'")
        stats['active_projects'] = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM projects WHERE status = 'completed'")
        stats['completed_projects'] = cur.fetchone()[0]
        
        # Department statistics
        cur.execute("SELECT COUNT(*) FROM departments")
        stats['total_departments'] = cur.fetchone()[0]
        
        return stats
    
    def _get_financial_metrics(self, cur):
        """Get financial performance metrics"""
        stats = {}
        
        # Current month date range
        today = date.today()
        first_day = today.replace(day=1)
        last_day = today.replace(day=calendar.monthrange(today.year, today.month)[1])
        
        # Invoice metrics
        cur.execute("""
            SELECT 
                COUNT(*) as total_invoices,
                COALESCE(SUM(total_amount), 0) as total_amount,
                COALESCE(SUM(CASE WHEN status = 'paid' THEN total_amount ELSE 0 END), 0) as paid_amount,
                COALESCE(SUM(CASE WHEN status = 'pending' THEN total_amount ELSE 0 END), 0) as pending_amount,
                COALESCE(SUM(CASE WHEN status = 'overdue' THEN total_amount ELSE 0 END), 0) as overdue_amount
            FROM invoices 
            WHERE invoice_date >= %s AND invoice_date <= %s
        """, (first_day, last_day))
        
        invoice_data = cur.fetchone()
        stats.update({
            'monthly_invoices': invoice_data[0],
            'monthly_invoice_total': float(invoice_data[1] or 0),
            'monthly_paid': float(invoice_data[2] or 0),
            'monthly_pending': float(invoice_data[3] or 0),
            'monthly_overdue': float(invoice_data[4] or 0)
        })
        
        # Payroll metrics
        cur.execute("""
            SELECT 
                COALESCE(SUM(basic_salary + COALESCE(allowances, 0)), 0) as total_payroll
            FROM salaries 
            WHERE is_active = 1
        """)
        stats['monthly_payroll'] = float(cur.fetchone()[0] or 0)
        
        # Expense metrics
        cur.execute("""
            SELECT 
                COUNT(*) as total_expenses,
                COALESCE(SUM(amount), 0) as total_amount,
                COALESCE(SUM(CASE WHEN status = 'approved' THEN amount ELSE 0 END), 0) as approved_amount
            FROM expense_reports 
            WHERE expense_date >= %s AND expense_date <= %s
        """, (first_day, last_day))
        
        expense_data = cur.fetchone()
        stats.update({
            'monthly_expenses_count': expense_data[0],
            'monthly_expenses_total': float(expense_data[1] or 0),
            'monthly_expenses_approved': float(expense_data[2] or 0)
        })
        
        # Calculate profit margin
        revenue = stats['monthly_paid']
        expenses = stats['monthly_expenses_approved'] + stats['monthly_payroll']
        stats['monthly_profit'] = revenue - expenses
        stats['profit_margin'] = (stats['monthly_profit'] / revenue * 100) if revenue > 0 else 0
        
        return stats
    
    def _get_trend_analysis(self, cur):
        """Get trend analysis for the last 6 months"""
        stats = {}
        
        # Get last 6 months data
        end_date = date.today()
        start_date = end_date - timedelta(days=180)
        
        # Monthly revenue trend
        cur.execute("""
            SELECT 
                DATE_FORMAT(invoice_date, '%%Y-%%m') as month,
                SUM(CASE WHEN status = 'paid' THEN total_amount ELSE 0 END) as revenue
            FROM invoices 
            WHERE invoice_date >= %s AND invoice_date <= %s
            GROUP BY DATE_FORMAT(invoice_date, '%%Y-%%m')
            ORDER BY month
        """, (start_date, end_date))
        
        revenue_trend = {row[0]: float(row[1]) for row in cur.fetchall()}
        stats['revenue_trend'] = revenue_trend
        
        # Monthly expense trend
        cur.execute("""
            SELECT 
                DATE_FORMAT(expense_date, '%%Y-%%m') as month,
                SUM(amount) as expenses
            FROM expense_reports 
            WHERE expense_date >= %s AND expense_date <= %s AND status = 'approved'
            GROUP BY DATE_FORMAT(expense_date, '%%Y-%%m')
            ORDER BY month
        """, (start_date, end_date))
        
        expense_trend = {row[0]: float(row[1]) for row in cur.fetchall()}
        stats['expense_trend'] = expense_trend
        
        # Calculate growth rates
        revenue_values = list(revenue_trend.values())
        if len(revenue_values) >= 2:
            latest_revenue = revenue_values[-1]
            previous_revenue = revenue_values[-2]
            stats['revenue_growth'] = ((latest_revenue - previous_revenue) / previous_revenue * 100) if previous_revenue > 0 else 0
        else:
            stats['revenue_growth'] = 0
        
        return stats
    
    def _get_performance_metrics(self, cur):
        """Get performance and efficiency metrics"""
        stats = {}
        
        # Invoice collection efficiency
        cur.execute("""
            SELECT 
                AVG(DATEDIFF(
                    CASE WHEN status = 'paid' THEN CURDATE() ELSE due_date END, 
                    invoice_date
                )) as avg_collection_days
            FROM invoices 
            WHERE invoice_date >= DATE_SUB(CURDATE(), INTERVAL 3 MONTH)
        """)
        result = cur.fetchone()
        stats['avg_collection_days'] = int(result[0] or 30)
        
        # Employee utilization (projects per employee)
        cur.execute("""
            SELECT 
                AVG(project_count) as avg_projects_per_employee
            FROM (
                SELECT 
                    ep.employee_id,
                    COUNT(ep.project_id) as project_count
                FROM employee_projects ep
                JOIN projects p ON ep.project_id = p.id
                WHERE p.status = 'active'
                GROUP BY ep.employee_id
            ) as emp_projects
        """)
        result = cur.fetchone()
        stats['avg_projects_per_employee'] = float(result[0] or 0)
        
        # Expense approval rate
        cur.execute("""
            SELECT 
                COUNT(CASE WHEN status = 'approved' THEN 1 END) * 100.0 / COUNT(*) as approval_rate
            FROM expense_reports 
            WHERE expense_date >= DATE_SUB(CURDATE(), INTERVAL 1 MONTH)
        """)
        result = cur.fetchone()
        stats['expense_approval_rate'] = float(result[0] or 0)
        
        return stats
    
    def _get_recent_activities(self, cur):
        """Get recent system activities"""
        stats = {}
        
        # Recent invoices
        cur.execute("""
            SELECT i.id, i.invoice_number, c.name as client_name, 
                   i.total_amount, i.status, i.invoice_date
            FROM invoices i
            JOIN clients c ON i.client_id = c.id
            ORDER BY i.invoice_date DESC
            LIMIT 5
        """)
        stats['recent_invoices'] = [
            {
                'id': row[0],
                'number': row[1],
                'client': row[2],
                'amount': float(row[3]),
                'status': row[4],
                'date': row[5]
            }
            for row in cur.fetchall()
        ]
        
        # Recent employees
        cur.execute("""
            SELECT id, name, email, status, created_date
            FROM employees
            ORDER BY created_date DESC
            LIMIT 5
        """)
        stats['recent_employees'] = [
            {
                'id': row[0],
                'name': row[1],
                'email': row[2],
                'status': row[3],
                'date': row[4]
            }
            for row in cur.fetchall()
        ]
        
        # Recent expenses
        cur.execute("""
            SELECT er.id, e.name as employee_name, er.description, 
                   er.amount, er.status, er.expense_date
            FROM expense_reports er
            JOIN employees e ON er.employee_id = e.id
            ORDER BY er.expense_date DESC
            LIMIT 5
        """)
        stats['recent_expenses'] = [
            {
                'id': row[0],
                'employee': row[1],
                'description': row[2],
                'amount': float(row[3]),
                'status': row[4],
                'date': row[5]
            }
            for row in cur.fetchall()
        ]
        
        return stats
    
    def _get_alerts(self, cur):
        """Get system alerts and notifications"""
        alerts = []
        
        # Overdue invoices
        cur.execute("""
            SELECT COUNT(*) FROM invoices 
            WHERE due_date < CURDATE() AND status != 'paid'
        """)
        overdue_count = cur.fetchone()[0]
        if overdue_count > 0:
            alerts.append({
                'type': 'warning',
                'message': f'{overdue_count} invoice(s) are overdue',
                'action': 'view_invoices',
                'priority': 'high'
            })
        
        # Pending expenses
        cur.execute("""
            SELECT COUNT(*) FROM expense_reports 
            WHERE status = 'pending'
        """)
        pending_expenses = cur.fetchone()[0]
        if pending_expenses > 0:
            alerts.append({
                'type': 'info',
                'message': f'{pending_expenses} expense(s) awaiting approval',
                'action': 'view_expenses',
                'priority': 'medium'
            })
        
        # Low project activity
        cur.execute("""
            SELECT COUNT(*) FROM projects 
            WHERE status = 'active' AND updated_date < DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        """)
        stale_projects = cur.fetchone()[0]
        if stale_projects > 0:
            alerts.append({
                'type': 'warning',
                'message': f'{stale_projects} project(s) haven\'t been updated in 30 days',
                'action': 'view_projects',
                'priority': 'medium'
            })
        
        # Salary review reminders
        cur.execute("""
            SELECT COUNT(*) FROM salaries 
            WHERE is_active = 1 AND effective_date < DATE_SUB(CURDATE(), INTERVAL 365 DAY)
        """)
        old_salaries = cur.fetchone()[0]
        if old_salaries > 0:
            alerts.append({
                'type': 'info',
                'message': f'{old_salaries} salary record(s) are over 1 year old',
                'action': 'view_salaries',
                'priority': 'low'
            })
        
        return {'alerts': alerts}

class ReportGenerator:
    """Generate various business reports"""
    
    def __init__(self, mysql_connection):
        self.mysql = mysql_connection
    
    def generate_monthly_summary(self, year, month):
        """Generate monthly business summary"""
        cur = self.mysql.connection.cursor()
        
        # Date range for the month
        start_date = date(year, month, 1)
        end_date = date(year, month, calendar.monthrange(year, month)[1])
        
        report = {
            'period': f"{calendar.month_name[month]} {year}",
            'start_date': start_date,
            'end_date': end_date
        }
        
        # Invoice summary
        cur.execute("""
            SELECT 
                COUNT(*) as count,
                SUM(total_amount) as total,
                AVG(total_amount) as average,
                SUM(CASE WHEN status = 'paid' THEN total_amount ELSE 0 END) as paid
            FROM invoices 
            WHERE invoice_date BETWEEN %s AND %s
        """, (start_date, end_date))
        
        invoice_data = cur.fetchone()
        report['invoices'] = {
            'count': invoice_data[0],
            'total': float(invoice_data[1] or 0),
            'average': float(invoice_data[2] or 0),
            'paid': float(invoice_data[3] or 0)
        }
        
        # Expense summary
        cur.execute("""
            SELECT 
                COUNT(*) as count,
                SUM(amount) as total,
                AVG(amount) as average
            FROM expense_reports 
            WHERE expense_date BETWEEN %s AND %s AND status = 'approved'
        """, (start_date, end_date))
        
        expense_data = cur.fetchone()
        report['expenses'] = {
            'count': expense_data[0],
            'total': float(expense_data[1] or 0),
            'average': float(expense_data[2] or 0)
        }
        
        # Calculate profit
        report['profit'] = report['invoices']['paid'] - report['expenses']['total']
        report['margin'] = (report['profit'] / report['invoices']['paid'] * 100) if report['invoices']['paid'] > 0 else 0
        
        cur.close()
        return report

# Example usage:
"""
from dashboard_analytics import DashboardAnalytics, ReportGenerator

# Initialize analytics
analytics = DashboardAnalytics(mysql)

# Get comprehensive dashboard data
dashboard_stats = analytics.get_comprehensive_stats()

# Generate monthly report
report_gen = ReportGenerator(mysql)
monthly_report = report_gen.generate_monthly_summary(2025, 8)
"""