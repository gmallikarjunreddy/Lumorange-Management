"""
Security Enhancement Script for Lumorange Management System
Implements CSRF protection, input validation, and security headers
"""

from flask import request, session, abort, g
from functools import wraps
import hashlib
import secrets
import re
from datetime import datetime, timedelta
import html

class SecurityManager:
    """Comprehensive security management for the application"""
    
    def __init__(self, app):
        self.app = app
        self.setup_security_headers()
        self.setup_csrf_protection()
    
    def setup_security_headers(self):
        """Add security headers to all responses"""
        
        @self.app.after_request
        def add_security_headers(response):
            # Prevent XSS attacks
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            
            # Content Security Policy
            csp = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self';"
            )
            response.headers['Content-Security-Policy'] = csp
            
            # Prevent MIME sniffing
            response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            
            return response
    
    def setup_csrf_protection(self):
        """Setup CSRF token protection"""
        
        @self.app.before_request
        def csrf_protect():
            if request.method == "POST":
                token = session.get('_csrf_token', None)
                if not token or token != request.form.get('_csrf_token'):
                    if not request.is_json:  # Allow JSON API requests for now
                        abort(403)
        
        def generate_csrf_token():
            if '_csrf_token' not in session:
                session['_csrf_token'] = secrets.token_hex(16)
            return session['_csrf_token']
        
        self.app.jinja_env.globals['csrf_token'] = generate_csrf_token
    
    @staticmethod
    def validate_email(email):
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_phone(phone):
        """Validate phone number format"""
        pattern = r'^[\+]?[1-9][\d]{0,15}$'
        return re.match(pattern, phone.replace(' ', '').replace('-', '')) is not None
    
    @staticmethod
    def sanitize_input(data):
        """Sanitize user input to prevent XSS"""
        if isinstance(data, str):
            return html.escape(data.strip())
        elif isinstance(data, dict):
            return {key: SecurityManager.sanitize_input(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [SecurityManager.sanitize_input(item) for item in data]
        return data
    
    @staticmethod
    def validate_amount(amount):
        """Validate monetary amounts"""
        try:
            amount_float = float(amount)
            return 0 <= amount_float <= 10000000  # Max 10 million
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_date(date_string):
        """Validate date format"""
        try:
            datetime.strptime(date_string, '%Y-%m-%d')
            return True
        except ValueError:
            return False

class InputValidator:
    """Comprehensive input validation"""
    
    VALIDATION_RULES = {
        'employee': {
            'name': {
                'required': True,
                'min_length': 2,
                'max_length': 100,
                'pattern': r'^[a-zA-Z\s]+$'
            },
            'email': {
                'required': True,
                'validator': SecurityManager.validate_email
            },
            'phone': {
                'required': False,
                'validator': SecurityManager.validate_phone
            },
            'salary': {
                'required': True,
                'validator': SecurityManager.validate_amount
            }
        },
        'invoice': {
            'client_id': {
                'required': True,
                'type': int
            },
            'amount': {
                'required': True,
                'validator': SecurityManager.validate_amount
            },
            'due_date': {
                'required': True,
                'validator': SecurityManager.validate_date
            }
        },
        'expense': {
            'amount': {
                'required': True,
                'validator': SecurityManager.validate_amount
            },
            'category': {
                'required': True,
                'choices': ['Travel', 'Office', 'Equipment', 'Marketing', 'Training', 'Other']
            },
            'expense_date': {
                'required': True,
                'validator': SecurityManager.validate_date
            }
        }
    }
    
    @staticmethod
    def validate_form_data(form_type, data):
        """Validate form data against rules"""
        rules = InputValidator.VALIDATION_RULES.get(form_type, {})
        errors = {}
        
        for field, rule in rules.items():
            value = data.get(field)
            
            # Check required fields
            if rule.get('required', False) and not value:
                errors[field] = f"{field} is required"
                continue
            
            if value:
                # Check length constraints
                if 'min_length' in rule and len(str(value)) < rule['min_length']:
                    errors[field] = f"{field} must be at least {rule['min_length']} characters"
                
                if 'max_length' in rule and len(str(value)) > rule['max_length']:
                    errors[field] = f"{field} cannot exceed {rule['max_length']} characters"
                
                # Check pattern matching
                if 'pattern' in rule and not re.match(rule['pattern'], str(value)):
                    errors[field] = f"{field} contains invalid characters"
                
                # Check choices
                if 'choices' in rule and value not in rule['choices']:
                    errors[field] = f"{field} must be one of: {', '.join(rule['choices'])}"
                
                # Custom validators
                if 'validator' in rule and not rule['validator'](value):
                    errors[field] = f"{field} is invalid"
                
                # Type checking
                if 'type' in rule:
                    try:
                        rule['type'](value)
                    except (ValueError, TypeError):
                        errors[field] = f"{field} must be of type {rule['type'].__name__}"
        
        return errors

class RateLimiter:
    """Simple rate limiting implementation"""
    
    def __init__(self):
        self.requests = {}
    
    def is_allowed(self, identifier, max_requests=100, time_window=3600):
        """Check if request is within rate limits"""
        now = datetime.now()
        
        if identifier not in self.requests:
            self.requests[identifier] = []
        
        # Clean old requests
        cutoff = now - timedelta(seconds=time_window)
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier] 
            if req_time > cutoff
        ]
        
        # Check if under limit
        if len(self.requests[identifier]) < max_requests:
            self.requests[identifier].append(now)
            return True
        
        return False

# Decorator for rate limiting
def rate_limit(max_requests=100, time_window=3600):
    """Rate limiting decorator"""
    limiter = RateLimiter()
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            identifier = request.remote_addr
            if not limiter.is_allowed(identifier, max_requests, time_window):
                abort(429)  # Too Many Requests
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Enhanced logging for security events
class SecurityLogger:
    """Security event logging"""
    
    @staticmethod
    def log_login_attempt(user_id, success, ip_address):
        """Log login attempts"""
        status = "SUCCESS" if success else "FAILED"
        print(f"[SECURITY] Login {status} - User: {user_id}, IP: {ip_address}")
    
    @staticmethod
    def log_data_access(table_name, record_id, user_id, action):
        """Log data access attempts"""
        print(f"[AUDIT] {action} - Table: {table_name}, Record: {record_id}, User: {user_id}")
    
    @staticmethod
    def log_security_violation(violation_type, details, ip_address):
        """Log security violations"""
        print(f"[VIOLATION] {violation_type} - Details: {details}, IP: {ip_address}")

# Example usage in Flask routes:
"""
from security_enhancements import SecurityManager, InputValidator, rate_limit

# Initialize security
security = SecurityManager(app)

@app.route('/add_employee', methods=['POST'])
@rate_limit(max_requests=10, time_window=60)  # 10 requests per minute
def add_employee():
    # Validate input
    errors = InputValidator.validate_form_data('employee', request.form)
    if errors:
        flash('Please correct the following errors: ' + ', '.join(errors.values()), 'danger')
        return redirect(url_for('employees'))
    
    # Sanitize input
    clean_data = SecurityManager.sanitize_input(dict(request.form))
    
    # Continue with normal processing...
"""