"""Due-date math shared by the dashboard and the reminder service.
Every function receives 'today' as an argument, which makes it easy to test."""
from datetime import datetime, timedelta

SOON_DAYS = 3   # "due soon" means 1 to 3 days left

# How many days are left until the due date when each reminder should go out.
REMINDER_RULES = {
    "before_3": 3,     # 3 days before the due date
    "due_today": 0,    # on the due date
    "overdue_1": -1,   # 1 day after the due date
}


def parse_due_date(due_date_text):
    return datetime.strptime(due_date_text, "%Y-%m-%d").date()


def days_until_due(due_date_text, today):
    """Positive = days left, 0 = due today, negative = days overdue."""
    return (parse_due_date(due_date_text) - today).days


def _days(number):
    return f"{number} day" + ("" if number == 1 else "s")


def get_status(due_date_text, today):
    """Returns a dict: key, label, color, days."""
    days = days_until_due(due_date_text, today)
    if days < 0:
        key, color, label = "overdue", "red", f"Overdue by {_days(-days)}"
    elif days == 0:
        key, color, label = "due_today", "yellow", "DUE TODAY"
    elif days <= SOON_DAYS:
        key, color, label = "due_soon", "yellow", f"Due in {_days(days)}"
    else:
        key, color, label = "on_track", "green", f"{days} days left"
    return {"key": key, "label": label, "color": color, "days": days}


def reminder_due_date(reminder_type, today):
    """The due date that triggers this reminder type today.
    Example: for 'before_3', books due 3 days from today."""
    return today + timedelta(days=REMINDER_RULES[reminder_type])
