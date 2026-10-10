# ExpenseTracker Pro

A Flask application for tracking expenses and budgets.

## Run locally

1. Install Flask:

   ```powershell
   py -m pip install Flask
   ```

2. Set a secret key for the current PowerShell session:

   ```powershell
   $env:FLASK_SECRET_KEY = py -c "import secrets; print(secrets.token_hex(32))"
   ```

3. Start the app:

   ```powershell
   py app.py
   ```

The app creates `expenses.db` in the project directory. The database and local
Python cache files are excluded from Git.
