import os
import random
import boto3
import pymysql
from flask import Flask, render_template, request, redirect, session

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "fallbacksecret")


# Load parameters from AWS SSM (Production Only)
if os.getenv("FLASK_ENV") == "production":
    try:
        client = boto3.client("ssm", region_name="us-east-1")

        response = client.get_parameters_by_path(
            Path="/application/banking",
            Recursive=True,
            WithDecryption=True
        )

        for p in response["Parameters"]:
            os.environ[os.path.basename(p["Name"])] = p["Value"]

        print("✅ SSM Parameters Loaded Successfully")

    except Exception as e:
        print(f"❌ Failed to load SSM Parameters: {e}")


def get_db_connection():
    return pymysql.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        db=os.getenv("DB_NAME"),
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=10,
    )


def generate_account_number():
    return str(random.randint(1000000000, 9999999999))


@app.route("/health")
def health():
    return "OK", 200


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "SELECT id FROM users WHERE username=%s",
            (username,)
        )

        if cur.fetchone():
            conn.close()
            return render_template(
                "register.html",
                error="Username already taken."
            )

        cur.execute(
            "INSERT INTO users(username,password) VALUES(%s,%s)",
            (username, password)
        )

        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "SELECT * FROM users WHERE username=%s AND password=%s",
            (username, password)
        )

        user = cur.fetchone()
        conn.close()

        if user:
            session["username"] = username
            return redirect("/dashboard")

        return render_template(
            "login.html",
            error="Invalid username or password."
        )

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect("/login")


@app.route("/open-account", methods=["GET", "POST"])
def open_account():

    if "username" not in session:
        return redirect("/login")

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        mobile = request.form["mobile"]
        balance = request.form["balance"]

        account_number = generate_account_number()

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO accounts
            (name,email,mobile,acc_number,balance)
            VALUES(%s,%s,%s,%s,%s)
        """,
        (
            name,
            email,
            mobile,
            account_number,
            balance
        ))

        conn.commit()
        conn.close()

        return redirect("/dashboard")

    return render_template("open_account.html")


@app.route("/dashboard")
def dashboard():

    if "username" not in session:
        return redirect("/login")

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM accounts")

    accounts = cur.fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        accounts=accounts
    )


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )