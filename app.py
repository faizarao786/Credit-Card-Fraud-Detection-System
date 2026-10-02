
# CREDIT CARD FRAUD DETECTION SYSTEM
# COMPLETE FLASK APPLICATIOn

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

from fraud_detection_model import predict_transaction

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

# NEW:
# Used for safely handling uploaded profile-picture filenames
from werkzeug.utils import secure_filename

import os
import sqlite3
import pandas as pd
from datetime import datetime


# ============================================================
# MATPLOTLIB FOR ANALYTICS CHARTS
# ============================================================

import matplotlib

# Use Agg backend because Flask runs without a GUI
matplotlib.use("Agg")

import matplotlib.pyplot as plt


# ============================================================
# FLASK APPLICATION
# ============================================================

app = Flask(__name__)

# Secret key for sessions
app.secret_key = "credit-card-fraud-secret-key-2026"


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

DATA_FILE = os.path.join(
    BASE_DIR,
    "creditcard.csv"
)

DATABASE_FILE = os.path.join(
    BASE_DIR,
    "users.db"
)


# ============================================================
# ANALYTICS CHART FOLDER
# ============================================================

GRAPH_FOLDER = os.path.join(
    BASE_DIR,
    "static",
    "graphs"
)

# Create graph folder automatically
os.makedirs(
    GRAPH_FOLDER,
    exist_ok=True
)


# ============================================================
# PROFILE PICTURE FOLDER
# ============================================================

PROFILE_FOLDER = os.path.join(
    BASE_DIR,
    "static",
    "images",
    "profile"
)

# Create profile picture folder automatically
os.makedirs(
    PROFILE_FOLDER,
    exist_ok=True
)


# ============================================================
# ALLOWED PROFILE IMAGE EXTENSIONS
# ============================================================

ALLOWED_PROFILE_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "webp",
    "gif"
}


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_db_connection():

    connection = sqlite3.connect(
        DATABASE_FILE
    )

    connection.row_factory = sqlite3.Row

    return connection


# ============================================================
# CREATE DATABASE TABLES
# ============================================================

def initialize_database():

    connection = get_db_connection()

    # --------------------------------------------------------
    # USERS TABLE
    # --------------------------------------------------------

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
        """
    )

    # --------------------------------------------------------
    # PROFILE IMAGE COLUMN
    #
    # This adds the column to an already-existing users.db.
    # If the column already exists, nothing happens.
    # --------------------------------------------------------

    try:

        connection.execute(
            """
            ALTER TABLE users
            ADD COLUMN profile_image TEXT DEFAULT NULL
            """
        )

    except sqlite3.OperationalError:

        # Column already exists
        pass

    # --------------------------------------------------------
    # PREDICTION HISTORY TABLE
    # --------------------------------------------------------

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS prediction_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            datetime TEXT NOT NULL,
            amount REAL NOT NULL,
            result TEXT NOT NULL,
            probability REAL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """
    )

    connection.commit()

    connection.close()


# ============================================================
# HOME PAGE
# ============================================================

@app.route("/")
def index():

    return render_template(
        "index.html"
    )


# ============================================================
# LOGIN
# ============================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        ).strip()

        # ----------------------------------------------------
        # CHECK EMPTY FIELDS
        # ----------------------------------------------------

        if not email or not password:

            flash(
                "Please enter email and password.",
                "danger"
            )

            return render_template(
                "login.html"
            )

        # ----------------------------------------------------
        # DEMO LOGIN
        #
        # For this project demo, any email and any password
        # will be accepted.
        # ----------------------------------------------------

        connection = get_db_connection()

        # Try to find the user if already registered
        user = connection.execute(
            """
            SELECT *
            FROM users
            WHERE email = ?
            """,
            (email,)
        ).fetchone()

        connection.close()

        # ----------------------------------------------------
        # EXISTING USER
        # ----------------------------------------------------

        if user:

            session["user"] = user["email"]

            session["user_name"] = user["name"]

            session["user_id"] = user["id"]

            # Store profile image in session
            session["profile_image"] = user["profile_image"]

        # ----------------------------------------------------
        # NEW / DEMO USER
        # ----------------------------------------------------

        else:

            # Use a demo session for an unregistered email.
            # Password is intentionally not checked.
            session["user"] = email

            session["user_name"] = email.split("@")[0]

            # Existing prediction-history tables require
            # a user_id, so use the first available user.
            connection = get_db_connection()

            first_user = connection.execute(
                """
                SELECT id
                FROM users
                ORDER BY id
                LIMIT 1
                """
            ).fetchone()

            connection.close()

            if first_user:

                session["user_id"] = first_user["id"]

                # Get first user's profile picture
                connection = get_db_connection()

                first_user_data = connection.execute(
                    """
                    SELECT profile_image
                    FROM users
                    WHERE id = ?
                    """,
                    (
                        first_user["id"],
                    )
                ).fetchone()

                connection.close()

                if first_user_data:

                    session["profile_image"] = (
                        first_user_data["profile_image"]
                    )

                else:

                    session["profile_image"] = None

            else:

                # If there is no registered user yet,
                # create a simple demo user automatically.
                try:

                    connection = get_db_connection()

                    cursor = connection.execute(
                        """
                        INSERT INTO users
                        (
                            name,
                            email,
                            password
                        )
                        VALUES (?, ?, ?)
                        """,
                        (
                            session["user_name"],
                            email,
                            generate_password_hash(password)
                        )
                    )

                    connection.commit()

                    session["user_id"] = cursor.lastrowid

                    session["profile_image"] = None

                    connection.close()

                except sqlite3.IntegrityError:

                    connection.close()

                    connection = get_db_connection()

                    existing_user = connection.execute(
                        """
                        SELECT id, name, email, profile_image
                        FROM users
                        WHERE email = ?
                        """,
                        (email,)
                    ).fetchone()

                    connection.close()

                    if existing_user:

                        session["user_id"] = existing_user["id"]

                        session["profile_image"] = (
                            existing_user["profile_image"]
                        )

                    else:

                        flash(
                            "Unable to create demo login.",
                            "danger"
                        )

                        return render_template(
                            "login.html"
                        )

        # ----------------------------------------------------
        # LOGIN SUCCESS
        # ----------------------------------------------------

        flash(
            "Login successful!",
            "success"
        )

        return redirect(
            url_for("dashboard")
        )

    return render_template(
        "login.html"
    )


