from cgi import test
from statistics import median
from dotenv import load_dotenv
import os
load_dotenv()
from tabnanny import check

from flask import Flask, flash, render_template, redirect, request, session
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, Integer
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta

from helpers import apology,  login_required, vnd

# Secret code to register
SECRET_CODE_1 = os.getenv("SECRET_CODE_1")
SECRET_CODE_2 = os.getenv("SECRET_CODE_2")

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
    med_quantity = db.Column(db.Text, nullable = False)
    med_quantity_formatted = db.Column(db.Text, nullable = False)
    med_unit = db.Column(db.Text, nullable = False)
    med_latest_price = db.Column(db.Text, nullable = False)
    med_price_formatted = db.Column(db.Text, nullable = False)
    med_notes = db.Column(db.Text) 

class ChangedInfo(db.Model):
    change_id = db.Column(db.Integer, primary_key = True)
    changed_by = db.Column(db.Text, nullable = False)
    changed_time = db.Column(db.DateTime, nullable = False)
    client_IP = db.Column(db.Text, nullable = False)
    change_type = db.Column(db.Text, nullable = False)
    medicine = db.Column(db.Text, nullable = False)
    changed_from = db.Column(db.Text, nullable = False)
    changed_to = db.Column(db.Text, nullable = False)
    change_notes = db.Column(db.Text)

