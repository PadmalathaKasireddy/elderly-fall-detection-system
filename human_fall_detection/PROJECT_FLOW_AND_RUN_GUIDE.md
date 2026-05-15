# Fall Surveillance Project Guide

## 1. Project Overview

This project is an elderly fall detection web application built with:

- Flask
- YOLO
- MediaPipe
- OpenCV
- PostgreSQL

The project now has:

- Dynamic `login`
- Dynamic `register`
- Role-based portal flow
- Fall detection portal
- Caregiver / medical portal UI
- PostgreSQL schema for users, fall events, and notification records

Important:

- Fall detection functionality was kept as-is.
- Login and register are now backend-driven through PostgreSQL.
- The notification database structure is ready, even if full alert delivery logic is not yet wired.

---

## 2. Main Files

- [`final1.py`](/c:/Users/harip/Music/human_fall/final1.py)
  Main app file you should run.

- [`schema.sql`](/c:/Users/harip/Music/human_fall/schema.sql)
  PostgreSQL schema file. Load this manually into your database.

- [`auth_db.py`](/c:/Users/harip/Music/human_fall/auth_db.py)
  Database helper for login/register.

- [`templates/`](/c:/Users/harip/Music/human_fall/templates)
  UI pages.

- [`static/styles.css`](/c:/Users/harip/Music/human_fall/static/styles.css)
  Shared styling.

---

## 3. Full Project Flow

### Entry Flow

When the app starts:

1. User opens the project in browser.
2. `/` redirects to `/login`.
3. User can:
   - log in
   - or go to register page

### Register Flow

1. User opens `/register`
2. User enters:
   - full name
   - email
   - phone number
   - role
   - password
   - confirm password
3. Data is stored in PostgreSQL table `app_users`
4. Password is stored as hashed password
5. User is redirected to login page

### Login Flow

1. User opens `/login`
2. User enters:
   - email
   - password
3. App checks PostgreSQL `app_users`
4. If credentials are correct:
   - session is created
   - `last_login_at` is updated
   - user is redirected based on role

### Role Redirect Flow

- `caregiver` -> caregiver portal
- `medical_personnel` -> caregiver portal
- `detection_operator` -> detection portal

### Caregiver / Medical Portal Flow

Portal page:

- shows signed-in user
- shows alert/response oriented UI
- is designed for future notification viewing

This portal is intended for:

- caregivers
- medical personnel

### Detection Operator Portal Flow

Portal page:

- shows signed-in user
- gives access to:
  - live stream detection
  - upload video detection

This portal is intended for the person operating the detection system.

### Fall Detection Flow

From detection portal:

1. User opens live stream mode or upload mode
2. Existing YOLO + MediaPipe logic runs
3. Fall is detected visually in the stream
4. Current functionality remains unchanged

### Database Notification Flow

Schema already supports:

- `fall_events`
- `notification_deliveries`

This means future logic can store:

- which fall occurred
- who detected it
- which caregiver / medical user should be notified
- notification status

---

## 4. PostgreSQL Tables Explained

### `app_users`

Stores:

- user identity
- role
- password hash
- active status
- timestamps

### `fall_events`

Stores:

- fall event details
- detection source
- event status
- confidence score

### `notification_deliveries`

Stores:

- recipient user
- related fall event
- delivery channel
- delivery status

---

## 5. How To Load Database Schema

You said you want to load PostgreSQL manually. Use this file:

- [`schema.sql`](/c:/Users/harip/Music/human_fall/schema.sql)

### Option 1: pgAdmin

1. Open pgAdmin
2. Select your database
3. Open Query Tool
4. Paste contents of `schema.sql`
5. Execute

### Option 2: psql

```powershell
psql -U your_user -d your_database -f schema.sql
```

---

## 6. Database Environment Variables

Before running the app, set PostgreSQL environment variables in PowerShell.

Example:

```powershell
$env:PGHOST="localhost"
$env:PGPORT="5432"
$env:PGDATABASE="human_fall"
$env:PGUSER="postgres"
$env:PGPASSWORD="your_password"
```

Optional:

```powershell
$env:FLASK_SECRET_KEY="your_secret_key"
```

You can also use:

```powershell
$env:DATABASE_URL="postgresql://postgres:your_password@localhost:5432/human_fall"
```

If `DATABASE_URL` is set, it will be used directly.

---

## 7. How To Run The Project

Open PowerShell in:

```powershell
cd C:\Users\harip\Music\human_fall
```

Then run:

```powershell
python .\final1.py
```

If everything is correct, you should see something like:

```text
* Running on http://127.0.0.1:5000
```

Open:

```text
http://127.0.0.1:5000
```

---

## 8. Full Run Order

Use this order every time:

1. Open PostgreSQL
2. Make sure your database exists
3. Load `schema.sql` if not loaded already
4. Set environment variables
5. Open project folder in PowerShell
6. Run `python .\final1.py`
7. Open browser
8. Go to `http://127.0.0.1:5000`
9. Register a user
10. Login
11. Open role-based portal
12. Use detection portal for live/upload fall detection

---

## 9. Example Test Users

When registering, use roles exactly like these through UI:

- Caregiver
- Medical Personnel
- Detection Operator

App internally maps them to:

- `caregiver`
- `medical_personnel`
- `detection_operator`

---

## 10. Common Problems

### Problem: Login/Register says database not configured

Reason:

- PostgreSQL env vars are not set

Fix:

- set `PGHOST`, `PGDATABASE`, `PGUSER`, `PGPASSWORD`
- or set `DATABASE_URL`

### Problem: Table does not exist

Reason:

- `schema.sql` was not loaded

Fix:

- run `schema.sql` manually in PostgreSQL

### Problem: Login fails

Reason:

- wrong email/password
- or account was not created

Fix:

- register first
- then login

### Problem: App opens but auth pages not saving

Reason:

- database connection issue

Fix:

- verify PostgreSQL is running
- verify credentials
- verify schema loaded

---

## 11. Current Functional Scope

Working now:

- login UI
- register UI
- PostgreSQL-based auth
- session-based role redirect
- caregiver portal page
- detection portal page
- live stream detection
- upload video detection

Prepared for future:

- fall event storage
- notification delivery storage
- caregiver alert timeline
- medical escalation flow

Not fully implemented yet:

- real SMS/email notifications
- automatic DB insert when fall is detected
- full role authorization restrictions across every route

---

## 12. Recommended Daily Usage Flow

For your current project demo, best flow is:

1. Load database
2. Start app
3. Register one caregiver user
4. Register one detection operator user
5. Login as detection operator
6. Open detection portal
7. Start live stream or upload detection
8. Login as caregiver in another session if needed
9. Show caregiver portal as alert-receiver side

---

## 13. Final Note

If you keep using this project as the main file, use:

- [`final1.py`](/c:/Users/harip/Music/human_fall/final1.py)

This is the correct file to run right now.