# ============================================================
# REGISTER
# ============================================================

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        ).strip()

        # ----------------------------------------------------
        # CONFIRM PASSWORD
        # ----------------------------------------------------

        confirm_password = request.form.get(
            "confirm_password",
            ""
        ).strip()

        # ----------------------------------------------------
        # CHECK EMPTY FIELDS
        # ----------------------------------------------------

        if (
            not name
            or not email
            or not password
            or not confirm_password
        ):

            flash(
                "Please fill all fields.",
                "danger"
            )

            return render_template(
                "register.html"
            )

        # ----------------------------------------------------
        # CHECK PASSWORD MATCH
        # ----------------------------------------------------

        if password != confirm_password:

            flash(
                "Passwords do not match.",
                "danger"
            )

            return render_template(
                "register.html"
            )

        # ----------------------------------------------------
        # EMAIL VALIDATION
        # ----------------------------------------------------

        if "@" not in email or "." not in email:

            flash(
                "Please enter a valid email address.",
                "danger"
            )

            return render_template(
                "register.html"
            )

        # ----------------------------------------------------
        # PASSWORD LENGTH
        # ----------------------------------------------------

        if len(password) < 6:

            flash(
                "Password must contain at least 6 characters.",
                "danger"
            )

            return render_template(
                "register.html"
            )

        # ----------------------------------------------------
        # HASH PASSWORD
        # ----------------------------------------------------

        hashed_password = generate_password_hash(
            password
        )

        # ----------------------------------------------------
        # SAVE USER
        # ----------------------------------------------------

        try:

            connection = get_db_connection()

            connection.execute(
                """
                INSERT INTO users
                (
                    name,
                    email,
                    password
                )
                VALUES (?, ?, ?)
                """,
                (
                    name,
                    email,
                    hashed_password
                )
            )

            connection.commit()

            connection.close()

            flash(
                "Registration successful! Please login.",
                "success"
            )

            return redirect(
                url_for("login")
            )

        except sqlite3.IntegrityError:

            flash(
                "This email is already registered.",
                "warning"
            )

            return render_template(
                "register.html"
            )

        except Exception as e:

            flash(
                f"Registration error: {str(e)}",
                "danger"
            )

            return render_template(
                "register.html"
            )

    return render_template(
        "register.html"
    )


# ============================================================
# DASHBOARD
# ============================================================

@app.route("/dashboard")
def dashboard():

    # Login protection
    if "user" not in session:

        flash(
            "Please login first.",
            "warning"
        )

        return redirect(
            url_for("login")
        )

    total_transactions = 0
    normal_transactions = 0
    fraud_transactions = 0

    fraud_rate = 0
    normal_rate = 0

    try:

        if os.path.exists(DATA_FILE):

            df = pd.read_csv(
                DATA_FILE
            )

            if "Class" in df.columns:

                total_transactions = len(df)

                normal_transactions = int(
                    (df["Class"] == 0).sum()
                )

                fraud_transactions = int(
                    (df["Class"] == 1).sum()
                )

                if total_transactions > 0:

                    normal_rate = round(
                        (
                            normal_transactions
                            /
                            total_transactions
                        ) * 100,
                        2
                    )

                    fraud_rate = round(
                        (
                            fraud_transactions
                            /
                            total_transactions
                        ) * 100,
                        2
                    )

    except Exception:

        pass

    return render_template(
        "dashboard.html",

        total_transactions=total_transactions,

        normal_transactions=normal_transactions,

        fraud_transactions=fraud_transactions,

        normal_rate=normal_rate,

        fraud_rate=fraud_rate
    )


# ============================================================
# FRAUD DETECTION
# ============================================================