class BuySellHistory(db.Model):
    action_id = db.Column(db.Integer, primary_key = True)
    performed_by = db.Column(db.Text, nullable = False)
    action_time = db.Column(db.DateTime, nullable = False)
    action_IP = db.Column(db.Text, nullable = False)
    medicine = db.Column(db.Text, nullable = False)
    unit= db.Column(db.Text, nullable = False)
    quantity = db.Column(db.Text, nullable = False)
    quantity_formatted = db.Column(db.Text, nullable = False)
    price = db.Column(db.Text, nullable = False)
    price_formatted = db.Column(db.Text, nullable = False)
    action_total = db.Column(db.Text, nullable = False)
    action_total_formatted = db.Column(db.Text, nullable = False)
    sale_place = db.Column(db.Text, nullable = False)
    action = db.Column(db.Text, nullable = False)
    previous_price = db.Column(db.Text, nullable = False)
    previous_quantity = db.Column(db.Text, nullable = False)
    action_notes = db.Column(db.Text)

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
    all_meds = Medicine.query.order_by(Medicine.med_name).all()
    return render_template("index.html", all_meds=all_meds)


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
        if len(User.query.filter_by(username=username).all()) == 0 and code_entered == SECRET_CODE_1:
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
    """Let user buy more of the medicine that they already have on the database"""
    # Query for all the existing meds to render buy.html if the user haven't submitted the form
    if request.method == "GET":
        all_meds = Medicine.query.order_by(Medicine.med_name).all()
        return render_template("buy.html", all_meds=all_meds)
    else:
        # Getting the information about the medicine that user wants to buy
        med_info = request.form.get("medname").split(" - ")
        # From that information, get the name, which is the first element in the list after splitting by " - "
        med_name = med_info[0]
        # Then, we will get the recorded unit of med, to prevent buying in different units
        med_recorded_quant = med_info[1].split(": ")[1]
        med_recorded_unit = med_info[2].split(": ")[1]
        med_recorded_price = med_info[3].split(": ")[1]
        # Then we will get the other information in order to add to database
        user_chosen_unit = request.form.get("medunit")
        med_quantity = int(request.form.get("quantity"))
        med_price = int(request.form.get("medprice"))
        purchase_total = med_quantity * med_price
        med_notes = request.form.get("med_notes")

        if med_recorded_unit != user_chosen_unit:
            flash(f"Đơn vị hiện tại: {med_recorded_unit}. Đơn vị bạn nhập: {user_chosen_unit}. Vui lòng cập nhật thông tin thuốc hoặc điền lại!")
            return apology("Sai don vi thuoc!", 400)
        else:
            # If the unit is correct, we will go ahead and query the medicine from database:
            changing_med = Medicine.query.filter_by(med_name=med_name).first()
            # And then update it with the new value
            new_quantity = med_quantity + int(changing_med.med_quantity)
            changing_med.med_quantity = str(new_quantity)
            changing_med.med_quantity_formatted = vnd(new_quantity)
            changing_med.med_latest_price = str(med_price)
            changing_med.med_price_formatted = vnd(med_price)
            changing_med.med_notes = med_notes
            db.session.commit()

            # Then we will need to record this purchase in the purchase history database
            current_user = User.query.filter_by(user_id=session["user_id"]).first().username
            current_time = datetime.now()
            current_IP = request.environ['REMOTE_ADDR']
            
            new_purchase = BuySellHistory(
                performed_by=current_user,
                action_time=current_time,
                action_IP=current_IP,
                medicine=med_name,
                quantity=str(med_quantity),
                quantity_formatted=f"+{vnd(med_quantity)}",
                unit=med_recorded_unit,
                price=str(med_price),
                price_formatted=vnd(med_price),
                action_total=str(purchase_total),
                action_total_formatted=vnd(purchase_total),
                sale_place="--",
                action="nhap",
                previous_price=med_recorded_price,
                previous_quantity=med_recorded_quant,
                action_notes=med_notes,
            )
            db.session.add(new_purchase)
            db.session.commit()

            flash("Nhập thuốc thành công!")
            return redirect("/")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Let user sell medicine to different places"""
    if request.method == "GET":
        all_meds = Medicine.query.order_by(Medicine.med_name).all()
        return render_template("sell.html", all_meds=all_meds)
    else:
        # Getting existing information from the database
        med_info = request.form.get("medname").split(" - ")
        med_name = med_info[0]
        med_recorded_quant = med_info[1].split(": ")[1]
        med_recorded_unit = med_info[2].split(": ")[1]
        med_recorded_price = med_info[3].split(": ")[1]

        # Getting user input
        user_chosen_unit = request.form.get("medunit")
        sale_place = request.form.get("place")
        sale_quantity = int(request.form.get("quantity"))
        sale_price = int(request.form.get("medprice"))
        sale_total = sale_quantity * sale_price
        sale_notes = request.form.get("med_notes")

        if med_recorded_unit != user_chosen_unit:
            flash(f"Đơn vị hiện tại: {med_recorded_unit}. Đơn vị bạn muốn xuất: {user_chosen_unit}. Vui lòng cập nhật thông tin thuốc hoặc điền lại!")
            return apology("Sai don vi thuoc!", 400)
        else:
            # If the unit is correct, we will go ahead and query the medicine from database:
            changing_med = Medicine.query.filter_by(med_name=med_name).first()
            # Check if there is enough left to sell:
            if int(changing_med.med_quantity) < sale_quantity:
                flash("Số lượng thuốc tồn không đủ để xuất!")
                return apology("Khong du thuoc de xuat!", 400)
            else:
                new_quantity = int(changing_med.med_quantity) - sale_quantity
                changing_med.med_quantity = str(new_quantity)
                changing_med.med_quantity_formatted = vnd(new_quantity)
                changing_med.med_notes = sale_notes
                db.session.commit()

                current_user = User.query.filter_by(user_id=session["user_id"]).first().username
                current_time = datetime.now()
                current_IP = request.environ['REMOTE_ADDR']

                new_sale = BuySellHistory(
                    performed_by=current_user,
                    action_time=current_time,
                    action_IP=current_IP,
                    medicine=med_name,
                    quantity=str(sale_quantity),
                    quantity_formatted=f"-{vnd(sale_quantity)}",
                    unit=med_recorded_unit,
                    price=str(sale_price),
                    price_formatted=vnd(sale_price),
                    action_total=str(sale_total),
                    action_total_formatted=vnd(sale_total),
                    sale_place=sale_place,
                    action="xuat",
                    previous_price=med_recorded_price,
                    previous_quantity=med_recorded_quant,
                    action_notes=sale_notes,
                )
                db.session.add(new_sale)
                db.session.commit()

                flash("Xuất thuốc thành công!")
                return redirect("/")

@app.route("/history", methods=["GET", "POST"])
@login_required
def history():
    """Let user see all transactions and filter data"""

    # If the user just got to the page through the links, without any filter:
    if request.method == "GET":
        all_transactions = BuySellHistory.query.order_by(BuySellHistory.action_time.desc()).all()
    # Else if the user has submitted a filter
    else:
        # Getting the input from the user: 
        filter_user = request.form.get("filter_user")
        filter_day = request.form.get("filter_day")
        filter_month = request.form.get("filter_month")
        filter_year = request.form.get("filter_year")
        filter_med = request.form.get("filter_med").lower()
        filter_place = request.form.get("filter_place").lower()
        filter_action = request.form.get("filter_action")

        # Creating an empty list for the queries we will perform
        queries = []

        if filter_user: queries.append(BuySellHistory.performed_by == filter_user)
        if filter_day: queries.append(func.strftime("%d", BuySellHistory.action_time) == filter_day)
        if filter_month: queries.append(func.strftime("%m", BuySellHistory.action_time) == filter_month)
        if filter_year: queries.append(func.strftime("%Y", BuySellHistory.action_time) == filter_year)
        if filter_med: queries.append(func.lower(BuySellHistory.medicine) == filter_med)
        if filter_place: queries.append(func.lower(BuySellHistory.sale_place) == filter_place)
        if filter_action: queries.append(BuySellHistory.action == filter_action)

        # Now that we have all the filters user wants:
        flash(f"Lọc theo người dùng: {filter_user}, ngày: {filter_day}, tháng: {filter_month}, năm: {filter_year}, thuốc: {filter_med}, nơi xuất:{filter_place}, nhập/xuất:{filter_action}")
        all_transactions = BuySellHistory.query.order_by(BuySellHistory.action_time.desc()).filter(*queries).all()

    quantity_total = 0
    money_total = 0

    for transaction in all_transactions:
        # If the action was buying, we don't care about the money
        if transaction.sale_place == "--":
            quantity_total += int(transaction.quantity)

        # If the action was selling, we care about the money
        else:
            quantity_total -= int(transaction.quantity)
        
        money_total += int(transaction.action_total)

    return render_template("transactions.html", all_transactions=all_transactions, quantity_total=vnd(quantity_total), money_total=vnd(money_total))


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
    med_quantity = str(request.form.get("quantity"))
    quantity_formatted = vnd(int(request.form.get("quantity")))
    med_unit = request.form.get("medunit")
    med_price = str(request.form.get("latest_price"))
    price_formatted = vnd(int(request.form.get("latest_price")))
    med_notes = request.form.get("med_notes")
    total = int(med_quantity) * int(med_price)
    total_formatted = vnd(total)
    
    # If there is no meds in the existing database with the same name
    if len(Medicine.query.filter_by(med_name=med_name).all()) == 0:
        # We add this confirmed new medicine to the db:
        new_med = Medicine(
            med_name=med_name,
            med_unit=med_unit,
            med_quantity=med_quantity,
            med_quantity_formatted=quantity_formatted,
            med_latest_price=med_price,
            med_price_formatted=price_formatted,
            med_notes=med_notes
        )
        db.session.add(new_med)
        db.session.commit()

        current_user = User.query.filter_by(user_id=session["user_id"]).first().username
        current_time = datetime.now()
        current_IP = request.environ['REMOTE_ADDR']

        new_add = BuySellHistory(
            performed_by=current_user,
            action_time=current_time,
            action_IP=current_IP,
            medicine=med_name,
            quantity=med_quantity,
            quantity_formatted=f"+{quantity_formatted}",
            unit=med_unit,
            price=med_price,
            price_formatted=price_formatted,
            action_total=total,
            action_total_formatted=total_formatted,
            sale_place="--",
            action="them",
            previous_price="chua co",
            previous_quantity="chua co",
            action_notes="Them thuoc chua ton tai tren he thong",
        )
        db.session.add(new_add)
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
        return render_template("change_med.html", existing_meds=existing_meds)
    
    # Else if the user wants to change transaction records
    else:
        return render_template("fix_transaction.html")


@app.route("/change_med", methods=["POST"])
@login_required
def change_med():
    """Allow user to change existing information about a medicine"""
    # Determine the medicine in need of change
    med_name = (request.form.get("medname").split(" - "))[0]
    # Query existing data about that medicine:
    info = Medicine.query.filter_by(med_name=med_name).first()
    changed_from = {
        "med_name": med_name,
        "old_quantity": info.med_quantity,
        "old_quantity_formatted": info.med_quantity_formatted,
        "old_unit": info.med_unit,
        "old_price": info.med_latest_price,
        "old_price_formatted": info.med_price_formatted,
        "old_notes": info.med_notes,
    }

    # Getting data that user wants to change:
    changed_to = {
        "med_name": med_name,
        "new_quantity": str(request.form.get("quantity")),
        "new_quantity_formatted": vnd(int(request.form.get("quantity"))),
        "new_unit": request.form.get("medunit"),
        "new_price": str(request.form.get("latest_price")),
        "new_price_formatted": vnd(int(request.form.get("latest_price"))),
    }

    # Adding the data to the ChangedInfo database:
    current_user = User.query.filter_by(user_id=session["user_id"]).first().username
    current_time = datetime.now()
    current_IP = request.environ['REMOTE_ADDR']
    change_notes = request.form.get("med_notes")

    new_change = ChangedInfo(
        changed_by = current_user,
        changed_time = current_time,
        client_IP = current_IP,
        change_type = "sua thong tin thuoc",
        medicine = med_name,
        changed_from = str(changed_from),
        changed_to = str(changed_to),
        change_notes = change_notes
    )
    db.session.add(new_change)
    db.session.commit()

    # Rendering the confirmation page to ask user 1 last time about their choice
    return render_template("medInfoChangeConfirm.html", med_name=med_name, changed_from=changed_from, 
                            changed_to=changed_to, current_user=current_user, client_IP=current_IP)


@app.route("/change_med_confirm", methods=["POST"])
@login_required
def change_med_confirm():
    # Get the name of the medicine that the user is modifying
    med_name = request.form.get("medname")
    # Query the latest change made to that particular medicine in the change info table
    change_before_confirm = ChangedInfo.query.filter_by(medicine=med_name).order_by(ChangedInfo.changed_time.desc()).first()

    #If user confirms the change they want to make
    if request.form.get("btnradio") == "confirmed":
        # The dictionary that stores values that user confirms they want to change
        changed_to = eval(change_before_confirm.changed_to)
        # Query the med in the Medicine table that we will update
        changing_med = Medicine.query.filter_by(med_name=med_name).first()
        # And update the entry with new information
        changing_med.med_quantity = changed_to["new_quantity"]
        changing_med.med_quantity_formatted = changed_to["new_quantity_formatted"]
        changing_med.med_unit = changed_to["new_unit"]
        changing_med.med_latest_price = changed_to["new_price"]
        changing_med.med_price_formatted = changed_to["new_price_formatted"]
        changing_med.med_notes = change_before_confirm.change_notes
        db.session.commit()

        # Once data entries have been updated, redirect to homepage
        flash("Sửa thông tin thuốc thành công!")
        return redirect("/changes")
    
    # If the user wants to cancel the previous change:
    else: 
        # We have to delete the change record from the database
        db.session.delete(change_before_confirm)
        db.session.commit()

        # Tell user cancellation was successful before redirecting
        flash("Hủy thành công việc sửa thông tin thuốc!")
        return redirect("/")


@app.route("/delete_initial", methods=["POST"])
@login_required
def delete_initial():
    # First we will get the transaction ID that user wants to delete
    trans_id = int(request.form.get("trans_id"))
    trans_info = BuySellHistory.query.filter_by(action_id=trans_id).first()
    return render_template("delete_confirm.html", trans_info=trans_info)


@app.route("/delete_final", methods=["POST"])
@login_required
def delete_final():
    # Get the ID of the transaction that user wants to delete
    trans_id = request.form.get("trans_id")

    # If user confirms that they want to delete the transaction
    if request.form.get("btnradio") == "confirmed":
        # Log the deletion in the changes database
        changing_trans = BuySellHistory.query.filter_by(action_id=trans_id).first()

        current_user = User.query.filter_by(user_id=session["user_id"]).first().username
        current_time = datetime.now()
        current_IP = request.environ['REMOTE_ADDR']
        changed_from = {
            "med_name": changing_trans.medicine,
            "old_quantity": changing_trans.quantity,
            "old_quantity_formatted": changing_trans.quantity_formatted,
            "old_unit": changing_trans.unit,
            "old_price": changing_trans.price,
            "old_price_formatted": changing_trans.price_formatted,
            "old_notes": changing_trans.action_time,
        }
        changed_to = {
            "med_name": changing_trans.medicine,
            "new_quantity": "xoa",
            "new_quantity_formatted": "xoa",
            "new_unit": changing_trans.unit,
            "new_price": "xoa",
            "new_price_formatted": "xoa",
        }
        
        new_delete = ChangedInfo(
            changed_by = current_user,
            changed_time = current_time,
            client_IP = current_IP,
            change_type = "sua giao dich",
            medicine = changing_trans.medicine,
            changed_from = str(changed_from),
            changed_to = str(changed_to),
            change_notes = f"Nơi xuất: {changing_trans.sale_place}"
        )
        db.session.add(new_delete)
        db.session.commit()

        # Change the inventory from the Medicine table bc of the deletion:
        changing_med = Medicine.query.filter_by(med_name=changing_trans.medicine).first()
        # If it was buying transaction that user wants to delete
        if changing_trans.sale_place == "--":
            new_quantity = int(changing_med.med_quantity) - int(changing_trans.quantity)
        # Else if it was selling transaction:
        else:
            new_quantity = int(changing_med.med_quantity) + int(changing_trans.quantity)
        
        changing_med.med_quantity = str(new_quantity)
        changing_med.med_quantity_formatted = vnd(new_quantity)
        changing_med.med_notes = "Thay doi do nguoi dung xoa giao dich"
        db.session.commit()

        # Delete the record from the transaction database
        db.session.delete(changing_trans)
        db.session.commit()

        flash("Xóa giao dịch thành công")
        return redirect("/changes")
    # If the user doesn't want to delete anymore
    else:
        flash("Hủy thành công việc xóa giao dịch!")
        return redirect("/")



@app.route("/changes", methods=["GET", "POST"])
@login_required
def changes():
    """Allow user to see existing records of changes made in med info or transaction info"""
    # Query the ChangedInfo table to get all the changes made by user
    if request.method == "GET":
        all_changes = ChangedInfo.query.order_by(ChangedInfo.changed_time.desc()).all()
    else:
        # Getting input from the user
        filter_user = request.form.get("filter_user")
        filter_day = request.form.get("filter_day")
        filter_month = request.form.get("filter_month")
        filter_year = request.form.get("filter_year")
        filter_med = request.form.get("filter_med")
        filter_type = request.form.get("filter_type")

        # Creating an empty list for the queries we will perform
        queries = []

        if filter_user: queries.append(ChangedInfo.changed_by == filter_user)
        if filter_day: queries.append(func.strftime("%d", ChangedInfo.changed_time) == filter_day)
        if filter_month: queries.append(func.strftime("%m", ChangedInfo.changed_time) == filter_month)
        if filter_year: queries.append(func.strftime("%Y", ChangedInfo.changed_time) == filter_year)
        if filter_med: queries.append(func.lower(ChangedInfo.medicine) == filter_med)
        if filter_type: queries.append(ChangedInfo.change_type == filter_type)
    
        flash(f"Lọc theo người dùng: {filter_user}, ngày: {filter_day}, tháng: {filter_month}, năm: {filter_year}, thuốc: {filter_med}, loại giao dịch:{filter_type}")
        all_changes = ChangedInfo.query.order_by(ChangedInfo.changed_time.desc()).filter(*queries).all()


    return render_template("changes_history.html", all_changes=all_changes)

@app.route("/report", methods=["GET", "POST"])
def report():
    """Allow non-admin user to confirm the arrival of medicine to their clinic"""
    med_report = db.session.query(BuySellHistory.medicine, func.sum(func.cast(BuySellHistory.quantity, Integer)), func.sum(func.cast(BuySellHistory.action_total, Integer))).filter_by(sale_place="Phung").group_by(BuySellHistory.medicine)

    for item in med_report:
        print(item)
    return apology("TODO")

# Run the app
if __name__ == "__main__":
    app.run()

