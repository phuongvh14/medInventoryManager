from dotenv import load_dotenv
import os
load_dotenv()
from tabnanny import check

from flask import Flask, flash, render_template, redirect, request, session
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from helpers import apology,  login_required, vnd

# Secret code to register
SECRET_CODE = os.getenv("SECRET_CODE")

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


class Medicine(db.Model):
    med_id = db.Column(db.Integer, primary_key = True)
    med_name = db.Column(db.Text, unique = True, nullable = False)
    med_quantity = db.Column(db.Numeric, nullable = False)
    med_unit = db.Column(db.Text, nullable = False)
    med_latest_price = db.Column(db.Numeric, nullable = False)
    med_notes = db.Column(db.Text) 

class ChangedInfo(db.Model):
    change_id = db.Column(db.Integer, primary_key = True)
    changed_by = db.Column(db.Text, nullable = False)
    changed_time = db.Column(db.DateTime, nullable = False)
    client_IP = db.Column(db.Text, nullable = False)
    change_type = db.Column(db.Text, nullable = False)
    changed_from = db.Column(db.Text, nullable = False)
    changed_to = db.Column(db.Text, nullable = False)
    change_notes = db.Column(db.Text)


with app.app_context():
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
    """Allow user to update existing records, like adding new medicine, or updating a transaction"""
    if request.method == "GET":
        return render_template("update.html")
    else:
        if request.form.get("btnradio") == "add_new":
            return render_template("add_new.html")
        else:
            return render_template("correct_record.html")


@app.route("/addnew", methods=["POST"])
@login_required
def addnew():
    """Allow user to add new medicine"""
    # We first get the input from user
    med_name = request.form.get("medname")
    med_quantity = request.form.get("quantity")
    med_unit = request.form.get("medunit")
    med_price = request.form.get("latest_price")
    med_notes = request.form.get("med_notes")

    # If there is no meds in the existing database with the same name
    if len(Medicine.query.filter_by(med_name=med_name).all()) == 0:
        # We add this confirmed new medicine to the db:
        new_med = Medicine(
            med_name=med_name,
            med_unit=med_unit,
            med_quantity=med_quantity,
            med_latest_price=med_price,
            med_notes=med_notes
        )
        db.session.add(new_med)
        db.session.commit()

        # And then we redirect user to the homepage after flashing a message
        flash("Thêm thuốc thành công")
        return redirect("/")
    else:
        return apology("Thuoc da ton tai tren he thong!", 400)


@app.route("/correct_record", methods=["POST"])
@login_required
def correct_record():
    """Allow user to change med info or transaction info"""
    # When user wants to change existing med info:
    # Will have to query Medicine database to get all meds name
    if request.form.get("btnradio") == "med_info":
        # Query for all records of medicine from database
        existing_meds = Medicine.query.order_by(Medicine.med_name).all()
        print(existing_meds)
        return render_template("change_med.html", existing_meds=existing_meds)
    
    # TODO: Else when user wants to change past transaction. Can be done only when transaction
    # table is up!
    else:
        return apology("TODO", 400)


@app.route("/change_med", methods=["POST"])
@login_required
def change_med():
    """Allow user to change existing information about a medicine"""
    # TODO: Design correct_record database, and then record editing there. 
    # Probably will have to call Medicine database, add info about exisiting med will
    # be added to correct_record database
    # After that, existing information will be updated 
    return apology("TODO", 400)


@app.route("/changes", methods=["GET", "POST"])
@login_required
def changes():
    """Allow user to see existing records of changes made in med info or transaction info"""
    # TODO: Display a table that details all the changes made to med info or transaction info
    return apology("TODO", 400)

@app.route("/receive", methods=["GET", "POST"])
def receive():
    """Allow non-admin user to confirm the arrival of medicine to their clinic"""
    return apology("TODO")


# Run the app
if __name__ == "__main__":
    app.run()

