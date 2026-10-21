"""Sends one email through an SMTP server (port 587 with STARTTLS).

Credentials are read from ENVIRONMENT VARIABLES, never from the code:
  LIBRARYCONNECT_SMTP_HOST       e.g. smtp.gmail.com
  LIBRARYCONNECT_SMTP_PORT       optional, default 587
  LIBRARYCONNECT_SMTP_USER       the login name for the mail account
  LIBRARYCONNECT_SMTP_PASSWORD   the password or app password
  LIBRARYCONNECT_SMTP_FROM       optional, defaults to the user name
"""
import os
import smtplib
import ssl
from email.message import EmailMessage

REQUIRED_VARIABLES = [
    "LIBRARYCONNECT_SMTP_HOST",
    "LIBRARYCONNECT_SMTP_USER",
    "LIBRARYCONNECT_SMTP_PASSWORD",
]


class EmailConfigError(Exception):
    pass


def load_email_settings():
    missing = [name for name in REQUIRED_VARIABLES if not os.environ.get(name)]
    if missing:
        raise EmailConfigError("missing environment variable(s): " + ", ".join(missing))
    try:
        port = int(os.environ.get("LIBRARYCONNECT_SMTP_PORT", "587"))
    except ValueError:
        raise EmailConfigError("LIBRARYCONNECT_SMTP_PORT must be a number")
    user = os.environ["LIBRARYCONNECT_SMTP_USER"]
    return {
        "host": os.environ["LIBRARYCONNECT_SMTP_HOST"],
        "port": port,
        "user": user,
        "password": os.environ["LIBRARYCONNECT_SMTP_PASSWORD"],
        "from_address": os.environ.get("LIBRARYCONNECT_SMTP_FROM") or user,
    }


def send_email(settings, to_address, subject, body):
    message = EmailMessage()
    message["From"] = f'LibraryConnect <{settings["from_address"]}>'
    message["To"] = to_address
    message["Subject"] = subject
    message.set_content(body)

    context = ssl.create_default_context()
    with smtplib.SMTP(settings["host"], settings["port"], timeout=30) as server:
        server.starttls(context=context)
        server.login(settings["user"], settings["password"])
        server.send_message(message)
