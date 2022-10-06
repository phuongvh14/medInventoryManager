import os
from tabnanny import check

from flask import Flask, flash, render_template, redirect, request, session
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology,  login_required, vnd

# Secret code to register
SECRET_CODE = "capxach"

# Configure application
app = Flask(__name__)

# Ensure application is auto-loaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filters
app.jinja_env.filters["vnd"] = vnd

# Configure session to use file system (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Create database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///medicine-inventory.db"
# Silence the deprication warning in the console
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# Create all the tables:
class User(db.Model):
    user_id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.Text, unique = True, nullable = False)
    hash = db.Column(db.Text, nullable = False)
    user_type = db.Column(db.Text, nullable = False, default = "non-admin")

db.create_all()

# Making sure that responses aren't cached
@app.after_request
def after_request(response):
    '''Ensure responses aren't cached'''
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Determining all different routes:
@app.route("/")
@login_required
def index():
    '''Show portfolio of medicine: med_id, med_name, current_inventory, latest_price'''
    return apology("TODO")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    
    # Make sure all sessions are clear when user click on the link
    session.clear()

    # Render the log in form for user to log in 
    if request.method == "GET":
        return render_template("login.html")

    # Log user in if information matches
    else:
        # Make sure user submitted username, password
        if not request.form.get("username"):
            return apology("Thieu ten dang nhap!", 403)
        elif not request.form.get("password"):
            return apology("Thieu mat khau!", 403)

        # When we are sure that users have submitted both username and password, time to query database
        rows = User.query.filter_by(username=request.form.get("username")).all()

        # Check if username is unique, and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0].hash, request.form.get("password")):
            return apology("Ten dang nhap/Mat khau sai!", 403)
        
        # Else, we know that all conditions are satisfied, log user in
        session["user_id"] = rows[0].user_id

        # Redirect to homepage
        return redirect("/")


@app.route("/logout")
def logout():
    """Log user out"""
    
    # Log user out by forgetting any user_id
    session.clear()

    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # Render register form if method is GET
    if request.method == "GET":
        return render_template("register.html")

    # If method is POST, deal with information user's information
    else:
        username = request.form.get("username")
        password = request.form.get("password")
        pw_cf = request.form.get("confirmation")
        code_entered = request.form.get("secret_code")

        # Perform several checks of the information received from user:
        if not username:
            return apology("Thieu ten dang nhap", 400)
        if not password or not pw_cf:
            return apology("Thieu mat khau va xac nhan", 400)
        if not code_entered:
            return apology("Thieu code (Khong duoc cap quyen dang ki)", 400)
        if password != pw_cf:
            return apology("Mat khau va xac nhan khong khop", 400)

        # Finally, when all fields are submitted and is valid, check for uniqueness of username
        if len(User.query.filter_by(username=username).all()) == 0 and code_entered == SECRET_CODE:
            # we then add the new user to our data base
            new_user = User(
                username=username,
                hash=generate_password_hash(password, method='pbkdf2:sha256', salt_length=8),
                user_type="authorized"
            )
            db.session.add(new_user)
            db.session.commit()

            # Finally, we are ready to log the user in 
            session["user_id"] = User.query.filter_by(username=username).first().user_id
            flash("Đăng kí thành công!")
            return redirect("/")

        else: 
            return apology("Ten dang nhap da ton tai/ Khong duoc cap quyen dang ki", 400)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Let user buy medicine"""
    return apology("TODO")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Let user sell medicine to different places"""
    return apology("TODO")


@app.route("/history", methods=["GET", "POST"])
@login_required
def history():
    """Let user see all transactions and filter data"""
    return apology("TODO")


@app.route("/update", methods=["GET", "POST"])
@login_required
def update():
    """Allow user to add new medicine, or update an existing record"""
    return apology("TODO")


@app.route("/receive", methods=["GET", "POST"])
def receive():
    """Allow non-admin user to confirm the arrival of medicine to their clinic"""
    return apology("TODO")


# Run the app
if __name__ == "__main__":
    app.run()

