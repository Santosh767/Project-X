import re
from datetime import datetime, date

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """Validate phone number (10 digits)"""
    pattern = r'^\d{10}$'
    return re.match(pattern, phone) is not None

def validate_password(password):
    """Validate password strength (min 6 characters)"""
    return len(password) >= 6

def validate_date(date_string):
    """Validate date format YYYY-MM-DD"""
    try:
        datetime.strptime(date_string, '%Y-%m-%d')
        return True
    except ValueError:
        return False

def validate_time(time_string):
    """Validate time format HH:MM"""
    try:
        datetime.strptime(time_string, '%H:%M')
        return True
    except ValueError:
        return False