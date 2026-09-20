import os

DATABASE_URL = os.environ["DATABASE_URL"]

ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")

MAX_UPLOAD_BYTES = int(os.environ.get("MAX_UPLOAD_BYTES", 50 * 1024 * 1024))  # 50 MB
