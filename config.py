"""Settings for LibraryConnect."""
import os
import secrets
from datetime import timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"


def load_secret_key():
    """Use the LIBRARYCONNECT_SECRET_KEY environment variable if set.
    Otherwise create a random key once and save it in instance/secret_key.txt
    (the instance folder is ignored by Git, so the key is never uploaded)."""
    env_key = os.environ.get("LIBRARYCONNECT_SECRET_KEY")
    if env_key:
        return env_key
    INSTANCE_DIR.mkdir(exist_ok=True)
    key_file = INSTANCE_DIR / "secret_key.txt"
    if not key_file.exists():
        key_file.write_text(secrets.token_hex(32))
    return key_file.read_text().strip()


class Config:
    DATABASE = str(INSTANCE_DIR / "libraryconnect.sqlite")
    SESSION_COOKIE_HTTPONLY = True        # JavaScript cannot read the cookie
    SESSION_COOKIE_SAMESITE = "Lax"       # helps block cross-site requests
    SESSION_COOKIE_SECURE = False         # set True once the site uses HTTPS
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    MAX_CONTENT_LENGTH = 16 * 1024        # reject huge form submissions
