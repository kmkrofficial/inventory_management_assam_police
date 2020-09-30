from flask import Flask, render_template, url_for, flash, session, request, redirect
from datetime import datetime
import pytz
from flask_wtf.csrf import CsrfProtect
from flask_bcrypt import Bcrypt
import pymysql.cursors
from pandas import read_csv
from werkzeug.utils import secure_filename

flask_obj = Flask(__name__)
flask_obj.secret_key = "9f9dace5bff3b61cd9603b631d00bad8"
db_connect = pymysql.connect(
    host = "localhost",
    user = 'root',
    password = "temppass@123",
    db = "inventory_management",
    charset = "utf8mb4",
    cursorclass = pymysql.cursors.DictCursor
)
cursor = db_connect.cursor()
CsrfProtect(flask_obj)
bcrypt = Bcrypt()
final_login = True


ALLOWED_EXTENSIONS = {'csv', 'xlsx'}

app = Flask(__name__)
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def email_client(email, s):
    import smtplib, ssl

    port = 587  # For starttls
    smtp_server = "smtp.gmail.com"
    sender_email = "18eucs058@skcet.ac.in"
    receiver_email = email
    password = "temppass@321"
    message = f"""\
    Subject: Sample Billing

    {s}. Approved by the Police of Assam."""

    context = ssl.create_default_context()
    with smtplib.SMTP(smtp_server, port) as server:
        server.ehlo()  # Can be omitted
        server.starttls(context=context)
        server.ehlo()  # Can be omitted
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message)

@flask_obj.route('/')
@flask_obj.route('/home')
def index():
    return render_template("index.html")

@flask_obj.route('/product-entry-page', methods = ['POST', 'GET'])
def product_entry_page():
    if request.method == 'POST':
        try:
            _product_name = request.form["product_name"]
            _product_type = request.form["select_dropdown_type"]
            _entry_date = request.form["entry_date"]
            _status = request.form["select_dropdown_status"]
            sql_query = f"insert into item_list (product_name, product_type, entry_date, select_dropdown_status) values (\"{_product_name}\", \"{_product_type}\", \"{_entry_date}\", \"{_status}\")"
            cursor.execute(sql_query)
            db_connect.commit()
            flash("Value Recorded", "success")
            return redirect(url_for("product_entry_page"))

        except Exception as e:
            print(e)
            flash("Error Occured", "danger")
            return redirect(url_for("product_entry_page"))
    else: 
        sql_query = "SELECT * FROM product_type_list"
        cursor.execute(sql_query)
        result = cursor.fetchall()
        return render_template("add_new_product.html", results = result)

@flask_obj.route("/add-product-type", methods= ["POST", "GET"])
def add_product_type():
        if request.method == "POST":
            try: 
                _type = request.form["specify_new_type"]
                sql_query = f"INSERT INTO product_type_list(product_type) VALUES (\"{_type}\")"
                cursor.execute(sql_query)
                db_connect.commit()
                flash("Successfully Added", "success")
                return redirect(url_for("add_product_type"))

            except Exception as e:
                print(e)
                flash("Some Error as occured", "danger")
                return redirect(url_for("add_product_type"))
            
        else:
            return render_template("add_product_type.html")

@flask_obj.route('/login', methods = ['POST', 'GET'])
def login():
    if request.method == 'POST':
        user_name = request.form["userid"]
        password = request.form["user_password"]
        sql_query = f"SELECT * FROM login_credentials WHERE username=\"{ user_name }\""
        cursor.execute(sql_query)
        result = cursor.fetchone()
        if(result):
            if(bcrypt.check_password_hash(result["pwd"], password)):
                flash("Login Successful", "success")
                return redirect(url_for("home"))
            else:
                flash("Wrong Password. Please try again", "danger")
                return redirect(url_for("login"))
        else:
            flash("User ID not found. Please Register.", "danger")
            return redirect(url_for("login"))
    else:
        return render_template("login.html")

