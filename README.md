# TickTick Remote MCP Server 📋

Connect your [TickTick](https://ticktick.com/) account to Claude AI and manage all your tasks and projects directly in conversations!

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastMCP](https://img.shields.io/badge/FastMCP-2.0+-green.svg)](https://github.com/jlowin/fastmcp)

## ✨ What Can You Do?

Once set up, you can ask Claude:

- **"Show me all my TickTick projects"** - View all your projects
- **"What tasks do I have due today?"** - Get tasks due today
- **"Create a new task called 'Finish documentation' in my work project"** - Create tasks
- **"Show me all overdue tasks"** - Find overdue items
- **"Search for tasks about 'meeting'"** - Search across all tasks
- **"What are my engaged tasks?"** - Get high-priority or urgent tasks (GTD framework)

## 🚀 10-Minute Setup

### What You Need

- ✅ TickTick account ([Get one here](https://ticktick.com/))
- ✅ Claude AI (Pro/Team/Enterprise - any plan with MCP support)
- ✅ Free [Render](https://render.com/) account for hosting
- ✅ TickTick API credentials (Client ID, Client Secret, Access Token)

### Step 1: Get Your TickTick API Credentials (5 min)

1. **Register your application** at the [TickTick Developer Center](https://developer.ticktick.com/manage)
   - Set the redirect URI to `http://localhost:8000/callback`
   - Note your **Client ID** and **Client Secret**

2. **Authenticate locally** (one-time setup):
   - Clone the [ticktick-mcp](https://github.com/jacepark12/ticktick-mcp) repository
   - Run the authentication flow:
     ```bash
     uv run -m ticktick_mcp.cli auth
     ```
   - This will save your `TICKTICK_ACCESS_TOKEN` and `TICKTICK_REFRESH_TOKEN` to a `.env` file
   - Copy these tokens along with your Client ID and Secret

### Step 2: Fork & Deploy Server (5 min)

#### Option A: Deploy to Render (Recommended)

1. **Fork this repository**:
   - Click "Fork" button at the top of this GitHub page
   - This creates your own copy of the code

2. **Sign up at [Render](https://render.com)** (free tier available)

3. **Create New Web Service**:
   - Click "New +" → "Web Service"
   - Choose "Connect a Git repository"
   - Select your forked repository from the list

4. **Configure**:
   - **Name**: `ticktick-mcp-remote` (or your choice)
   - **Runtime**: Docker (auto-detected)
   - **Plan**: Free

5. **Add Environment Variables** (in Render dashboard):
   ```bash
   TICKTICK_CLIENT_ID=<your_client_id>
   TICKTICK_CLIENT_SECRET=<your_client_secret>
   TICKTICK_ACCESS_TOKEN=<your_access_token>
   TICKTICK_REFRESH_TOKEN=<your_refresh_token>
   MCP_API_KEY=<generate_a_secure_random_string>
   ```

   **Important**: Generate a secure random string for `MCP_API_KEY` (e.g., use `openssl rand -hex 32`)

6. Click **Create Web Service** and wait ~2 minutes

#### Option B: Other Platforms

<details>
<summary>Railway / Fly.io / Google Cloud Run</summary>

The server works on any platform that supports Docker. See `Dockerfile` for configuration.
</details>

### Step 3: Verify It's Running (1 min)

Visit: `https://YOUR-SERVICE-NAME.onrender.com/health`

You should see:
```json
{
  "status": "healthy",
  "service": "ticktick-mcp-remote",
  "version": "1.0.0",
  "authentication": "enabled"
}
```

✅ If you see this, you're good to go!

### Step 4: Connect to Claude (3 min)

1. **Open Claude AI** at https://claude.ai

2. **Go to Settings** → **Integrations** (or similar MCP section)

3. **Add MCP Server**:
   ```
   Name: TickTick
   URL: https://YOUR-SERVICE-NAME.onrender.com
   API Key: <your_MCP_API_KEY_from_step_2>
   ```

4. **Test Connection** - Should show "20+ tools available"

5. **Save** and you're done! 🎉

### Step 5: Start Using!

Try asking Claude:
- "Show me all my TickTick projects"
- "What tasks are due today?"
- "Create a task called 'Review PR' in my work project with high priority"
- "Show me all overdue tasks"

## 📖 All Available Features

### Project Tools (5 tools)
- **Get projects** - List all your projects
- **Get project** - Get details about a specific project
- **Get project tasks** - List all tasks in a project
- **Create project** - Create a new project
- **Delete project** - Delete a project

### Task Management Tools (6 tools)
- **Get task** - Get details about a specific task
- **Create task** - Create a new task with optional dates, priority, content
- **Update task** - Update task details
- **Complete task** - Mark a task as complete
- **Delete task** - Delete a task
- **Create subtask** - Create a subtask for a parent task

### Advanced Task Tools (9 tools)
- **Get all tasks** - Get all tasks from all projects
- **Get tasks by priority** - Filter by priority (None, Low, Medium, High)
- **Get tasks due today** - Tasks due today
- **Get tasks due tomorrow** - Tasks due tomorrow
- **Get tasks due in X days** - Tasks due in exactly X days
- **Get tasks due this week** - Tasks due within next 7 days
- **Get overdue tasks** - All overdue tasks
- **Search tasks** - Search by title, content, or subtask titles
- **Batch create tasks** - Create multiple tasks at once

### Getting Things Done (GTD) Tools (2 tools)
- **Get engaged tasks** - High priority, due today, or overdue tasks
- **Get next tasks** - Medium priority or due tomorrow tasks

### 🚀 Advanced Features
- ✅ **Automatic token refresh** - Handles OAuth token expiration automatically
- ✅ **Rate limiting** - Exponential backoff for API rate limits
- ✅ **Error handling** - Comprehensive error messages
- ✅ **Task filtering** - Filter by date, priority, search terms
- ✅ **Batch operations** - Create multiple tasks efficiently

## 🆓 Cost

**100% Free for Personal Use:**
- ✅ Render: 750 hours/month (runs 24/7)
- ✅ Uses your existing TickTick subscription
- ⚠️ Server "sleeps" after 15 min (10 sec wake-up on first request)

**Optional Upgrade:**
- 💵 $7/month for Render Starter (always-on, no sleep)

## 🛠️ Troubleshooting

### "Connection Failed" in Claude

1. Visit `https://YOUR-SERVICE.onrender.com/health` - Should return healthy status
2. Verify the URL is correct in Claude settings
3. Check that `MCP_API_KEY` matches between server and Claude
4. Wait 10 seconds if server was sleeping (free tier)

### Server Takes Long to Respond

- Free tier "sleeps" after 15 min inactivity
- First request after sleep takes ~10 seconds to wake up
- This is normal - subsequent requests are fast!

### "TickTick API Error"

- Check your `TICKTICK_ACCESS_TOKEN` in Render dashboard
- Token might have expired - the server will try to refresh automatically
- If refresh fails, you may need to re-authenticate locally and update tokens

### "Invalid API key" Error

- Verify `MCP_API_KEY` matches between server environment variables and Claude settings
- Make sure you're using `Bearer <token>` format in Claude (if required)

### Still Need Help?

- 📖 See the [local TickTick MCP documentation](https://github.com/jacepark12/ticktick-mcp) for authentication help
- 🐛 [Open an issue](https://github.com/YOUR-USERNAME/remote-ticktick-mcp/issues)

## 🔒 Security & Privacy

- ✅ All requests encrypted via HTTPS
- ✅ Your TickTick tokens stay on your server (never exposed to Claude)
- ✅ API key authentication protects your server
- ✅ Open source - inspect the code yourself!
- ⚠️ **Important**: Your server URL is public but only works with YOUR API key

**Keep your secrets safe:**
- Never commit `.env` files with tokens
- Don't share your TickTick tokens or API key
- Only you can access your data through your server
- Use a strong, random `MCP_API_KEY`

## 🧪 For Developers

### Run Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Configure
cp env.example .env
# Edit .env with your tokens

# Run
python main.py

# Test health endpoint
curl http://localhost:8000/health
```

### Docker

```bash
docker build -t ticktick-mcp-remote .
docker run -p 8000:8000 \
  -e TICKTICK_CLIENT_ID=your_id \
  -e TICKTICK_CLIENT_SECRET=your_secret \
  -e TICKTICK_ACCESS_TOKEN=your_token \
  -e TICKTICK_REFRESH_TOKEN=your_refresh_token \
  -e MCP_API_KEY=your_api_key \
  ticktick-mcp-remote
```

### Project Structure

```
remote-ticktick-mcp/
├── main.py              # FastMCP HTTP server (20+ tools)
├── ticktick_client.py   # Async TickTick API client
├── requirements.txt     # Python dependencies
├── Dockerfile          # Container config
├── render.yaml         # Render deployment
├── env.example         # Environment variable template
└── README.md           # This file
```

### Environment Variables

Required:
- `TICKTICK_CLIENT_ID` - OAuth client ID from TickTick Developer Center
- `TICKTICK_CLIENT_SECRET` - OAuth client secret
- `TICKTICK_ACCESS_TOKEN` - Current access token (obtained via OAuth flow)
- `TICKTICK_REFRESH_TOKEN` - Refresh token for automatic token renewal

Optional:
- `TICKTICK_BASE_URL` - API base URL (default: https://api.ticktick.com/open/v1)
- `TICKTICK_TOKEN_URL` - Token endpoint URL (default: https://ticktick.com/oauth/token)
- `MCP_API_KEY` - API key for server authentication (highly recommended)
- `PORT` - Server port (default: 8000)
- `HOST` - Server host (default: 0.0.0.0)
- `TICKTICK_RATE_LIMIT_DELAY` - Delay between API requests in seconds (default: 0.2)

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repo
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 🙏 Credits

Built with:
- [FastMCP](https://github.com/jlowin/fastmcp) - Python MCP framework
- [TickTick API](https://developer.ticktick.com/) - TickTick platform
- [MCP Protocol](https://modelcontextprotocol.io) - Anthropic's protocol
- Based on [ticktick-mcp](https://github.com/jacepark12/ticktick-mcp) - Local MCP server

## ⭐ Support

If you find this useful, please star the repository!

---

**Made with ❤️ for the TickTick and Claude AI community**

