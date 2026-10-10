import sqlite3


# =========================================================
# DATABASE CONNECTION
# =========================================================

DB_NAME = "expenses.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


# =========================================================
# PRINT LINE
# =========================================================

def print_line(length=100):
    print("-" * length)


# =========================================================
# SHOW USERS
# =========================================================

def show_users(conn):

    print("\n")
    print("=" * 100)
    print("USERS TABLE")
    print("=" * 100)

    rows = conn.execute("""
        SELECT
            id,
            name,
            email,
            password
        FROM users
        ORDER BY id ASC
    """).fetchall()

    if not rows:
        print("No users found.")
        return

    print(f"Total Users: {len(rows)}")
    print_line()

    print(
        f"{'ID':<5}"
        f"{'NAME':<20}"
        f"{'EMAIL':<32}"
        f"{'PASSWORD':<25}"
    )

    print_line()

    for row in rows:

        # Password ko screen par expose nahi karenge
        password = "[HASHED]" if row["password"] else "[EMPTY]"

        print(
            f"{row['id']:<5}"
            f"{row['name'][:18]:<20}"
            f"{row['email'][:30]:<32}"
            f"{password:<25}"
        )

    print_line()


# =========================================================
# SHOW EXPENSES
# =========================================================

def show_expenses(conn):

    print("\n")
    print("=" * 100)
    print("EXPENSES TABLE")
    print("=" * 100)

    rows = conn.execute("""
        SELECT
            id,
            user_id,
            date,
            category,
            description,
            notes,
            amount
        FROM expenses
        ORDER BY id ASC
    """).fetchall()

    if not rows:
        print("No expenses found.")
        return

    print(f"Total Expenses: {len(rows)}")
    print_line(120)

    print(
        f"{'ID':<5}"
        f"{'USER':<7}"
        f"{'DATE':<13}"
        f"{'CATEGORY':<15}"
        f"{'DESCRIPTION':<25}"
        f"{'NOTES':<25}"
        f"{'AMOUNT':>10}"
    )

    print_line(120)

    for row in rows:

        description = row["description"] or ""
        notes = row["notes"] or ""

        print(
            f"{row['id']:<5}"
            f"{str(row['user_id']):<7}"
            f"{str(row['date']):<13}"
            f"{str(row['category'])[:13]:<15}"
            f"{description[:23]:<25}"
            f"{notes[:23]:<25}"
            f"{float(row['amount']):>10.2f}"
        )

    print_line(120)


# =========================================================
# SHOW BUDGET
# =========================================================

def show_budget(conn):

    print("\n")
    print("=" * 100)
    print("BUDGET TABLE")
    print("=" * 100)

    rows = conn.execute("""
        SELECT
            user_id,
            amount
        FROM budget
        ORDER BY user_id ASC
    """).fetchall()

    if not rows:
        print("No budget records found.")
        return

    print(f"Total Budget Records: {len(rows)}")
    print_line()

    print(
        f"{'USER ID':<12}"
        f"{'BUDGET AMOUNT':>20}"
    )

    print_line()

    for row in rows:

        print(
            f"{row['user_id']:<12}"
            f"{float(row['amount']):>20.2f}"
        )

    print_line()


# =========================================================
# SHOW TABLE INFORMATION
# =========================================================

def show_table_info(conn):

    print("\n")
    print("=" * 100)
    print("DATABASE TABLES")
    print("=" * 100)

    tables = conn.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        AND name NOT LIKE 'sqlite_%'
        ORDER BY name
    """).fetchall()

    if not tables:
        print("No tables found.")
        return

    for table in tables:

        table_name = table["name"]

        print(f"\nTable: {table_name}")

        columns = conn.execute(
            f"PRAGMA table_info({table_name})"
        ).fetchall()

        for column in columns:

            print(
                f"   {column['name']:<15}"
                f" Type: {column['type']}"
            )

    print_line()


# =========================================================
# DATABASE SUMMARY
# =========================================================

def show_summary(conn):

    print("\n")
    print("=" * 100)
    print("DATABASE SUMMARY")
    print("=" * 100)

    users_count = conn.execute(
        "SELECT COUNT(*) FROM users"
    ).fetchone()[0]

    expenses_count = conn.execute(
        "SELECT COUNT(*) FROM expenses"
    ).fetchone()[0]

    budget_count = conn.execute(
        "SELECT COUNT(*) FROM budget"
    ).fetchone()[0]

    total_expenses = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) FROM expenses"
    ).fetchone()[0]

    print(f"Users            : {users_count}")
    print(f"Expenses         : {expenses_count}")
    print(f"Budget Records   : {budget_count}")
    print(f"Total Expenses   : ₹{float(total_expenses):.2f}")

    print_line()


# =========================================================
# MAIN
# =========================================================

def main():

    try:

        conn = get_connection()

        print("\n")
        print("=" * 100)
        print("        EXPENSETRACKER PRO - DATABASE VIEWER")
        print("=" * 100)

        show_summary(conn)

        show_table_info(conn)

        show_users(conn)

        show_expenses(conn)

        show_budget(conn)

        conn.close()

        print("\nDatabase reading completed successfully.")
        print("=" * 100)

    except sqlite3.Error as error:

        print("\nDatabase Error:")
        print(error)

    except Exception as error:

        print("\nUnexpected Error:")
        print(error)


# =========================================================
# START PROGRAM
# =========================================================

if __name__ == "__main__":
    main()