@app.route(
    "/detect",
    methods=["GET", "POST"]
)
def detect():

    if "user" not in session:

        flash(
            "Please login first.",
            "warning"
        )

        return redirect(
            url_for("login")
        )

    result = None
    probability = None

    if request.method == "POST":

        try:

            transaction = {}

            # ------------------------------------------------
            # TIME
            # ------------------------------------------------

            transaction["Time"] = float(
                request.form.get(
                    "Time",
                    0
                )
            )

            # ------------------------------------------------
            # V1 - V28
            # ------------------------------------------------

            for i in range(1, 29):

                transaction[f"V{i}"] = float(
                    request.form.get(
                        f"V{i}",
                        0
                    )
                )

            # ------------------------------------------------
            # AMOUNT
            # ------------------------------------------------

            transaction["Amount"] = float(
                request.form.get(
                    "Amount",
                    0
                )
            )

            # ------------------------------------------------
            # PREDICTION
            # ------------------------------------------------

            prediction = predict_transaction(
                transaction
            )

            # ------------------------------------------------
            # HANDLE MODEL RESULT
            # ------------------------------------------------

            if isinstance(prediction, dict):

                result = prediction.get(
                    "result",
                    "Prediction completed"
                )

                probability = prediction.get(
                    "fraud_probability",
                    0
                )

            else:

                if int(prediction) == 1:

                    result = "Fraudulent Transaction"

                else:

                    result = "Normal Transaction"

                probability = 0

            # =================================================
            # SAVE PREDICTION HISTORY
            # =================================================

            history_result = result

            if "fraud" in str(result).lower():

                history_result = "Fraud"

            elif "normal" in str(result).lower():

                history_result = "Normal"

            # ------------------------------------------------
            # PROBABILITY KO NUMBER MEIN CONVERT KARNA
            # ------------------------------------------------

            try:

                history_probability = float(
                    probability
                )

            except (TypeError, ValueError):

                history_probability = 0.0

            # ------------------------------------------------
            # CURRENT DATE AND TIME
            # ------------------------------------------------

            prediction_datetime = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            # ------------------------------------------------
            # SAVE INTO DATABASE
            # ------------------------------------------------

            connection = get_db_connection()

            connection.execute(
                """
                INSERT INTO prediction_history
                (
                    user_id,
                    datetime,
                    amount,
                    result,
                    probability
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    session["user_id"],
                    prediction_datetime,
                    float(transaction["Amount"]),
                    history_result,
                    history_probability
                )
            )

            connection.commit()

            connection.close()

        except Exception as e:

            flash(
                f"Prediction error: {str(e)}",
                "danger"
            )

    return render_template(
        "detect.html",

        result=result,

        probability=probability
    )


# ============================================================
# LOAD SAMPLE TRANSACTION FROM CSV
# ============================================================

@app.route("/sample-transaction")
def sample_transaction():

    # User must be logged in
    if "user" not in session:

        return {
            "error": "Unauthorized"
        }, 401

    try:

        # Load credit card dataset
        df = pd.read_csv(
            DATA_FILE
        )

        # Take first transaction
        sample = df.iloc[0]

        # Prepare transaction
        transaction = {

            "Time": float(
                sample["Time"]
            ),

            "Amount": float(
                sample["Amount"]
            )
        }

        # Add V1 to V28
        for i in range(1, 29):

            column = f"V{i}"

            transaction[column] = float(
                sample[column]
            )

        # Actual class for reference
        transaction["Class"] = int(
            sample["Class"]
        )

        return transaction

    except Exception as e:

        return {
            "error": str(e)
        }, 500


# ============================================================
# BULK PREDICTION
# ============================================================

@app.route(
    "/bulk-prediction",
    methods=["GET", "POST"]
)
def bulk_prediction():

    # --------------------------------------------------------
    # LOGIN PROTECTION
    # --------------------------------------------------------

    if "user" not in session:

        flash(
            "Please login first.",
            "warning"
        )

        return redirect(
            url_for("login")
        )

    results = []

    total_predictions = 0
    normal_predictions = 0
    fraud_predictions = 0

    error = None
    success = None

    # --------------------------------------------------------
    # HANDLE CSV UPLOAD
    # --------------------------------------------------------

    if request.method == "POST":

        try:

            uploaded_file = request.files.get(
                "file"
            )

            if not uploaded_file:

                error = "Please select a CSV file."

                return render_template(
                    "bulk_prediction.html",

                    results=results,

                    total_predictions=total_predictions,

                    normal_predictions=normal_predictions,

                    fraud_predictions=fraud_predictions,

                    error=error,

                    success=success
                )

            if uploaded_file.filename == "":

                error = "Please select a CSV file."

                return render_template(
                    "bulk_prediction.html",

                    results=results,

                    total_predictions=total_predictions,

                    normal_predictions=normal_predictions,

                    fraud_predictions=fraud_predictions,

                    error=error,

                    success=success
                )

            if not uploaded_file.filename.lower().endswith(".csv"):

                error = "Only CSV files are allowed."

                return render_template(
                    "bulk_prediction.html",

                    results=results,

                    total_predictions=total_predictions,

                    normal_predictions=normal_predictions,

                    fraud_predictions=fraud_predictions,

                    error=error,

                    success=success
                )

            df = pd.read_csv(
                uploaded_file
            )

            required_columns = (
                ["Time"]
                + [f"V{i}" for i in range(1, 29)]
                + ["Amount"]
            )

            missing_columns = [
                column
                for column in required_columns
                if column not in df.columns
            ]

            if missing_columns:

                error = (
                    "Required columns are missing: "
                    + ", ".join(missing_columns)
                )

                return render_template(
                    "bulk_prediction.html",

                    results=results,

                    total_predictions=total_predictions,

                    normal_predictions=normal_predictions,

                    fraud_predictions=fraud_predictions,

                    error=error,

                    success=success
                )

            if df.empty:

                error = "The uploaded CSV file is empty."

                return render_template(
                    "bulk_prediction.html",

                    results=results,

                    total_predictions=total_predictions,

                    normal_predictions=normal_predictions,

                    fraud_predictions=fraud_predictions,

                    error=error,

                    success=success
                )

            for column in required_columns:

                df[column] = pd.to_numeric(
                    df[column],
                    errors="coerce"
                )

            if df[required_columns].isnull().any().any():

                error = (
                    "The CSV contains empty or invalid "
                    "values in the required model columns."
                )

                return render_template(
                    "bulk_prediction.html",

                    results=results,

                    total_predictions=total_predictions,

                    normal_predictions=normal_predictions,

                    fraud_predictions=fraud_predictions,

                    error=error,

                    success=success
                )

            for _, row in df.iterrows():

                transaction = {}

                transaction["Time"] = float(
                    row["Time"]
                )

                for i in range(1, 29):

                    transaction[f"V{i}"] = float(
                        row[f"V{i}"]
                    )

                transaction["Amount"] = float(
                    row["Amount"]
                )

                prediction = predict_transaction(
                    transaction
                )

                if isinstance(prediction, dict):

                    prediction_result = prediction.get(
                        "result",
                        "Normal Transaction"
                    )

                    fraud_probability = prediction.get(
                        "fraud_probability",
                        0
                    )

                else:

                    if int(prediction) == 1:

                        prediction_result = (
                            "Fraudulent Transaction"
                        )

                    else:

                        prediction_result = (
                            "Normal Transaction"
                        )

                    fraud_probability = 0

                if prediction_result == "Fraudulent Transaction":

                    fraud_predictions += 1

                else:

                    normal_predictions += 1

                total_predictions += 1

                results.append({

                    "Amount": round(
                        float(row["Amount"]),
                        2
                    ),

                    "Prediction": prediction_result,

                    "Fraud_Probability": round(
                        float(fraud_probability),
                        2
                    )

                })

            success = (
                f"{total_predictions} transactions analyzed successfully."
            )

        except Exception as e:

            error = (
                f"Bulk prediction error: {str(e)}"
            )

    return render_template(

        "bulk_prediction.html",

        results=results,

        total_predictions=total_predictions,

        normal_predictions=normal_predictions,

        fraud_predictions=fraud_predictions,

        error=error,

        success=success
    )


# ============================================================
# ANALYTICS
# ============================================================

@app.route("/analytics")
def analytics():

    if "user" not in session:

        flash(
            "Please login first.",
            "warning"
        )

        return redirect(url_for("login"))

    total_transactions = 0
    normal_transactions = 0
    fraud_transactions = 0
    normal_rate = 0
    fraud_rate = 0

    pie_chart = url_for(
        "static",
        filename="graphs/fraud_pie_chart.png"
    )

    bar_chart = url_for(
        "static",
        filename="graphs/transaction_bar_chart.png"
    )

    rate_chart = url_for(
        "static",
        filename="graphs/fraud_rate_chart.png"
    )

    amount_chart = url_for(
        "static",
        filename="graphs/transaction_amount_chart.png"
    )

    class_chart = url_for(
        "static",
        filename="graphs/transaction_class_chart.png"
    )

    try:

        if not os.path.exists(DATA_FILE):

            flash(
                "creditcard.csv file was not found.",
                "danger"
            )

            return render_template(
                "analytics.html",
                total_transactions=0,
                normal_transactions=0,
                fraud_transactions=0,
                normal_rate=0,
                fraud_rate=0,
                pie_chart=pie_chart,
                bar_chart=bar_chart,
                rate_chart=rate_chart,
                amount_chart=amount_chart,
                class_chart=class_chart
            )

        df = pd.read_csv(
            DATA_FILE
        )

        if "Class" not in df.columns:

            flash(
                "Class column is missing from dataset.",
                "danger"
            )

            return render_template(
                "analytics.html",
                total_transactions=0,
                normal_transactions=0,
                fraud_transactions=0,
                normal_rate=0,
                fraud_rate=0,
                pie_chart=pie_chart,
                bar_chart=bar_chart,
                rate_chart=rate_chart,
                amount_chart=amount_chart,
                class_chart=class_chart
            )

        total_transactions = len(df)

        normal_transactions = int(
            (df["Class"] == 0).sum()
        )

        fraud_transactions = int(
            (df["Class"] == 1).sum()
        )

        if total_transactions > 0:

            normal_rate = round(
                (
                    normal_transactions
                    /
                    total_transactions
                ) * 100,
                2
            )

            fraud_rate = round(
                (
                    fraud_transactions
                    /
                    total_transactions
                ) * 100,
                2
            )

        green = "#16A085"
        red = "#E74C3C"
        blue = "#3498DB"
        purple = "#8E44AD"
        orange = "#F39C12"
        teal = "#1ABC9C"
        navy = "#2C3E50"
        gold = "#E67E22"

        # ====================================================
        # 1. PIE CHART
        # ====================================================

        plt.close("all")

        fig, ax = plt.subplots(
            figsize=(6.5, 4.8)
        )

        values = [
            normal_transactions,
            fraud_transactions
        ]

        labels = [
            "Normal Transactions",
            "Fraud Transactions"
        ]

        if sum(values) > 0:

            wedges, texts, autotexts = ax.pie(
                values,
                labels=labels,
                autopct="%1.2f%%",
                startangle=90,
                colors=[green, red],
                wedgeprops={
                    "edgecolor": "white",
                    "linewidth": 2
                }
            )

            for text in autotexts:

                text.set_fontsize(10)

                text.set_weight(
                    "bold"
                )

        ax.set_title(
            "Normal vs Fraud Transactions",
            fontsize=14,
            fontweight="bold"
        )

        fig.tight_layout()

        fig.savefig(
            os.path.join(
                GRAPH_FOLDER,
                "fraud_pie_chart.png"
            ),
            dpi=150,
            bbox_inches="tight"
        )

        plt.close(fig)

        # ====================================================
        # 2. BAR CHART
        # ====================================================

        plt.close("all")

        fig, ax = plt.subplots(
            figsize=(6.5, 4.5)
        )

        categories = [
            "Normal",
            "Fraud"
        ]

        counts = [
            normal_transactions,
            fraud_transactions
        ]

        bars = ax.bar(
            categories,
            counts,
            color=[blue, red],
            width=0.55
        )

        ax.set_title(
            "Transaction Comparison",
            fontsize=14,
            fontweight="bold"
        )

        ax.set_ylabel(
            "Number of Transactions"
        )

        ax.grid(
            axis="y",
            alpha=0.18
        )

        for bar, value in zip(
            bars,
            counts
        ):

            ax.text(
                bar.get_x()
                + bar.get_width() / 2,
                bar.get_height(),
                f"{value:,}",
                ha="center",
                va="bottom",
                fontsize=10,
                fontweight="bold"
            )

        fig.tight_layout()

        fig.savefig(
            os.path.join(
                GRAPH_FOLDER,
                "transaction_bar_chart.png"
            ),
            dpi=150,
            bbox_inches="tight"
        )

        plt.close(fig)

        # ====================================================
        # 3. FRAUD RATE CHART
        # ====================================================

        plt.close("all")

        fig, ax = plt.subplots(
            figsize=(6.5, 4.5)
        )

        rates = [
            normal_rate,
            fraud_rate
        ]

        bars = ax.bar(
            [
                "Normal Rate",
                "Fraud Rate"
            ],
            rates,
            color=[purple, orange],
            width=0.55
        )

        ax.set_title(
            "Fraud Rate vs Normal Rate",
            fontsize=14,
            fontweight="bold"
        )

        ax.set_ylabel(
            "Percentage (%)"
        )

        ax.set_ylim(
            0,
            max(
                100,
                max(rates) + 5
            )
            if rates
            else 100
        )

        ax.grid(
            axis="y",
            alpha=0.18
        )

        for bar, value in zip(
            bars,
            rates
        ):

            ax.text(
                bar.get_x()
                + bar.get_width() / 2,
                bar.get_height(),
                f"{value:.2f}%",
                ha="center",
                va="bottom",
                fontsize=10,
                fontweight="bold"
            )

        fig.tight_layout()

        fig.savefig(
            os.path.join(
                GRAPH_FOLDER,
                "fraud_rate_chart.png"
            ),
            dpi=150,
            bbox_inches="tight"
        )

        plt.close(fig)

        # ====================================================
        # 4. TRANSACTION AMOUNT DISTRIBUTION
        # ====================================================

        plt.close("all")

        fig, ax = plt.subplots(
            figsize=(6.5, 4.5)
        )

        if "Amount" in df.columns:

            amounts = pd.to_numeric(
                df["Amount"],
                errors="coerce"
            ).dropna()

            if not amounts.empty:

                bins = 10

                counts_hist, edges, patches = ax.hist(
                    amounts,
                    bins=bins,
                    edgecolor="white",
                    linewidth=1.0
                )

                histogram_colors = [
                    blue,
                    purple,
                    teal,
                    green,
                    orange,
                    gold,
                    red,
                    navy,
                    "#27AE60",
                    "#9B59B6"
                ]

                for patch, color in zip(
                    patches,
                    histogram_colors
                ):

                    patch.set_facecolor(
                        color
                    )

                ax.set_xlabel(
                    "Transaction Amount"
                )

                ax.set_ylabel(
                    "Number of Transactions"
                )

        else:

            ax.text(
                0.5,
                0.5,
                "Amount column not available",
                ha="center",
                va="center",
                transform=ax.transAxes
            )

        ax.set_title(
            "Transaction Amount Distribution",
            fontsize=14,
            fontweight="bold"
        )

        ax.grid(
            axis="y",
            alpha=0.15
        )

        fig.tight_layout()

        fig.savefig(
            os.path.join(
                GRAPH_FOLDER,
                "transaction_amount_chart.png"
            ),
            dpi=150,
            bbox_inches="tight"
        )

        plt.close(fig)

        # ====================================================
        # 5. TRANSACTION CLASS ANALYSIS
        # ====================================================

        plt.close("all")

        fig, ax = plt.subplots(
            figsize=(6.5, 4.5)
        )

        class_labels = [
            "Normal Class (0)",
            "Fraud Class (1)"
        ]

        class_values = [
            normal_transactions,
            fraud_transactions
        ]

        bars = ax.bar(
            class_labels,
            class_values,
            color=[teal, red],
            width=0.55
        )

        ax.set_title(
            "Transaction Class Analysis",
            fontsize=14,
            fontweight="bold"
        )

        ax.set_ylabel(
            "Transactions"
        )

        ax.grid(
            axis="y",
            alpha=0.18
        )

        for bar, value in zip(
            bars,
            class_values
        ):

            ax.text(
                bar.get_x()
                + bar.get_width() / 2,
                bar.get_height(),
                f"{value:,}",
                ha="center",
                va="bottom",
                fontsize=10,
                fontweight="bold"
            )

        fig.tight_layout()

        fig.savefig(
            os.path.join(
                GRAPH_FOLDER,
                "transaction_class_chart.png"
            ),
            dpi=150,
            bbox_inches="tight"
        )

        plt.close(fig)

    except Exception as e:

        flash(
            f"Analytics error: {str(e)}",
            "danger"
        )

    return render_template(
        "analytics.html",

        total_transactions=total_transactions,

        normal_transactions=normal_transactions,

        fraud_transactions=fraud_transactions,

        normal_rate=normal_rate,

        fraud_rate=fraud_rate,

        pie_chart=pie_chart,

        bar_chart=bar_chart,

        rate_chart=rate_chart,

        amount_chart=amount_chart,

        class_chart=class_chart
    )


# ============================================================
# TRANSACTIONS
# ============================================================

@app.route("/transactions")
def transactions():

    if "user" not in session:

        flash(
            "Please login first.",
            "warning"
        )

        return redirect(
            url_for("login")
        )

    transactions_data = []

    total_transactions = 0

    try:

        if not os.path.exists(DATA_FILE):

            flash(
                "creditcard.csv file was not found.",
                "danger"
            )

            return render_template(
                "transactions.html",

                transactions=[],

                total_transactions=0
            )

        df = pd.read_csv(
            DATA_FILE
        )

        total_transactions = len(df)

        display_df = df.head(
            100
        ).copy()

        for index, row in display_df.iterrows():

            class_value = row.get(
                "Class",
                0
            )

            if int(class_value) == 1:

                status = "Fraud"

            else:

                status = "Normal"

            transaction_time = row.get(
                "Time",
                0
            )

            amount = row.get(
                "Amount",
                0
            )

            try:

                transaction_time = round(
                    float(transaction_time),
                    2
                )

            except Exception:

                transaction_time = 0

            try:

                amount = round(
                    float(amount),
                    2
                )

            except Exception:

                amount = 0

            transactions_data.append({

                "id": index + 1,

                "time": transaction_time,

                "amount": amount,

                "status": status

            })

    except Exception as e:

        flash(
            f"Transactions error: {str(e)}",
            "danger"
        )

    return render_template(

        "transactions.html",

        transactions=transactions_data,

        total_transactions=total_transactions
    )


# ============================================================
# ABOUT
# ============================================================

@app.route("/about")
def about():

    return render_template(
        "about.html"
    )


# ============================================================
# CONTACT
# ============================================================

@app.route(
    "/contact",
    methods=["GET", "POST"]
)
def contact():

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        subject = request.form.get(
            "subject",
            ""
        ).strip()

        message = request.form.get(
            "message",
            ""
        ).strip()

        if not name or not email or not subject or not message:

            flash(
                "Please fill all contact form fields.",
                "danger"
            )

            return render_template(
                "contact.html"
            )

        if "@" not in email or "." not in email:

            flash(
                "Please enter a valid email address.",
                "danger"
            )

            return render_template(
                "contact.html"
            )

        print()
        print("=" * 60)
        print("CONTACT MESSAGE RECEIVED")
        print("=" * 60)
        print("Name    :", name)
        print("Email   :", email)
        print("Subject :", subject)
        print("Message :", message)
        print("=" * 60)
        print()

        flash(
            "Your message has been submitted successfully!",
            "success"
        )

    return render_template(
        "contact.html"
    )


# ============================================================
# HELP PAGE
# ============================================================

@app.route("/help")
def help_page():

    return render_template(
        "help.html"
    )


# ============================================================
# SETTINGS PAGE
# ============================================================

@app.route("/settings")
def settings():

    # User login check
    if "user" not in session:

        flash(
            "Please login first.",
            "warning"
        )

        return redirect(
            url_for("login")
        )

    # Open Settings page
    return render_template(
        "settings.html"
    )


# ============================================================
# USER PROFILE
# ============================================================

@app.route("/profile")
def profile():

    # --------------------------------------------------------
    # LOGIN PROTECTION
    # --------------------------------------------------------

    if "user" not in session:

        flash(
            "Please login first.",
            "warning"
        )

        return redirect(
            url_for("login")
        )

    # --------------------------------------------------------
    # DEFAULT USER INFORMATION
    # --------------------------------------------------------

    user_id = session.get(
        "user_id"
    )

    user_name = session.get(
        "user_name",
        ""
    )

    user_email = session.get(
        "user",
        ""
    )

    # Default profile picture
    profile_image = session.get(
        "profile_image"
    )

    # --------------------------------------------------------
    # GET CURRENT USER FROM DATABASE
    # --------------------------------------------------------

    try:

        connection = get_db_connection()

        user = connection.execute(
            """
            SELECT
                id,
                name,
                email,
                profile_image
            FROM users
            WHERE id = ?
            """,
            (
                user_id,
            )
        ).fetchone()

        connection.close()

        # ----------------------------------------------------
        # UPDATE INFORMATION FROM DATABASE
        # ----------------------------------------------------

        if user:

            user_id = user["id"]

            user_name = user["name"]

            user_email = user["email"]

            profile_image = user["profile_image"]

            # Keep session updated
            session["profile_image"] = profile_image

    except Exception as e:

        flash(
            f"Profile error: {str(e)}",
            "danger"
        )

    # --------------------------------------------------------
    # SHOW PROFILE PAGE
    # --------------------------------------------------------

    return render_template(
        "profile.html",

        user_id=user_id,

        user_name=user_name,

        user_email=user_email,

        profile_image=profile_image
    )


# ============================================================
# UPLOAD PROFILE PICTURE
# ============================================================

@app.route(
    "/upload-profile-image",
    methods=["POST"]
)
def upload_profile_image():

    # --------------------------------------------------------
    # LOGIN PROTECTION
    # --------------------------------------------------------

    if "user" not in session:

        flash(
            "Please login first.",
            "warning"
        )

        return redirect(
            url_for("login")
        )

    # --------------------------------------------------------
    # GET CURRENT USER ID
    # --------------------------------------------------------

    user_id = session.get(
        "user_id"
    )

    # --------------------------------------------------------
    # GET UPLOADED FILE
    # --------------------------------------------------------

    uploaded_file = request.files.get(
        "profile_image"
    )

    # --------------------------------------------------------
    # CHECK FILE
    # --------------------------------------------------------

    if not uploaded_file:

        flash(
            "Please select a profile picture.",
            "warning"
        )

        return redirect(
            url_for("profile")
        )

    if uploaded_file.filename == "":

        flash(
            "Please select a profile picture.",
            "warning"
        )

        return redirect(
            url_for("profile")
        )

    # --------------------------------------------------------
    # SECURE ORIGINAL FILE NAME
    # --------------------------------------------------------

    original_filename = secure_filename(
        uploaded_file.filename
    )

    # --------------------------------------------------------
    # GET FILE EXTENSION
    # --------------------------------------------------------

    if "." not in original_filename:

        flash(
            "Invalid image file.",
            "danger"
        )

        return redirect(
            url_for("profile")
        )

    extension = original_filename.rsplit(
        ".",
        1
    )[1].lower()

    # --------------------------------------------------------
    # CHECK ALLOWED EXTENSION
    # --------------------------------------------------------

    if extension not in ALLOWED_PROFILE_EXTENSIONS:

        flash(
            "Only PNG, JPG, JPEG, WEBP or GIF images are allowed.",
            "danger"
        )

        return redirect(
            url_for("profile")
        )

    connection = None

    try:

        # ----------------------------------------------------
        # GET OLD PROFILE IMAGE
        # ----------------------------------------------------

        connection = get_db_connection()

        old_user = connection.execute(
            """
            SELECT profile_image
            FROM users
            WHERE id = ?
            """,
            (
                user_id,
            )
        ).fetchone()

        # ----------------------------------------------------
        # CREATE UNIQUE FILE NAME
        # ----------------------------------------------------

        timestamp = datetime.now().strftime(
            "%Y%m%d%H%M%S%f"
        )

        filename = (
            f"profile_{user_id}_{timestamp}.{extension}"
        )

        file_path = os.path.join(
            PROFILE_FOLDER,
            filename
        )

        # ----------------------------------------------------
        # SAVE NEW PROFILE PICTURE
        # ----------------------------------------------------

        uploaded_file.save(
            file_path
        )

        # ----------------------------------------------------
        # SAVE FILE NAME IN DATABASE
        # ----------------------------------------------------

        connection.execute(
            """
            UPDATE users
            SET profile_image = ?
            WHERE id = ?
            """,
            (
                filename,
                user_id
            )
        )

        connection.commit()

        connection.close()

        connection = None

        # ----------------------------------------------------
        # UPDATE SESSION
        # ----------------------------------------------------

        session["profile_image"] = filename

        # ----------------------------------------------------
        # DELETE OLD PROFILE PICTURE
        # ----------------------------------------------------

        if old_user:

            old_filename = old_user["profile_image"]

            if old_filename:

                old_filename = secure_filename(
                    old_filename
                )

                old_file_path = os.path.join(
                    PROFILE_FOLDER,
                    old_filename
                )

                # Only delete an existing local file
                if os.path.isfile(old_file_path):

                    try:

                        os.remove(
                            old_file_path
                        )

                    except OSError:

                        pass

        # ----------------------------------------------------
        # SUCCESS MESSAGE
        # ----------------------------------------------------

        flash(
            "Profile picture updated successfully!",
            "success"
        )

    except Exception as e:

        if connection:

            connection.close()

        # If something went wrong, show the error
        flash(
            f"Profile picture upload error: {str(e)}",
            "danger"
        )

    # --------------------------------------------------------
    # RETURN TO PROFILE
    # --------------------------------------------------------

    return redirect(
        url_for("profile")
    )
    # ============================================================
# DELETE PROFILE PICTURE
# ============================================================

@app.route(
    "/delete-profile-image",
    methods=["POST"]
)
def delete_profile_image():

    # --------------------------------------------------------
    # LOGIN PROTECTION
    # --------------------------------------------------------

    if "user" not in session:

        flash(
            "Please login first.",
            "warning"
        )

        return redirect(
            url_for("login")
        )

    # --------------------------------------------------------
    # GET CURRENT USER ID
    # --------------------------------------------------------

    user_id = session.get(
        "user_id"
    )

    connection = None

    try:

        # ----------------------------------------------------
        # CONNECT TO DATABASE
        # ----------------------------------------------------

        connection = get_db_connection()

        # ----------------------------------------------------
        # GET CURRENT PROFILE IMAGE
        # ----------------------------------------------------

        user = connection.execute(
            """
            SELECT profile_image
            FROM users
            WHERE id = ?
            """,
            (
                user_id,
            )
        ).fetchone()

        # ----------------------------------------------------
        # CHECK PROFILE PICTURE
        # ----------------------------------------------------

        if not user or not user["profile_image"]:

            connection.close()

            flash(
                "No profile picture found.",
                "warning"
            )

            return redirect(
                url_for("profile")
            )

        # ----------------------------------------------------
        # GET OLD IMAGE FILE NAME
        # ----------------------------------------------------

        old_filename = secure_filename(
            user["profile_image"]
        )

        # ----------------------------------------------------
        # REMOVE IMAGE FROM DATABASE
        # ----------------------------------------------------

        connection.execute(
            """
            UPDATE users
            SET profile_image = NULL
            WHERE id = ?
            """,
            (
                user_id,
            )
        )

        connection.commit()

        connection.close()

        connection = None

        # ----------------------------------------------------
        # DELETE ACTUAL IMAGE FROM FOLDER
        # ----------------------------------------------------

        old_file_path = os.path.join(
            PROFILE_FOLDER,
            old_filename
        )

        if os.path.isfile(old_file_path):

            try:

                os.remove(
                    old_file_path
                )

            except OSError:

                pass

        # ----------------------------------------------------
        # REMOVE PROFILE IMAGE FROM SESSION
        # ----------------------------------------------------

        session.pop(
            "profile_image",
            None
        )

        # ----------------------------------------------------
        # SUCCESS MESSAGE
        # ----------------------------------------------------

        flash(
            "Profile picture deleted successfully!",
            "success"
        )

    except Exception as e:

        if connection:

            connection.close()

        flash(
            f"Profile picture delete error: {str(e)}",
            "danger"
        )

    # --------------------------------------------------------
    # RETURN TO PROFILE PAGE
    # --------------------------------------------------------

    return redirect(
        url_for("profile")
    )


# ============================================================
# EDIT USER PROFILE
# ============================================================

@app.route(
    "/edit-profile",
    methods=["POST"]
)
def edit_profile():

    # --------------------------------------------------------
    # LOGIN PROTECTION
    # --------------------------------------------------------

    if "user" not in session:

        flash(
            "Please login first.",
            "warning"
        )

        return redirect(
            url_for("login")
        )

    # --------------------------------------------------------
    # GET CURRENT USER ID
    # --------------------------------------------------------

    user_id = session.get(
        "user_id"
    )

    # --------------------------------------------------------
    # GET UPDATED INFORMATION FROM FORM
    # --------------------------------------------------------

    name = request.form.get(
        "name",
        ""
    ).strip()

    email = request.form.get(
        "email",
        ""
    ).strip().lower()

    # --------------------------------------------------------
    # CHECK EMPTY FIELDS
    # --------------------------------------------------------

    if not name or not email:

        flash(
            "Name and email are required.",
            "warning"
        )

        return redirect(
            url_for("profile")
        )

    # --------------------------------------------------------
    # BASIC EMAIL VALIDATION
    # --------------------------------------------------------

    if "@" not in email or "." not in email:

        flash(
            "Please enter a valid email address.",
            "danger"
        )

        return redirect(
            url_for("profile")
        )

    connection = None

    try:

        # ----------------------------------------------------
        # CONNECT TO DATABASE
        # ----------------------------------------------------

        connection = get_db_connection()

        # ----------------------------------------------------
        # CHECK IF EMAIL IS ALREADY USED BY ANOTHER USER
        # ----------------------------------------------------

        existing_user = connection.execute(
            """
            SELECT id
            FROM users
            WHERE email = ?
            AND id != ?
            """,
            (
                email,
                user_id
            )
        ).fetchone()

        if existing_user:

            connection.close()

            flash(
                "This email is already registered with another account.",
                "danger"
            )

            return redirect(
                url_for("profile")
            )

        # ----------------------------------------------------
        # UPDATE USER INFORMATION
        # ----------------------------------------------------

        connection.execute(
            """
            UPDATE users
            SET
                name = ?,
                email = ?
            WHERE id = ?
            """,
            (
                name,
                email,
                user_id
            )
        )

        connection.commit()

        connection.close()

        # ----------------------------------------------------
        # UPDATE SESSION INFORMATION
        #
        # This makes the new name/email immediately visible
        # throughout the dashboard.
        # ----------------------------------------------------

        session["user_name"] = name

        session["user"] = email

        # ----------------------------------------------------
        # SUCCESS MESSAGE
        # ----------------------------------------------------

        flash(
            "Profile updated successfully!",
            "success"
        )

    except sqlite3.IntegrityError:

        if connection:

            connection.close()

        flash(
            "This email is already registered.",
            "danger"
        )

    except Exception as e:

        if connection:

            connection.close()

        flash(
            f"Profile update error: {str(e)}",
            "danger"
        )

    # --------------------------------------------------------
    # RETURN TO PROFILE PAGE
    # --------------------------------------------------------

    return redirect(
        url_for("profile")
    )


# ============================================================
# FRAUD ALERTS
# ============================================================

@app.route("/fraud-alerts")
def fraud_alerts():

    # Login protection
    if "user" not in session:

        flash(
            "Please login first.",
            "warning"
        )

        return redirect(
            url_for("login")
        )

    return render_template(
        "fraud_alerts.html"
    )


# ============================================================
# PREDICTION HISTORY
# ============================================================

@app.route("/prediction-history")
def prediction_history():

    # --------------------------------------------------------
    # LOGIN PROTECTION
    # --------------------------------------------------------

    if "user" not in session:

        flash(
            "Please login first.",
            "warning"
        )

        return redirect(
            url_for("login")
        )

    # --------------------------------------------------------
    # DEFAULT VALUES
    # --------------------------------------------------------

    predictions = []

    # --------------------------------------------------------
    # LOAD CURRENT USER'S PREDICTIONS
    # --------------------------------------------------------

    try:

        connection = get_db_connection()

        history_rows = connection.execute(
            """
            SELECT
                id,
                datetime,
                amount,
                result,
                probability
            FROM prediction_history
            WHERE user_id = ?
            ORDER BY id DESC
            """,
            (
                session["user_id"],
            )
        ).fetchall()

        connection.close()

        # ----------------------------------------------------
        # CONVERT DATABASE ROWS INTO DICTIONARIES
        # ----------------------------------------------------

        for row in history_rows:

            predictions.append({

                "id": row["id"],

                "datetime": row["datetime"],

                "amount": row["amount"],

                "result": row["result"],

                "probability": row["probability"]

            })

    except Exception as e:

        flash(
            f"Prediction history error: {str(e)}",
            "danger"
        )

    # --------------------------------------------------------
    # SUMMARY COUNTS
    # --------------------------------------------------------

    total_predictions = len(
        predictions
    )

    fraud_predictions = sum(
        1
        for prediction in predictions
        if prediction.get("result") == "Fraud"
    )

    normal_predictions = sum(
        1
        for prediction in predictions
        if prediction.get("result") == "Normal"
    )

    # --------------------------------------------------------
    # SHOW PREDICTION HISTORY PAGE
    # --------------------------------------------------------

    return render_template(
        "prediction_history.html",

        predictions=predictions,

        total_predictions=total_predictions,

        fraud_predictions=fraud_predictions,

        normal_predictions=normal_predictions
    )


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
def logout():

    session.pop(
        "user",
        None
    )

    session.pop(
        "user_name",
        None
    )

    session.pop(
        "user_id",
        None
    )

    # Clear profile image from session
    session.pop(
        "profile_image",
        None
    )

    flash(
        "You have been logged out.",
        "success"
    )

    return redirect(
        url_for("login")
    )


# ============================================================
# INITIALIZE DATABASE
# ============================================================

initialize_database()


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 60)
    print("   CREDIT CARD FRAUD DETECTION SYSTEM")
    print("=" * 60)
    print("   Server starting...")
    print("   URL: http://127.0.0.1:5000")
    print("=" * 60)
    print()

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )