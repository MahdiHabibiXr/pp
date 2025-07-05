# mk_scaffold.py
import os
from pathlib import Path

# 1) Root of your project
BASE_DIR = Path(r"C:\Users\Mahdi\Desktop\PPbot")

# 2) All directories to provision
DIRS = [
    BASE_DIR,
    BASE_DIR / "src",
    BASE_DIR / "src" / "handlers",
    BASE_DIR / "src" / "models",
    BASE_DIR / "src" / "services",
    BASE_DIR / "src" / "webhooks",
]

# 3) All files to touch (empty stubs)
FILES = [
    "README.md",
    "requirements.txt",
    "Dockerfile",
    ".env.example",
    "src/main.py",
    "src/config.py",
    "src/database.py",
    "src/bot.py",
    "src/handlers/commands.py",
    "src/handlers/messages.py",
    "src/handlers/callbacks.py",
    "src/models/user.py",
    "src/models/generation.py",
    "src/models/payment.py",
    "src/services/tapsage_client.py",
    "src/services/replicate_client.py",
    "src/services/pixy_storage.py",
    "src/services/zarinpal_client.py",
    "src/webhooks/replicate_webhook.py",
]

def make_structure():
    # Create directories
    for d in DIRS:
        d.mkdir(parents=True, exist_ok=True)
    # Touch files
    for f in FILES:
        (BASE_DIR / f).touch(exist_ok=True)
    print(f"Scaffold created at {BASE_DIR}")

if __name__ == "__main__":
    make_structure()
