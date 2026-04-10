#!/usr/bin/env python3
"""
Run this script locally to generate your bcrypt password hash.
Paste the output into your HuggingFace Space Secrets as PASSWORD_HASH.

Usage:
    python generate_password_hash.py
"""
import getpass

try:
    import bcrypt
except ImportError:
    print("Installing bcrypt...")
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "bcrypt"])
    import bcrypt

password = getpass.getpass("Enter password for 'arko': ")
confirm  = getpass.getpass("Confirm password: ")

if password != confirm:
    print("Passwords do not match.")
    exit(1)

hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

print("\nYour PASSWORD_HASH:")
print(hashed)
print("\nPaste this value into HuggingFace Space Secrets as PASSWORD_HASH")
