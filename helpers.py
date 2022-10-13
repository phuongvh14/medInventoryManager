from flask import redirect, render_template, session
from functools import wraps


# Render apology message to user
def apology(message, code=400):
    """Render apology to user when something went wrong"""
    def escape(s):
        """Escape special characters"""
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


# Decoration function to require users to log in
def login_required(f):
    """
    Require log-in in routes by means of decorated function
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, ** kwargs)
    return decorated_function


# Function to format VND value
def vnd(value):
    """
    :param value: The value of money we want to format
    :return: The value with commas separating thousands
    """
    return f"{value:,}".replace(",", ".")