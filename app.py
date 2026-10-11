from datetime import datetime
import sqlite3
import re

from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "expense_tracker_secret_key"


# =========================================================
# DATABASE CONNECTION
# =========================================================

import os
import sqlite3

DB_PATH = "/tmp/expenses.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


# =========================================================
# DATABASE SETUP
# =========================================================

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            date TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            notes TEXT,
            amount REAL NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )

    expense_columns = [row[1] for row in cursor.execute("PRAGMA table_info(expenses)").fetchall()]
    if "user_id" not in expense_columns:
        cursor.execute("ALTER TABLE expenses ADD COLUMN user_id INTEGER")
    if "notes" not in expense_columns:
        cursor.execute("ALTER TABLE expenses ADD COLUMN notes TEXT")

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS budget (
            user_id INTEGER PRIMARY KEY,
            amount REAL NOT NULL DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sub_budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )

    budget_columns = [row[1] for row in cursor.execute("PRAGMA table_info(budget)").fetchall()]
    if "id" in budget_columns and "user_id" not in budget_columns:
        cursor.execute("ALTER TABLE budget RENAME TO budget_old")
        cursor.execute(
            """
            CREATE TABLE budget (
                user_id INTEGER PRIMARY KEY,
                amount REAL NOT NULL DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """
        )
        old_budget = cursor.execute("SELECT amount FROM budget_old WHERE id = 1").fetchone()
        if old_budget:
            users = cursor.execute("SELECT id FROM users").fetchall()
            for user in users:
                cursor.execute(
                    "INSERT OR IGNORE INTO budget (user_id, amount) VALUES (?, ?)",
                    (user["id"], old_budget[0]),
                )
        cursor.execute("DROP TABLE budget_old")

    conn.commit()
    conn.close()


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():
    return render_template("home.html")


# =========================================================
# SIGN UP
# =========================================================

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not name or not email or not password or not confirm_password:
            return render_template("signup.html", error="Please fill all required fields.")

        if not re.fullmatch(r"(?=.{6,30}@gmail\.com$)[a-zA-Z0-9]+([.][a-zA-Z0-9]+)*@gmail\.com", email):
            return render_template("signup.html", error="Please enter a valid Gmail address.")

        if password != confirm_password:
            return render_template("signup.html", error="Passwords do not match.")

        conn = get_db_connection()
        existing_user = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing_user:
            conn.close()
            return render_template("signup.html", error="This Gmail is already registered. Please use another Gmail.")

        hashed_password = generate_password_hash(password)
        conn.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)", (name, email, hashed_password))
        conn.commit()
        conn.close()
        return redirect("/signin")

    return render_template("signup.html")


# =========================================================
# SIGN IN
# =========================================================

@app.route("/signin", methods=["GET", "POST"])
def signin():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            return render_template("signin.html", error="Please enter your email and password.")

        conn = get_db_connection()
        user = conn.execute("SELECT id, name, email, password FROM users WHERE email = ?", (email,)).fetchone()
        if user is None:
            conn.close()
            return render_template("signin.html", error="Incorrect email or password.")

        password_valid = False
        try:
            password_valid = check_password_hash(user["password"], password)
        except ValueError:
            password_valid = False

        if not password_valid and user["password"] == password:
            new_hash = generate_password_hash(password)
            conn.execute("UPDATE users SET password = ? WHERE id = ?", (new_hash, user["id"]))
            conn.commit()
            password_valid = True

        if not password_valid:
            conn.close()
            return render_template("signin.html", error="Incorrect email or password.")

        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        conn.close()
        return redirect("/dashboard")

    return render_template("signin.html")


# =========================================================
# RESET PASSWORD
# =========================================================

@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        if new_password != confirm_password:
            return render_template("reset_password.html", error="Passwords do not match.")

        conn = get_db_connection()
        user = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if user is None:
            conn.close()
            return render_template("reset_password.html", error="This Gmail is not registered.")

        new_hash = generate_password_hash(new_password)
        conn.execute("UPDATE users SET password = ? WHERE id = ?", (new_hash, user["id"]))
        conn.commit()
        conn.close()
        return redirect("/signin")

    return render_template("reset_password.html")


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# =========================================================
# GET USER EXPENSES
# =========================================================

