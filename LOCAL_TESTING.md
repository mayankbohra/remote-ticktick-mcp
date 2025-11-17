# Local Testing Guide

## Prerequisites

Make sure you have all required environment variables set in your `.env` file:

### Required Variables

```bash
TICKTICK_CLIENT_ID=your_client_id_here
TICKTICK_CLIENT_SECRET=your_client_secret_here
TICKTICK_ACCESS_TOKEN=your_access_token_here
TICKTICK_REFRESH_TOKEN=your_refresh_token_here
```

### Optional but Recommended

```bash
MCP_API_KEY=your_secure_random_string_here
PORT=8000
HOST=0.0.0.0
```

### Optional TickTick Configuration

```bash
TICKTICK_BASE_URL=https://api.ticktick.com/open/v1
TICKTICK_TOKEN_URL=https://ticktick.com/oauth/token
TICKTICK_RATE_LIMIT_DELAY=0.2
```

## Getting Your TickTick Credentials

If you don't have your credentials yet:

1. **Register your app** at https://developer.ticktick.com/manage
   - Set redirect URI to: `http://localhost:8000/callback`

2. **Authenticate locally** using the original ticktick-mcp:
   ```bash
   # Clone the local MCP server
   git clone https://github.com/jacepark12/ticktick-mcp.git
   cd ticktick-mcp
   
   # Run authentication
   uv run -m ticktick_mcp.cli auth
   
   # This will create a .env file with your tokens
   # Copy TICKTICK_ACCESS_TOKEN and TICKTICK_REFRESH_TOKEN to your remote server .env
   ```

## Running the Server Locally

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Set Environment Variables

Copy `env.example` to `.env` and fill in your values:

```bash
cp env.example .env
# Edit .env with your actual credentials
```

### Step 3: Start the Server

```bash
python main.py
```

You should see:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Registered X tools: ...
```

### Step 4: Test the Health Endpoint

In another terminal:

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "ticktick-mcp-remote",
  "version": "1.0.0",
  "authentication": "enabled"
}
```

### Step 5: Run Test Script

```bash
python test_server.py
```

This will test:
- Health endpoint
- MCP tools listing
- A few sample tools

## Testing with Claude Desktop (Local)

To test with Claude Desktop locally:

1. **Start the server** (as above)

2. **Configure Claude Desktop**:
   
   Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

   ```json
   {
     "mcpServers": {
       "ticktick": {
         "url": "http://localhost:8000",
         "apiKey": "your_mcp_api_key_here"
       }
     }
   }
   ```

3. **Restart Claude Desktop**

4. **Test in Claude**:
   - "Show me all my TickTick projects"
   - "What tasks are due today?"

## Troubleshooting

### "TICKTICK_ACCESS_TOKEN environment variable is required"

- Make sure your `.env` file exists and contains `TICKTICK_ACCESS_TOKEN`
- Check that you're running from the correct directory
- Verify the token is valid (not expired)

### "Failed to refresh access token"

- Check that `TICKTICK_CLIENT_ID` and `TICKTICK_CLIENT_SECRET` are set
- Verify `TICKTICK_REFRESH_TOKEN` is valid
- You may need to re-authenticate if tokens expired

### "Connection refused" when testing

- Make sure the server is running (`python main.py`)
- Check that PORT matches (default 8000)
- Try `http://127.0.0.1:8000` instead of `localhost`

### "Invalid API key" error

- Make sure `MCP_API_KEY` in `.env` matches what you're using in requests
- If testing without API key, remove `MCP_API_KEY` from `.env` (not recommended)

### Server starts but tools don't work

- Check server logs for errors
- Verify your TickTick tokens are valid
- Test the health endpoint first
- Check that all required environment variables are set

## Manual Testing with curl

### Health Check
```bash
curl http://localhost:8000/health
```

### List Tools (requires MCP_API_KEY)
```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_MCP_API_KEY" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list"
  }'
```

### Call a Tool (get_projects)
```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_MCP_API_KEY" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "get_projects",
      "arguments": {}
    }
  }'
```

## Next Steps

Once local testing works:

1. Deploy to Render/Railway/etc. (see README.md)
2. Update environment variables in your deployment platform
3. Connect Claude AI to your deployed server URL

