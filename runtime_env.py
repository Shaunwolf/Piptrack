"""Where the app is running, and where it may write files.

Serverless hosts such as Vercel have a read-only filesystem apart from /tmp, and no
long-running process, so caches, the SQLite fallback and background threads adapt here.
"""

import os

ON_VERCEL = bool(os.environ.get("VERCEL"))
# Directory for caches and other runtime files (override with APP_WRITABLE_DIR)
WRITABLE_DIR = os.environ.get("APP_WRITABLE_DIR") or ("/tmp" if ON_VERCEL else ".")


def database_url() -> str:
    """DATABASE_URL (or Vercel Postgres/Neon's POSTGRES_URL); otherwise a local SQLite file"""
    url = os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL")
    if not url:
        return f"sqlite:///{os.path.join(WRITABLE_DIR, 'pipsqueak.db')}" if ON_VERCEL else "sqlite:///pipsqueak.db"
    # SQLAlchemy 2 only accepts the postgresql:// scheme
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    return url


def background_threads_allowed() -> bool:
    return os.environ.get("DISABLE_BACKGROUND_SCANNER") != "1" and not ON_VERCEL
