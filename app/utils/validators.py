import re

def validate_phone(phone):
    # Indian phone number validation (10 digits, optionally starting with +91)
    pattern = r'^(?:\+91)?[6-9]\d{9}$'
    return bool(re.match(pattern, phone))

def validate_email(email):
    # Basic email validation
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_pincode(pincode):
    # Indian PIN code validation (6 digits)
    pattern = r'^\d{6}$'
    return bool(re.match(pattern, pincode))

def validate_password(password):
    # Password validation
    # At least 8 characters
    # Must contain at least one uppercase letter
    # Must contain at least one lowercase letter
    # Must contain at least one number
    # Must contain at least one special character
    if len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'\d', password):
        return False
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False
    return True

def validate_username(username):
    # Username validation
    # 5-30 characters
    # Can contain letters, numbers, and underscores
    # Must start with a letter
    pattern = r'^[a-zA-Z][a-zA-Z0-9_]{4,29}$'
    return bool(re.match(pattern, username)) 