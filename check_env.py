#!/usr/bin/env python3
"""
Check .env file for required variables and validate setup.
"""

import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

# Color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def check_var(name, required=True, description=""):
    """Check if an environment variable is set"""
    value = os.getenv(name)
    if value:
        # Mask sensitive values
        if 'SECRET' in name or 'TOKEN' in name or 'KEY' in name:
            display_value = f"{value[:10]}...{value[-4:]}" if len(value) > 14 else "***"
        else:
            display_value = value
        
        print(f"{GREEN}✓{RESET} {name:30} = {display_value}")
        return True
    else:
        if required:
            print(f"{RED}✗{RESET} {name:30} = MISSING (REQUIRED)")
        else:
            print(f"{YELLOW}○{RESET} {name:30} = Not set (optional)")
        return False

print(f"\n{BLUE}{'='*60}{RESET}")
print(f"{BLUE}Checking .env File Configuration{RESET}")
print(f"{BLUE}{'='*60}{RESET}\n")

# Check if .env file exists
env_path = Path('.env')
if not env_path.exists():
    print(f"{RED}✗{RESET} .env file not found!")
    print(f"\n{YELLOW}Create one by copying env.example:{RESET}")
    print("  cp env.example .env")
    print("  # Then edit .env with your values")
    exit(1)

print(f"{GREEN}✓{RESET} .env file found\n")

# Required variables
print(f"{BLUE}Required Variables:{RESET}")
print("-" * 60)

required_vars = [
    ("TICKTICK_CLIENT_ID", True, "OAuth Client ID from TickTick Developer Console"),
    ("TICKTICK_CLIENT_SECRET", True, "OAuth Client Secret from TickTick Developer Console"),
    ("TICKTICK_ACCESS_TOKEN", True, "Access token from OAuth flow (run get_tokens.py)"),
    ("TICKTICK_REFRESH_TOKEN", True, "Refresh token from OAuth flow (run get_tokens.py)"),
]

all_required = True
for var_name, required, desc in required_vars:
    if not check_var(var_name, required, desc):
        all_required = False

# Optional but recommended
print(f"\n{BLUE}Optional but Recommended:{RESET}")
print("-" * 60)

optional_vars = [
    ("MCP_API_KEY", False, "API key for server authentication (recommended for security)"),
]

for var_name, required, desc in optional_vars:
    check_var(var_name, required, desc)

# Optional configuration
print(f"\n{BLUE}Optional Configuration:{RESET}")
print("-" * 60)

config_vars = [
    ("TICKTICK_BASE_URL", False, "API base URL (default: https://api.ticktick.com/open/v1)"),
    ("TICKTICK_TOKEN_URL", False, "Token endpoint URL (default: https://ticktick.com/oauth/token)"),
    ("PORT", False, "Server port (default: 8000)"),
    ("HOST", False, "Server host (default: 0.0.0.0)"),
    ("TICKTICK_RATE_LIMIT_DELAY", False, "Rate limit delay in seconds (default: 0.2)"),
]

for var_name, required, desc in config_vars:
    check_var(var_name, required, desc)

# Summary
print(f"\n{BLUE}{'='*60}{RESET}")
if all_required:
    print(f"{GREEN}✓ All required variables are set!{RESET}")
    print(f"\n{BLUE}Next steps:{RESET}")
    print("1. If you don't have ACCESS_TOKEN and REFRESH_TOKEN yet:")
    print("   python get_tokens.py")
    print("\n2. Test the server:")
    print("   python main.py")
    print("\n3. In another terminal, test it:")
    print("   python test_server.py")
else:
    print(f"{RED}✗ Some required variables are missing!{RESET}")
    print(f"\n{YELLOW}To fix:{RESET}")
    
    if not os.getenv("TICKTICK_CLIENT_ID") or not os.getenv("TICKTICK_CLIENT_SECRET"):
        print("1. Get Client ID and Secret from: https://developer.ticktick.com/manage")
        print("   Add them to your .env file")
    
    if not os.getenv("TICKTICK_ACCESS_TOKEN") or not os.getenv("TICKTICK_REFRESH_TOKEN"):
        print("2. Run the token generator:")
        print("   python get_tokens.py")
        print("   (This requires CLIENT_ID and CLIENT_SECRET to be set first)")

print(f"{BLUE}{'='*60}{RESET}\n")