def get_user_expenses(user_id):
    conn = get_db_connection()
    rows = conn.execute(
        """
        SELECT id, date, category, description, notes, amount
        FROM expenses
        WHERE user_id = ?
        ORDER BY date DESC, id DESC
        """,
        (user_id,),
    ).fetchall()
    conn.close()
    return rows


# =========================================================
# GET USER BUDGET
# =========================================================

def get_budget_amount(user_id):
    conn = get_db_connection()
    row = conn.execute("SELECT amount FROM budget WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    if row:
        return float(row["amount"])
    return 0.0


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect("/signin")

    user_id = session["user_id"]

    # ---------------- GET USER EXPENSES ----------------

    user_expenses = get_user_expenses(user_id)

    # ---------------- TOTAL EXPENSE ----------------

    total = sum(
        float(expense["amount"])
        for expense in user_expenses
    )

    # ---------------- CURRENT MONTH ----------------

    now = datetime.now()

    current_month = (
        f"{now.year:04d}-{now.month:02d}-"
    )

    # ---------------- MONTHLY EXPENSE ----------------

    monthly = sum(
        float(expense["amount"])
        for expense in user_expenses
        if expense["date"]
        and expense["date"].startswith(current_month)
    )

    # ---------------- BUDGET ----------------

    budget_amount = get_budget_amount(user_id)

    remaining = budget_amount - monthly

    # ---------------- TOP CATEGORY ----------------

    category_totals = {}

    for expense in user_expenses:

        category = expense["category"]

        amount = float(expense["amount"])

        category_totals[category] = (
            category_totals.get(category, 0.0)
            + amount
        )

    top_category_name = "No Data"

    top_category_amount = 0.0

    if category_totals:

        (
            top_category_name,
            top_category_amount
        ) = max(
            category_totals.items(),
            key=lambda item: item[1]
        )

    # =====================================================
    # CATEGORY SPENDING FOR CURRENT MONTH
    # =====================================================

    category_spending = {}

    for expense in user_expenses:

        if (
            expense["date"]
            and expense["date"].startswith(current_month)
        ):

            category = expense["category"]

            amount = float(expense["amount"])

            category_spending[category] = (
                category_spending.get(category, 0.0)
                + amount
            )

    # =====================================================
    # RETURN DASHBOARD
    # =====================================================

    return render_template(
        "dashboard.html",

        total=total,

        monthly=monthly,

        budget=budget_amount,

        remaining=remaining,

        recent_expenses=list(
            user_expenses[:5]
        ),

        top_category_name=top_category_name,

        top_category_amount=top_category_amount,

        category_spending=category_spending
    )

# =========================================================
# BUDGET
# =========================================================

@app.route("/budget", methods=["GET", "POST"])
def budget():
    if "user_id" not in session:
        return redirect("/signin")

    user_id = session["user_id"]
    conn = get_db_connection()

    if request.method == "POST":
        amount_text = request.form.get("amount", "").strip()

        try:
            budget_amount = float(amount_text or 0)
        except ValueError:
            conn.close()
            return redirect("/budget")

        if budget_amount < 0:
            conn.close()
            return redirect("/budget")

        distributed_row = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) AS total FROM sub_budgets WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        distributed_amount = float(distributed_row["total"])

        if budget_amount < distributed_amount:
            conn.close()
            return redirect("/budget")

        conn.execute(
            """
            INSERT INTO budget (user_id, amount)
            VALUES (?, ?)
            ON CONFLICT(user_id)
            DO UPDATE SET amount = excluded.amount
            """,
            (user_id, budget_amount),
        )
        conn.commit()

    budget_row = conn.execute("SELECT amount FROM budget WHERE user_id = ?", (user_id,)).fetchone()
    total_budget = float(budget_row["amount"]) if budget_row else 0.0

    sub_budgets = conn.execute(
        "SELECT id, category, amount FROM sub_budgets WHERE user_id = ? ORDER BY id DESC",
        (user_id,),
    ).fetchall()

    distributed_row = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) AS total FROM sub_budgets WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    distributed_amount = float(distributed_row["total"])
    remaining_distribution = max(total_budget - distributed_amount, 0.0)

    category_budgets = {}
    for item in sub_budgets:
        category = item["category"]
        category_budgets[category] = category_budgets.get(category, 0.0) + float(item["amount"])

    now = datetime.now()
    current_month = f"{now.year:04d}-{now.month:02d}-"
    category_spending = {}
    expenses = get_user_expenses(user_id)
    for expense in expenses:
        if expense["date"] and expense["date"].startswith(current_month):
            category = expense["category"]
            category_spending[category] = category_spending.get(category, 0.0) + float(expense["amount"])

    categories = [
        "Food",
        "Travel",
        "Shopping",
        "Entertainment",
        "Health",
        "Education",
        "Utilities",
        "Rent",
        "Other",
    ]

    budget_chart = []
    max_value = 1.0
    for category in categories:
        budget_value = float(category_budgets.get(category, 0.0))
        actual_value = float(category_spending.get(category, 0.0))
        max_value = max(max_value, budget_value, actual_value)

        if budget_value > 0:
            percentage = (actual_value / budget_value) * 100
        else:
            percentage = 0
        percentage = min(round(percentage, 1), 100)

        budget_chart.append(
            {
                "category": category,
                "budget": budget_value,
                "actual": actual_value,
                "percentage": percentage,
            }
        )

    for item in budget_chart:
        if max_value > 0:
            item["budget_height"] = max(
                round((item["budget"] / max_value) * 100, 1),
                2 if item["budget"] > 0 else 0,
            )
            item["actual_height"] = max(
                round((item["actual"] / max_value) * 100, 1),
                2 if item["actual"] > 0 else 0,
            )
        else:
            item["budget_height"] = 0
            item["actual_height"] = 0

    conn.close()
    return render_template(
        "budget.html",
        budget=total_budget,
        sub_budgets=sub_budgets,
        distributed_amount=distributed_amount,
        remaining_distribution=remaining_distribution,
        category_budgets=category_budgets,
        category_spending=category_spending,
        budget_chart=budget_chart,
    )


