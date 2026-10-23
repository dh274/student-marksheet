# Student Lost Marksheet Assistance Portal

A Flask assistance portal for students preparing to ask their university about a
duplicate marksheet. It is not an official university website and does not submit
requests to a university or issue marksheets.

## Current features

- Student registration and sign-in with securely hashed passwords.
- CSRF-protected registration, sign-in, application, logout, and status forms.
- Private application records stored in SQLite.
- A student tracker that only returns and updates the signed-in student's records.
- A separately authenticated admin view; admin credentials are supplied through
  environment variables and are not stored in the database.
- Input validation, parameterized database queries, and a restrictive file ignore list.
- Clear warnings that checklist guidance is not an official verified university
  requirement and tracker statuses are student-maintained.

The document checklist and letter pages are general preparation guidance only. They
do not assert current Anna University fees, procedures, addresses, or document
requirements. Confirm all details directly with the university or college.

## Project structure

```text
student-marksheet-portal/
|-- app.py
|-- forms.py
|-- schema.sql
|-- requirements.txt
|-- templates/
|-- static/
|   `-- css/
|       `-- style.css
`-- tests/
    `-- test_app.py
```

## Run locally in VS Code (PowerShell)

1. Open the project folder in VS Code and open **Terminal > New Terminal**.
2. Create and activate a virtual environment:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   If PowerShell blocks activation, run this in that terminal and activate again:

   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   ```

3. Install dependencies and set a temporary development secret:

   ```powershell
   python -m pip install -r requirements.txt
   $env:SECRET_KEY = python -c "import secrets; print(secrets.token_hex(32))"
   ```

4. Start Flask:

   ```powershell
   python app.py
   ```

5. Open <http://127.0.0.1:5000>. Keep the same terminal open while using the app.
   Stop the server with **Ctrl+C**.

The database is created automatically at `instance/applications.sqlite3`. Do not
put real student data in test environments or commit this file.

## Configure local admin access

Admin access is disabled until both settings are provided. Generate a password hash
without saving the admin password in the project:

```powershell
$env:ADMIN_USERNAME = "portal-admin"
$env:ADMIN_PASSWORD_HASH = python -c "from getpass import getpass; from werkzeug.security import generate_password_hash; print(generate_password_hash(getpass('Admin password: ')))"
```

Start the app in that same terminal, then visit
<http://127.0.0.1:5000/admin/login>. Use the configured username and the password
used to generate the hash.

## Environment variables

| Variable | Purpose |
| --- | --- |
| `SECRET_KEY` | Required random key used to sign sessions and CSRF tokens. Keep it private and stable. |
| `DATABASE_PATH` | Optional SQLite file path. Defaults to `instance/applications.sqlite3`. |
| `ADMIN_USERNAME` | Optional admin login name. Without admin configuration, the admin route returns unavailable. |
| `ADMIN_PASSWORD_HASH` | Optional Werkzeug password hash for the admin password; never use a plaintext password here. |
| `APP_ENV` | Set to `production` in production; enables secure-only session cookies and disables debug mode. |
| `FLASK_DEBUG` | Set to `1` only for local development. Debug remains off when `APP_ENV=production`. |

Generate a production `SECRET_KEY` with:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

Set secrets in the hosting provider's environment-variable dashboard. Do not commit
them, place them in source files, or share them publicly.

## Run tests

```powershell
python -m unittest discover -s tests -v
```

The tests cover public/private route access, SQLite persistence, student ownership,
status updates, admin authentication, and CSRF rejection.

## Data and deployment status

SQLite files and `.env` files are excluded by `.gitignore`. On hosts with temporary
filesystem storage, SQLite data can disappear on restart or redeploy. Production
deployment must use a persistent disk mounted at the configured `DATABASE_PATH` or a
managed database, and must set the secret/admin variables in the host dashboard.

This project has not yet been configured or deployed to Render. Before publishing,
complete and verify the production server configuration, dependency list, persistent
storage plan, secrets setup, and GitHub exclusion check. Do not deploy real student
records to a temporary database.
