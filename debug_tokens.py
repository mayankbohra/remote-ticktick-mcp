#!/usr/bin/env python3
"""
Debug script to check what tokens are actually in the .env file
"""

import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

print("Checking .env file contents:\n")

env_path = Path('.env')
if not env_path.exists():
    print("❌ .env file not found")
    exit(1)

with open(env_path, 'r') as f:
    for line_num, line in enumerate(f, 1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        if '=' in line:
            key, value = line.split('=', 1)
            if 'TOKEN' in key or 'SECRET' in key or 'KEY' in key:
                # Show first and last few chars
                if len(value) > 20:
                    masked = f"{value[:10]}...{value[-4:]}"
                else:
                    masked = "***" if value and value != "your_refresh_token_here" else value
                print(f"Line {line_num}: {key:30} = {masked}")
            else:
                print(f"Line {line_num}: {key:30} = {value}")

print("\n" + "="*60)
print("Environment variables loaded:")
print("="*60)

access_token = os.getenv("TICKTICK_ACCESS_TOKEN")
refresh_token = os.getenv("TICKTICK_REFRESH_TOKEN")

if access_token:
    if access_token.startswith("your_") or access_token == "your_access_token_here":
        print("❌ TICKTICK_ACCESS_TOKEN is still a placeholder")
    else:
        print(f"✅ TICKTICK_ACCESS_TOKEN = {access_token[:15]}...{access_token[-4:]}")
else:
    print("❌ TICKTICK_ACCESS_TOKEN not set")

if refresh_token:
    if refresh_token.startswith("your_") or refresh_token == "your_refresh_token_here":
        print("❌ TICKTICK_REFRESH_TOKEN is still a placeholder")
    else:
        print(f"✅ TICKTICK_REFRESH_TOKEN = {refresh_token[:15]}...{refresh_token[-4:]}")
else:
    print("❌ TICKTICK_REFRESH_TOKEN not set")

