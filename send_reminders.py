"""LibraryConnect reminder service (run by hand or by Windows Task Scheduler).

  python send_reminders.py                      send today's reminders for real
  python send_reminders.py --dry-run            preview only: nothing is sent or recorded
  python send_reminders.py --dry-run --today 2026-10-20
                                                preview as if today were that date
"""
import argparse
import os
import sqlite3
import sys
from datetime import date, datetime

import emailer
import reminders
from app import app
from db import get_db


def main():
    parser = argparse.ArgumentParser(description="Send LibraryConnect due-date reminders.")
    parser.add_argument("--dry-run", action="store_true",
                        help="preview the emails without sending or recording anything")
    parser.add_argument("--today", help="pretend today is this date (YYYY-MM-DD); needs --dry-run")
    args = parser.parse_args()

    if args.today:
        if not args.dry_run:
            parser.error("--today can only be used with --dry-run, "
                         "so pretend dates never send real emails")
        try:
            today = datetime.strptime(args.today, "%Y-%m-%d").date()
        except ValueError:
            parser.error("--today must look like 2026-10-20")
    else:
        today = date.today()

    if not os.path.exists(app.config["DATABASE"]):
        print("Database not found. Run:  flask --app app init-db")
        sys.exit(1)

    send_function = None
    if not args.dry_run:
        try:
            settings = emailer.load_email_settings()
        except emailer.EmailConfigError as error:
            print(f"Cannot send emails: {error}")
            print("Set the variables (see README) or use --dry-run to preview.")
            sys.exit(1)

        def send_function(to_address, subject, body):
            emailer.send_email(settings, to_address, subject, body)

    mode = "DRY RUN" if args.dry_run else "LIVE"
    print(f"LibraryConnect reminder run for {today} ({mode})")

    with app.app_context():
        try:
            summary = reminders.process_reminders(get_db(), today, send_function, args.dry_run)
        except sqlite3.OperationalError as error:
            print(f"Database problem: {error}")
            print("Try running:  flask --app app init-db")
            sys.exit(1)

    print(f"Done. found={summary['found']} sent={summary['sent']} "
          f"previewed={summary['previewed']} failed={summary['failed']}")
    if summary["failed"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
