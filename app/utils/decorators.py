from functools import wraps
from flask import redirect, url_for
from flask_login import current_user

def profile_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_profile_complete():
            return redirect(url_for('user.complete_profile'))
        return f(*args, **kwargs)
    return decorated_function 