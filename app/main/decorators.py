
from flask import flash, redirect, url_for
from flask_login import current_user
from functools import wraps

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("You must be logged in to access this page.", "warning")
            return redirect(url_for("main.login"))
        
        role: str = current_user.role
        if not role or role != 'admin':
            flash("You do not have permission to access this page.", "danger")
            return redirect(url_for("main.index_page"))
        
        return fn(*args, **kwargs)
    return wrapper
