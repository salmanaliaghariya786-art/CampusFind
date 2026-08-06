import os


from werkzeug.utils import secure_filename


from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = "campusfind123"

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def create_database():

    conn = sqlite3.connect("database/campusfind.db")

    cursor = conn.cursor()

    # Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        fullname TEXT NOT NULL,

        email TEXT UNIQUE NOT NULL,

        password TEXT NOT NULL

    )
    """)

    # Lost Items Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS lost_items(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        item_name TEXT NOT NULL,

        category TEXT NOT NULL,

        description TEXT NOT NULL,

        location TEXT NOT NULL,

        lost_date TEXT NOT NULL

    )
    """)
    #found items table 
    
    cursor.execute("""
CREATE TABLE IF NOT EXISTS found_items(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    item_name TEXT NOT NULL,

    category TEXT NOT NULL,

    description TEXT NOT NULL,

    location TEXT NOT NULL,

    found_date TEXT NOT NULL,

    image TEXT
)
""")

    cursor.execute("""
CREATE TABLE IF NOT EXISTS claims(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    item_id INTEGER NOT NULL,

    claimant_name TEXT NOT NULL,

    claimant_email TEXT NOT NULL,

    status TEXT DEFAULT 'Pending'

)
""")

    conn.commit()

    conn.close()

create_database()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]

        password = request.form["password"]
        

        conn = sqlite3.connect("database/campusfind.db")

        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE email=? AND password=?",
            (email, password)
        )

        user = cursor.fetchone()

        conn.close()

        if user:
            return redirect(url_for("dashboard"))

        else:
            return "Invalid Email or Password"

    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        fullname = request.form["fullname"]
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("database/campusfind.db")
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO users(fullname, email, password)
        VALUES (?, ?, ?)
        """, (fullname, email, password))

        conn.commit()
        conn.close()

        return "Account Created Successfully!"

    return render_template("signup.html")
@app.route("/users")
def users():

    conn = sqlite3.connect("database/campusfind.db")

    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users")

    users = cursor.fetchall()

    conn.close()

    return str(users)


@app.route("/dashboard")
def dashboard():

    conn = sqlite3.connect("database/campusfind.db")
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM lost_items")
    total_lost = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM found_items")
    total_found = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM claims")
    total_claims = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "dashboard.html",
        total_users=total_users,
        total_lost=total_lost,
        total_found=total_found,
        total_claims=total_claims
    )
    
@app.route("/report_lost", methods=["GET", "POST"])
def report_lost():

    if request.method == "POST":

        item_name = request.form["item_name"]
        category = request.form["category"]
        description = request.form["description"]
        location = request.form["location"]
        lost_date = request.form["lost_date"]

        conn = sqlite3.connect("database/campusfind.db")
        cursor = conn.cursor()
        
        

        cursor.execute("""
        INSERT INTO lost_items(item_name, category, description, location, lost_date)
        VALUES (?, ?, ?, ?, ?)
        """, (item_name, category, description, location, lost_date))

        conn.commit()
        conn.close()

        return redirect(url_for("lost_items"))

    return render_template("report_lost.html")

@app.route("/lost_items")
def lost_items():

    conn = sqlite3.connect("database/campusfind.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM lost_items")

    items = cursor.fetchall()
    
    conn.close()

    return render_template("lost_items.html", items=items, total_items=len(items))

@app.route("/report_found", methods=["GET", "POST"])
def report_found():

    if request.method == "POST":

        item_name = request.form["item_name"]
        category = request.form["category"]
        description = request.form["description"]
        location = request.form["location"]
        found_date = request.form["found_date"]
        image = request.files["image"]

        filename = secure_filename(image.filename)
        image.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        conn = sqlite3.connect("database/campusfind.db")
        cursor = conn.cursor()

        cursor.execute("""
INSERT INTO found_items
(item_name, category, description, location, found_date, image)
VALUES (?, ?, ?, ?, ?, ?)
""", (item_name, category, description, location, found_date, filename))
        conn.commit()
        conn.close()

        return redirect(url_for("found_items"))

    return render_template("report_found.html")

@app.route("/found_items")
def found_items():

    conn = sqlite3.connect("database/campusfind.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM found_items")

    items = cursor.fetchall()

    conn.close()

    return render_template(
    "found_items.html",
    items=items,
    total_items=len(items)
)
    
@app.route("/search", methods=["GET", "POST"])
def search():

    items = []

    if request.method == "POST":

        keyword = request.form["keyword"].strip()
        category = request.form["category"]
        if keyword == "":
            return render_template("search.html", items=[])

        conn = sqlite3.connect("database/campusfind.db")
        cursor = conn.cursor()

        if category == "":
            cursor.execute(
        "SELECT * FROM lost_items WHERE item_name LIKE ?",
        ('%' + keyword + '%',)
    )
        else:
            cursor.execute(
        "SELECT * FROM lost_items WHERE item_name LIKE ? AND category=?",
        ('%' + keyword + '%', category)
    ) 

        items = cursor.fetchall()

        conn.close()

    return render_template("search.html", items=items)
    
@app.route("/claim/<int:item_id>", methods=["GET", "POST"])
def claim(item_id):

    if request.method == "POST":

        claimant_name = request.form["claimant_name"]
        claimant_email = request.form["claimant_email"]

        conn = sqlite3.connect("database/campusfind.db")
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO claims(item_id, claimant_name, claimant_email)
        VALUES (?, ?, ?)
        """, (item_id, claimant_name, claimant_email))

        conn.commit()
        conn.close()

        return "Claim Request Submitted Successfully!"

    return render_template("claim.html")
    
@app.route("/admin")
def admin():

    if not session.get("is_admin"):
        return redirect(url_for("admin_login"))

    conn = sqlite3.connect("database/campusfind.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM claims")
    claims = cursor.fetchall()

    conn.close()

    return render_template("admin.html", claims=claims)

@app.route("/approve/<int:claim_id>")
def approve(claim_id):

    conn = sqlite3.connect("database/campusfind.db")
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE claims SET status='Approved' WHERE id=?",
        (claim_id,)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("admin"))
    
@app.route("/reject/<int:claim_id>")
def reject(claim_id):

    conn = sqlite3.connect("database/campusfind.db")
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE claims SET status='Rejected' WHERE id=?",
        (claim_id,)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("admin"))
    
@app.route("/delete_duplicate")
def delete_duplicate():

    conn = sqlite3.connect("database/campusfind.db")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM lost_items WHERE id = 5")

    conn.commit()
    conn.close()

    return "Duplicate Deleted Successfully!"


@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if username == "CampusFindadmin642" and password == "CAMPUS_Find_CF@735692":

            session["is_admin"] = True

            return redirect(url_for("admin"))

        else:
            return "Invalid Admin Username or Password"

    return render_template("admin_login.html")
    
    
@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))
if __name__ == "__main__":
    app.run(debug=True)