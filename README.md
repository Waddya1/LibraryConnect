# LibraryConnect

**Library Due-Date Tracking and Email Reminder Application**

## Project Overview

LibraryConnect is a web application designed to help library patrons keep track of borrowed materials and remember when items are due.

Patrons can manually enter information about their borrowed books, view upcoming due dates, and receive automated email reminders. The application is designed as an independent system that could potentially be integrated with a library's integrated library system (ILS) in the future.

This project was developed as an individual CIT Capstone Project.

## Features

- Patron registration and login
- Add and manage borrowed books
- Edit book information and mark items as returned
- Save book records using SQLite
- Dashboard with color-coded due-date statuses
- Automated email reminders:
  - Three days before the due date
  - On the due date
  - One day after the due date
- Prevention of duplicate reminder emails
- Gmail SMTP integration for email delivery
- Windows Task Scheduler support for daily reminder processing
- Dry-run mode for testing reminders without sending emails

## Technologies Used

- **Python** — Application programming and reminder processing
- **Flask** — Web application framework
- **SQLite** — Database for patron accounts, books, and reminder history
- **HTML and CSS** — User interface
- **Gmail SMTP** — Email delivery
- **Windows Task Scheduler** — Automatic daily reminder execution
- **Windows Credential Manager** — Secure storage of the Gmail app password

## Installation and Setup

### Requirements

- Python 3
- Windows
- Visual Studio Code or another code editor
- Internet connection for sending email reminders

### 1. Set up the virtual environment

Open the project folder in VS Code and use the PowerShell terminal.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Initialize the database

From the folder containing `app.py`, run:

```powershell
flask --app app init-db
```

### 4. Start the application

```powershell
flask --app app run --debug
```

Open the application in your browser:

http://127.0.0.1:5000

## Using LibraryConnect

1. Register a patron account or log in.
2. Add a borrowed book, including its title, library, and due date.
3. View borrowed books and their due-date statuses on the dashboard.
4. Edit book information when necessary.
5. Mark a book as returned when it has been returned to the library.

Book records are stored in the database and remain available after logging out.

## Email Reminder System

LibraryConnect checks book due dates and determines whether reminders are needed.

Reminders are generated three days before the due date, on the due date, and one day after the due date.

The application records successfully sent reminders to prevent duplicate emails for the same book and reminder type.

### Preview reminders

```powershell
python send_reminders.py --dry-run
```

This previews reminders without sending emails or recording them as sent.

### Preview reminders for a specific date

```powershell
python send_reminders.py --dry-run --today 2026-10-22
```

### Send live reminders

```powershell
python send_reminders.py
```

Live delivery requires SMTP configuration and valid email credentials.

The application can retrieve the Gmail app password from Windows Credential Manager. Passwords should not be stored in source code or uploaded to GitHub.

Demo addresses ending in `@example.com` are excluded from live email delivery.

## Automatic Reminder Scheduling

LibraryConnect includes `run_reminders.bat`, which can be configured in Windows Task Scheduler.

The scheduled task runs the reminder script once per day. During development, the task was configured to run at 9:00 AM.

Because the current scheduler runs locally on Windows, the computer must be available for scheduled execution.

## Running Automated Tests

From the folder containing `app.py`, run:

```powershell
python -m unittest discover -s tests -t .
```

The automated tests cover application functionality and reminder-related logic.

Additional manual testing included:

- Registering and logging into patron accounts
- Confirming book records persist after logging out
- Checking due-date calculations
- Previewing reminders without sending emails
- Successfully delivering test emails through Gmail
- Running the reminder script through Windows Task Scheduler
- Confirming demo email addresses are skipped during live processing

## Project Limitations and Future Improvements

LibraryConnect currently requires patrons to enter borrowed book information manually. It does not connect directly to a library's circulation database.

Potential future improvements include:

- Integration with the Sierra integrated library system
- Automatic importing of checked-out materials
- Text message reminders
- Deployment to a web hosting service
- Additional notification preferences

## Project Status

The core application, database, due-date tracking, email delivery, and reminder scheduling components have been implemented and tested.

LibraryConnect was developed as an individual CIT Capstone Project.