# =========================================================
# ADD EXPENSE
# =========================================================

@app.route("/add-expense", methods=["GET", "POST"])
def add_expense():
    if "user_id" not in session:
        return redirect("/signin")

    if request.method == "POST":
        amount = request.form.get("amount")
        date = request.form.get("date")
        category = request.form.get("category")
        description = request.form.get("description") or ""
        notes = request.form.get("notes") or ""

        if not amount or not date or not category:
            return "Missing required expense fields"

        try:
            amount = float(amount)
        except ValueError:
            return "Invalid amount"

        if amount < 0:
            return "Amount cannot be negative"

        conn = get_db_connection()
        conn.execute(
            """
            INSERT INTO expenses (user_id, date, category, description, notes, amount)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (session["user_id"], date, category, description, notes, amount),
        )
        conn.commit()
        conn.close()
        return redirect("/dashboard")

    return render_template("add_expense.html")


# =========================================================
# ALL EXPENSES
# =========================================================

@app.route("/expenses")
def expenses():
    if "user_id" not in session:
        return redirect("/signin")

    rows = get_user_expenses(session["user_id"])
    return render_template("expenses.html", expenses=rows)


# =========================================================
# DELETE EXPENSE
# =========================================================

@app.route("/delete-expense/<int:expense_id>", methods=["POST", "GET"])
def delete_expense(expense_id):
    if "user_id" not in session:
        return redirect("/signin")

    conn = get_db_connection()
    conn.execute("DELETE FROM expenses WHERE id = ? AND user_id = ?", (expense_id, session["user_id"]))
    conn.commit()
    conn.close()
    return redirect("/expenses")


@app.route("/edit-expense/<int:expense_id>", methods=["GET", "POST"])
def edit_expense(expense_id):
    if "user_id" not in session:
        return redirect("/signin")

    conn = get_db_connection()
    if request.method == "POST":
        date = request.form["date"]
        amount = request.form["amount"]
        category = request.form["category"]
        description = request.form["description"]
        notes = request.form.get("notes", "")

        conn.execute(
            """
            UPDATE expenses
            SET date = ?, amount = ?, category = ?, description = ?, notes = ?
            WHERE id = ? AND user_id = ?
            """,
            (date, amount, category, description, notes, expense_id, session["user_id"]),
        )
        conn.commit()
        conn.close()
        return redirect("/expenses")

    expense = conn.execute(
        "SELECT * FROM expenses WHERE id = ? AND user_id = ?",
        (expense_id, session["user_id"]),
    ).fetchone()
    conn.close()

    if expense is None:
        return "Expense not found"

    return render_template("edit_expense.html", expense=expense)


# =========================================================
# EDIT SUB BUDGET
# =========================================================

@app.route("/edit-sub-budget/<int:sub_budget_id>", methods=["POST"])
def edit_sub_budget(sub_budget_id):
    if "user_id" not in session:
        return redirect("/signin")

    user_id = session["user_id"]
    category = request.form.get("category", "").strip()
    amount_text = request.form.get("amount", "").strip()

    if not category or not amount_text:
        return redirect("/budget")

    try:
        new_amount = float(amount_text)
    except ValueError:
        return redirect("/budget")

    if new_amount <= 0:
        return redirect("/budget")

    conn = get_db_connection()
    budget_row = conn.execute("SELECT amount FROM budget WHERE user_id = ?", (user_id,)).fetchone()
    total_budget = float(budget_row["amount"]) if budget_row else 0.0

    distributed_row = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) AS total FROM sub_budgets WHERE user_id = ? AND id != ?",
        (user_id, sub_budget_id),
    ).fetchone()
    other_distributed = float(distributed_row["total"])

    if other_distributed + new_amount > total_budget:
        conn.close()
        return redirect("/budget")

    conn.execute(
        "UPDATE sub_budgets SET category = ?, amount = ? WHERE id = ? AND user_id = ?",
        (category, new_amount, sub_budget_id, user_id),
    )
    conn.commit()
    conn.close()
    return redirect("/budget")


# =========================================================
# ADD SUB BUDGET
# =========================================================

@app.route("/add-sub-budget", methods=["POST"])
def add_sub_budget():
    if "user_id" not in session:
        return redirect("/signin")

    user_id = session["user_id"]
    category = request.form.get("category", "").strip()
    amount_text = request.form.get("amount", "").strip()

    if not category or not amount_text:
        return redirect("/budget")

    try:
        amount = float(amount_text)
    except ValueError:
        return redirect("/budget")

    if amount <= 0:
        return redirect("/budget")

    conn = get_db_connection()
    budget_row = conn.execute("SELECT amount FROM budget WHERE user_id = ?", (user_id,)).fetchone()
    total_budget = float(budget_row["amount"]) if budget_row else 0.0

    distributed_row = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) AS total FROM sub_budgets WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    distributed_amount = float(distributed_row["total"])

    if distributed_amount + amount > total_budget:
        conn.close()
        return redirect("/budget")

    conn.execute(
        "INSERT INTO sub_budgets (user_id, category, amount) VALUES (?, ?, ?)",
        (user_id, category, amount),
    )
    conn.commit()
    conn.close()
    return redirect("/budget")


# =========================================================
# DELETE SUB BUDGET
# =========================================================

@app.route("/delete-sub-budget/<int:sub_budget_id>", methods=["POST"])
def delete_sub_budget(sub_budget_id):
    if "user_id" not in session:
        return redirect("/signin")

    conn = get_db_connection()
    conn.execute("DELETE FROM sub_budgets WHERE id = ? AND user_id = ?", (sub_budget_id, session["user_id"]))
    conn.commit()
    conn.close()
    return redirect("/budget")


# =========================================================
# REPORTS
# =========================================================

@app.route("/reports")
def reports():
    if "user_id" not in session:
        return redirect("/signin")

    user_id = session["user_id"]
    selected_month = request.args.get("month", "").strip() or datetime.now().strftime("%Y-%m")

    rows = get_user_expenses(user_id)


    
    # ALL-TIME ANALYTICS
    from collections import defaultdict
    from datetime import date

    today = date.today()
    category_totals_all = defaultdict(float)
    monthly_totals_all = defaultdict(float)
    total_spending = 0.0
    month_spending = 0.0
    expense_count = 0
    recent_expenses = []

    for expense in rows:
        raw_date = expense["date"] or ""

        try:
            expense_date = datetime.strptime(
                raw_date[:10], "%Y-%m-%d"
            ).date()
        except (ValueError, TypeError):
            continue

        amount = float(expense["amount"] or 0)
        category = expense["category"] or "Other"

        total_spending += amount
        expense_count += 1
        category_totals_all[category] += amount

        month_key = expense_date.strftime("%Y-%m")
        monthly_totals_all[month_key] += amount

        if (expense_date.year, expense_date.month) == (
            today.year, today.month
        ):
            month_spending += amount

        if len(recent_expenses) < 8:
            recent_expenses.append({
                "date": expense_date.strftime("%d %b %Y"),
                "description": expense["description"] or "",
                "category": category,
                "amount": amount
            })

    # Last six months, including current month
    month_labels = []
    month_values = []

    for offset in range(5, -1, -1):
        month_number = today.month - offset
        year = today.year

        while month_number <= 0:
            month_number += 12
            year -= 1

        month_date = date(year, month_number, 1)
        month_key = month_date.strftime("%Y-%m")

        month_labels.append(month_date.strftime("%b %Y"))
        month_values.append(
            round(monthly_totals_all.get(month_key, 0), 2)
        )

    sorted_categories_all = sorted(
        category_totals_all.items(),
        key=lambda item: item[1],
        reverse=True
    )

    category_labels = [
        item[0] for item in sorted_categories_all
    ]
    category_values = [
        round(item[1], 2) for item in sorted_categories_all
    ]

    top_category = (
        sorted_categories_all[0][0]
        if sorted_categories_all else "No data"
    )

    month_expenses = [
        expense for expense in rows if (expense["date"] or "").startswith(selected_month)
    ]

    total = sum(float(expense["amount"]) for expense in month_expenses)
    largest_expense = max((float(expense["amount"]) for expense in month_expenses), default=0.0)

    daily_totals = {}
    category_totals = {}
    for expense in month_expenses:
        amount = float(expense["amount"])
        expense_date = expense["date"] or ""
        if expense_date:
            daily_totals[expense_date] = daily_totals.get(expense_date, 0.0) + amount

        category = expense["category"]
        category_totals[category] = category_totals.get(category, 0.0) + amount


    daily_average = total / len(daily_totals) if daily_totals else 0.0

    category_data = [
        {"category": category, "amount": amount}
        for category, amount in sorted(category_totals.items(), key=lambda item: item[1], reverse=True)
    ]
    max_category_amount = max((item["amount"] for item in category_data), default=0.0)

    budget_amount = get_budget_amount(user_id)
    remaining_budget = budget_amount - total
    burn_rate = (total / budget_amount) * 100 if budget_amount > 0 else 0.0
    burn_rate = min(max(burn_rate, 0), 100)
    
    expense_insights = generate_expense_insights(
        rows, budget_amount
    )


    monthly_totals = {}
    for expense in rows:
        try:
            expense_date = datetime.strptime(expense["date"], "%Y-%m-%d")
        except (TypeError, ValueError):
            continue

        month_key = expense_date.strftime("%Y-%m")
        month_label = expense_date.strftime("%B %Y")
        if month_key not in monthly_totals:
            monthly_totals[month_key] = {"label": month_label, "amount": 0.0}
        monthly_totals[month_key]["amount"] += float(expense["amount"])

    monthly_history = []
    for month_key, data in sorted(monthly_totals.items(), reverse=True)[:6]:
        spent = data["amount"]
        month_remaining = budget_amount - spent
        month_percentage = (spent / budget_amount) * 100 if budget_amount > 0 else 0.0
        month_percentage = min(max(month_percentage, 0), 100)
        monthly_history.append(
            {
                "key": month_key,
                "label": data["label"],
                "budget": budget_amount,
                "spent": spent,
                "remaining": month_remaining,
                "percentage": month_percentage,
            }
        )

    max_monthly_amount = max((item["spent"] for item in monthly_history), default=0.0)

   
    return render_template(
        "reports.html",
        selected_month=selected_month,
        total=total,
        daily_average=daily_average,
        largest_expense=largest_expense,
        category_data=category_data,
        monthly_history=monthly_history,
        max_category_amount=max_category_amount,
        max_monthly_amount=max_monthly_amount,
        budget=budget_amount,
        remaining_budget=remaining_budget,
        burn_rate=burn_rate,
        expense_insights=expense_insights,

        # Analytics variables
        total_spending=round(total_spending, 2),
        month_spending=round(month_spending, 2),
        expense_count=expense_count,
        top_category=top_category,
        month_labels=month_labels,
        month_values=month_values,
        category_labels=category_labels,
        category_values=category_values,
        recent_expenses=recent_expenses,
    )



from collections import defaultdict
from datetime import datetime


def generate_expense_insights(expenses, budget):
    """Generate rule-based insights without any external API."""

    insights = []

    now = datetime.now()
    current_month = now.strftime("%Y-%m")

    previous_month_date = now.replace(day=1)
    previous_month_date = (
        previous_month_date.replace(
            day=1
        )
    )

    if previous_month_date.month == 1:
        previous_month = f"{previous_month_date.year - 1}-12"
    else:
        previous_month = (
            f"{previous_month_date.year}-"
            f"{previous_month_date.month - 1:02d}"
        )

    category_totals = defaultdict(float)
    current_total = 0.0
    previous_total = 0.0

    for expense in expenses:
        raw_date = expense["date"] or ""

        try:
            expense_date = datetime.strptime(
                raw_date[:10], "%Y-%m-%d"
            )
        except (ValueError, TypeError):
            continue

        amount = float(expense["amount"] or 0)
        category = expense["category"] or "Other"

        if expense_date.strftime("%Y-%m") == current_month:
            current_total += amount
            category_totals[category] += amount

        elif expense_date.strftime("%Y-%m") == previous_month:
            previous_total += amount

    if category_totals:
        top_category = max(
            category_totals,
            key=category_totals.get
        )
        insights.append(
            f"Highest spending category this month: "
            f"{top_category} (₹{category_totals[top_category]:,.2f})."
        )
    else:
        insights.append(
            "No expenses recorded for the current month yet."
        )

    if previous_total > 0:
        change = (
            (current_total - previous_total)
            / previous_total
        ) * 100

        if change > 0:
            insights.append(
                f"Spending is {change:.1f}% higher than last month."
            )
        elif change < 0:
            insights.append(
                f"Spending is {abs(change):.1f}% lower than last month."
            )
        else:
            insights.append(
                "Spending is unchanged compared with last month."
            )
    elif current_total > 0:
        insights.append(
            "There is current-month spending but no previous-month "
            "spending to compare."
        )

    if budget > 0:
        percentage = (current_total / budget) * 100

        if percentage >= 100:
            insights.append(
                f"Budget exceeded! Current-month spending is "
                f"{percentage:.1f}% of your budget."
            )
        elif percentage >= 80:
            insights.append(
                f"Budget warning: {percentage:.1f}% of your "
                f"budget has been used."
            )
        else:
            insights.append(
                f"You have used {percentage:.1f}% of your budget."
            )
    else:
        insights.append(
            "Set a monthly budget to enable budget insights."
        )

    return insights



# =========================================================
# START APPLICATION
# =========================================================

init_db()


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
