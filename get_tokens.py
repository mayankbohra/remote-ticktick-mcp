#!/usr/bin/env python3
"""
Helper script to get TickTick Access and Refresh Tokens via OAuth 2.0 flow.

This script performs the OAuth 2.0 authorization flow to obtain access and refresh tokens.
You need to have TICKTICK_CLIENT_ID and TICKTICK_CLIENT_SECRET in your .env file.
"""

import os
import sys
import base64
import requests
import webbrowser
import http.server
import socketserver
import urllib.parse
from threading import Event
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

CLIENT_ID = os.getenv("TICKTICK_CLIENT_ID")
CLIENT_SECRET = os.getenv("TICKTICK_CLIENT_SECRET")
BASE_URL = os.getenv("TICKTICK_BASE_URL", "https://api.ticktick.com/open/v1")
AUTH_URL = os.getenv("TICKTICK_AUTH_URL", "https://ticktick.com/oauth/authorize")
TOKEN_URL = os.getenv("TICKTICK_TOKEN_URL", "https://ticktick.com/oauth/token")
REDIRECT_URI = "http://localhost:8000/callback"
PORT = 8000

# Store the authorization code
auth_code = None
auth_code_received = Event()


class CallbackHandler(http.server.SimpleHTTPRequestHandler):
    """Handle OAuth callback"""
    
    def do_GET(self):
        """Handle GET request from OAuth redirect"""
        global auth_code
        
        # Parse the callback URL
        parsed = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed.query)
        
        if 'code' in query_params:
            auth_code = query_params['code'][0]
            auth_code_received.set()
            
            # Send success response
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"""
            <html>
            <head><title>Authorization Successful</title></head>
            <body>
                <h1>Authorization Successful!</h1>
                <p>You can close this window and return to the terminal.</p>
                <script>window.close();</script>
            </body>
            </html>
            """)
        elif 'error' in query_params:
            error = query_params['error'][0]
            error_description = query_params.get('error_description', ['Unknown error'])[0]
            
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(f"""
            <html>
            <head><title>Authorization Failed</title></head>
            <body>
                <h1>Authorization Failed</h1>
                <p>Error: {error}</p>
                <p>Description: {error_description}</p>
            </body>
            </html>
            """.encode())
            auth_code_received.set()
        else:
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"<html><body><h1>Invalid callback</h1></body></html>")
            auth_code_received.set()
    
    def log_message(self, format, *args):
        """Suppress server logs"""
        pass


def get_tokens():
    """Perform OAuth 2.0 flow to get access and refresh tokens"""
    
    if not CLIENT_ID or not CLIENT_SECRET:
        print("❌ Error: TICKTICK_CLIENT_ID and TICKTICK_CLIENT_SECRET must be set in .env file")
        print("\nPlease add them to your .env file:")
        print("TICKTICK_CLIENT_ID=your_client_id")
        print("TICKTICK_CLIENT_SECRET=your_client_secret")
        sys.exit(1)
    
    print("""
╔════════════════════════════════════════════════╗
║    TickTick OAuth Token Generator              ║
╚════════════════════════════════════════════════╝

This script will:
1. Open your browser for TickTick authorization
2. Start a local server to receive the callback
3. Exchange the authorization code for tokens
4. Save tokens to your .env file

Make sure your OAuth redirect URL in TickTick Developer Console is set to:
http://localhost:8000/callback

Press Enter to continue...
    """)
    input()
    
    # Step 1: Generate authorization URL
    # TickTick only supports: tasks:read and tasks:write
    auth_params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": "tasks:read tasks:write"
    }
    
    auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(auth_params)}"
    
    print(f"\n📋 Opening browser for authorization...")
    print(f"URL: {auth_url}\n")
    
    # Step 2: Start local server to receive callback
    print(f"🌐 Starting local server on port {PORT}...")
    
    with socketserver.TCPServer(("", PORT), CallbackHandler) as httpd:
        # Open browser
        webbrowser.open(auth_url)
        
        print("⏳ Waiting for authorization...")
        print("(Complete the authorization in your browser)")
        
        # Wait for callback (with timeout)
        httpd.timeout = 300  # 5 minutes timeout
        httpd.handle_request()
        
        # Wait for auth code
        if not auth_code_received.wait(timeout=60):
            print("\n❌ Timeout waiting for authorization callback")
            sys.exit(1)
    
    if not auth_code:
        print("\n❌ No authorization code received")
        sys.exit(1)
    
    print("✅ Authorization code received!")
    print("🔄 Exchanging code for tokens...")
    
    # Step 3: Exchange authorization code for tokens
    token_data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": REDIRECT_URI
    }
    
    # Prepare Basic Auth credentials
    auth_str = f"{CLIENT_ID}:{CLIENT_SECRET}"
    auth_bytes = auth_str.encode('ascii')
    auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
    
    headers = {
        "Authorization": f"Basic {auth_b64}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    try:
        response = requests.post(TOKEN_URL, data=token_data, headers=headers)
        response.raise_for_status()
        
        tokens = response.json()
        
        # Debug: Show full response structure
        print(f"\n📋 Full token response: {json.dumps(tokens, indent=2)}")
        print(f"📋 Response keys: {list(tokens.keys())}")
        
        access_token = tokens.get('access_token')
        refresh_token = tokens.get('refresh_token')
        
        # Try alternative key names
        if not refresh_token:
            refresh_token = tokens.get('refreshToken')  # camelCase variant
        if not refresh_token:
            refresh_token = tokens.get('refresh_token')  # snake_case
        
        if not access_token:
            print("❌ Error: No access token in response")
            print(f"Response: {tokens}")
            sys.exit(1)
        
        print("\n✅ Tokens received successfully!")
        print(f"   Access token: {access_token[:20]}...")
        
        if refresh_token:
            print(f"   Refresh token: {refresh_token[:20]}...")
        else:
            print("   ⚠️  Warning: No refresh_token found in response")
            print("   This might be normal - TickTick may not always return refresh_token")
            print("   The access_token will work, but you may need to re-authenticate when it expires")
        
        # Step 4: Save tokens to .env file
        env_path = Path('.env')
        env_content = {}
        
        # Read existing .env file
        if env_path.exists():
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_content[key] = value
        
        # Update tokens
        env_content["TICKTICK_ACCESS_TOKEN"] = access_token
        if refresh_token:
            env_content["TICKTICK_REFRESH_TOKEN"] = refresh_token
        else:
            # Keep existing refresh token if no new one provided
            if "TICKTICK_REFRESH_TOKEN" not in env_content:
                print("   ⚠️  No refresh token to save - keeping existing if present")
        
        # Make sure client credentials are saved
        env_content["TICKTICK_CLIENT_ID"] = CLIENT_ID
        env_content["TICKTICK_CLIENT_SECRET"] = CLIENT_SECRET
        
        # Write back to .env file
        with open(env_path, 'w') as f:
            for key, value in env_content.items():
                f.write(f"{key}={value}\n")
        
        print("\n✅ Tokens saved to .env file!")
        print("\n📝 Your .env file now contains:")
        print(f"   TICKTICK_ACCESS_TOKEN={access_token[:20]}...")
        if refresh_token:
            print(f"   TICKTICK_REFRESH_TOKEN={refresh_token[:20]}...")
        
        print("\n🎉 Setup complete! You can now run the MCP server:")
        print("   python main.py")
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error exchanging code for tokens: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        get_tokens()
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
        sys.exit(1)

