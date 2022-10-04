import os

from flask import Flask, flash, render_template, redirect, request, session
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology,  login_required, vnd


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
    return apology("TODO")


@app.route("/logout")
def logout():
    """Log user out"""
    return apology("TODO")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    return apology("TODO")


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

