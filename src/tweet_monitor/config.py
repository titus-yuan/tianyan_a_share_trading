"""Configuration from .env file and defaults."""

import os
from pathlib import Path

# Load .env from project root
_ENV_PATH = Path(__file__).parent.parent.parent / ".env"
if _ENV_PATH.exists():
    with open(_ENV_PATH) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                if key not in os.environ:
                    os.environ[key] = val

# Bot PC PostgreSQL (for monitor SSH access)
BOT_PC_HOST = os.getenv("BOT_PC_HOST", "192.168.169.30")
BOT_PC_USER = os.getenv("BOT_PC_USER", "titus")
BOT_PC_DB = os.getenv("BOT_PC_DB", "media_x_monitor")
BOT_PC_DB_USER = os.getenv("BOT_PC_DB_USER", "titus")

# Local PostgreSQL (for web app on Bot PC)
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "media_x_monitor")
DB_USER = os.getenv("DB_USER", "titus")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

# SSH (use key-based auth — no password needed)
SSH_KEY = os.path.expanduser("~/.ssh/id_rsa")

# Nitter
NITTER_UA = os.getenv(
    "NITTER_USER_AGENT",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36",
)
NITTER_PRIMARY = os.getenv("NITTER_PRIMARY", "https://nitter.net")
NITTER_TIMEOUT = int(os.getenv("NITTER_TIMEOUT", "12"))

# Monitoring
TRADING_INTERVAL = int(os.getenv("MONITOR_INTERVAL_TRADING", "1800"))
NONTRADING_INTERVAL = int(os.getenv("MONITOR_INTERVAL_NONTRADING", "3600"))

# Monitoring targets (comma-separated usernames)
MONITOR_USERS = os.getenv("MONITOR_USERS", "STOCK6688")

# Trading hours in CST (UTC+8)
TRADING_START = 9  # 9:00
TRADING_END = 15   # 15:00