@flask_obj.route('/register', methods = ['POST', 'GET'])
def register():
    if request.method == "POST":
        if request.form["user_password"] != request.form["confirm_password"]:
            flash("Passwords do not match!", "danger")
            return redirect(url_for("register"))
        pw_hash = bcrypt.generate_password_hash(request.form["user_password"]).decode('utf-8')
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        police_id = request.form["police_reg_num"]
        userid = request.form["userid"]
        email = request.form["user_email"]
        access_rights = request.form["access_rights"]
        print(access_rights)
        try:
            sql_query = f"INSERT INTO login_credentials(first_name, last_name, police_id, username, pwd, access_level, email) VALUES ('{first_name}', '{last_name}', {police_id}, '{userid}', '{pw_hash}', '{email}', '{access_rights}');"
            cursor.execute(sql_query)
            db_connect.commit()
            
        except Exception as e:
            print (e)
            flash("Some Error has occured. Please try again later.", "danger")
            return redirect(url_for("register"))

        flash("Successfully Added.", "success")
        return redirect(url_for("login"))
    else:
        return render_template('register.html')

@flask_obj.route('/police_entry', methods = ["POST", "GET"])
def police_entry():
    if(request.method == "POST"):
        police_name = request.form["police_name"]
        police_id = request.form["police_id"]
        station = request.form["station_name"]
        sql_query = f"insert into members_list(mem_name, police_id, station) values (\"{ police_name }\", {police_id}, \"{station}\");"
        cursor.execute(sql_query)
        db_connect.commit()
        flash("Successfully Added.", "success")
        return redirect(url_for("police_entry"))
    return render_template("police_entry.html")


@flask_obj.route("/upload", methods=["POST", "GET"])
def upload():
    if request.method == "POST":
        file = request.files['files']
        if file.filename == '':
            flash('No selected file', "info")
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(filename)
            flash("Read Successfully.", "success")
            dataset = read_csv(filename)
            try:
                for i in dataset.itertuples():
                    sql_query = f"insert into members_list(mem_name, police_id, station) values (\"{i.Name}\", {i.Id}, \"{i.Station}\");"
                    cursor.execute(sql_query)
                db_connect.commit()
                flash("Successful Database operation.", "success")
            except Exception as e:
                print(e)
                flash("Error during Database Storing. Please try again later.", "info")   
            return redirect(url_for("upload"))
    return render_template("excel_upload.html")

@flask_obj.route("/view-members")
def view_table():
    try:
        sql_query = "SELECT * FROM members_list"
        cursor.execute(sql_query)
        result = cursor.fetchall()
        return render_template("inventory_table.html", result=result)
    except Exception as e:
        print(e)
        return "Error has occured during database fetch. Reload the page."

@flask_obj.route("/place_order", methods=["POST", "GET"])
def place_order():
    if request.method == "POST":
        if request.form["product1"]!="" and request.form["r_name"]:
            requestor = request.form["r_name"]
            temp1 = request.form["product1"]
            temp2 = request.form["quantity1"]
            s = f"{temp1} * {temp2}\n"
            if request.form["product2"]!="":
                temp1 = request.form["product2"]
                temp2 = request.form["quantity2"]
                s = s+ f"{temp1} * {temp2}\n"
            if request.form["product3"]!="":
                temp1 = request.form["product3"]
                temp2 = request.form["quantity3"]
                s = s+ f"{temp1} * {temp2}\n"
            if request.form["product4"]!="":
                temp1 = request.form["product4"]
                temp2 = request.form["quantity4"]
                s = s+ f"{temp1} * {temp2}\n"
        time_now = datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%Y:%m:%d %H:%M:%S %Z %z')
        email = request.form["recipient_email"]
        try:
            sql_query = f"INSERT INTO requests (products, requestor, request_time, requestor_email) VALUES (\"{s}\", \"{requestor}\", \"{time_now}\", \"{email}\")"
            cursor.execute(sql_query)
            db_connect.commit()
            email_client(email, s)
            flash("Successfully Completed. Check your mail for Billing Reciept.", "success")
            return redirect(url_for("place_order"))
        except Exception as e:
            print("Error occured while DB Connection." + e)
            flash("Error Executing Query", "info")
            return redirect(url_for("index"))

    sql_query = "SELECT mem_name FROM members_list"
    cursor.execute(sql_query)
    names = cursor.fetchall()
    sql_query = "SELECT product_name FROM item_list"
    cursor.execute(sql_query)
    products = cursor.fetchall()
    return render_template("place_order.html", names = names, products = products)

@flask_obj.route("/request_list")
def request_list():
    sql_query = "SELECT * FROM requests"   
    cursor.execute(sql_query)
    results = cursor.fetchall()
    return render_template("request_list.html", requests = results)


# driver code
if __name__ == "__main__":
    flask_obj.run(debug=True)