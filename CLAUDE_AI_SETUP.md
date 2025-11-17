# Setting Up TickTick MCP with Claude AI

This guide will help you deploy your TickTick MCP server and connect it to Claude AI.

## Prerequisites

- ✅ TickTick account with API credentials
- ✅ Claude AI account (Pro/Team/Enterprise plan)
- ✅ GitHub account (for deployment)
- ✅ Render.com account (free tier works)

## Step 1: Deploy to Render (or Similar Platform)

### Option A: Render.com (Recommended - Free Tier Available)

1. **Push your code to GitHub:**
   ```bash
   cd /Users/mayank.bohra/Documents/Projects/remote-ticktick-mcp
   git init
   git add .
   git commit -m "Initial commit"
   
   # Create a new repository on GitHub, then:
   git remote add origin https://github.com/YOUR_USERNAME/remote-ticktick-mcp.git
   git push -u origin main
   ```

2. **Deploy on Render:**
   - Go to https://render.com
   - Sign up/Login (free tier available)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select your `remote-ticktick-mcp` repository

3. **Configure the service:**
   - **Name**: `ticktick-mcp-remote` (or your choice)
   - **Runtime**: Docker (auto-detected)
   - **Plan**: Free (or Starter for always-on)

4. **Add Environment Variables:**
   In the Render dashboard, add these environment variables:
   ```
   TICKTICK_CLIENT_ID=y9dTr8B0UOE3bYqCcX
   TICKTICK_CLIENT_SECRET=!h6Cu+ZR*c3L5n003xM3)N+ej&K@vPpk
   TICKTICK_ACCESS_TOKEN=6ab5788a-33d7-4421-8af9-742b24229371
   TICKTICK_REFRESH_TOKEN=your_refresh_token_here
   TICKTICK_BASE_URL=https://api.ticktick.com/open/v1
   TICKTICK_TOKEN_URL=https://ticktick.com/oauth/token
   MCP_API_KEY=<generate_a_secure_random_string>
   PORT=8000
   ```

   **Important**: Generate a secure `MCP_API_KEY`:
   ```bash
   # On macOS/Linux:
   openssl rand -hex 32
   
   # Or use Python:
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

5. **Deploy:**
   - Click "Create Web Service"
   - Wait 2-3 minutes for deployment
   - Your service URL will be: `https://ticktick-mcp-remote.onrender.com` (or your custom name)

6. **Verify Deployment:**
   ```bash
   curl https://YOUR-SERVICE-NAME.onrender.com/health
   ```
   Should return:
   ```json
   {
     "status": "healthy",
     "service": "ticktick-mcp-remote",
     "version": "1.0.0",
     "authentication": "enabled"
   }
   ```

### Option B: Railway.app (Alternative)

1. Go to https://railway.app
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repository
4. Add environment variables (same as Render)
5. Deploy

### Option C: Fly.io (Alternative)

1. Install Fly CLI: `curl -L https://fly.io/install.sh | sh`
2. Login: `fly auth login`
3. Launch: `fly launch`
4. Set secrets: `fly secrets set TICKTICK_CLIENT_ID=...` (for each variable)

## Step 2: Update TickTick OAuth Redirect URL (If Needed)

If you're using a different redirect URL for production:

1. Go to https://developer.ticktick.com/manage
2. Edit your app settings
3. Update "OAuth redirect URL" to your deployed server's callback URL (if different)
4. For local testing, keep: `http://localhost:8000/callback`

## Step 3: Connect to Claude AI

### For Claude.ai (Web)

1. **Go to Claude AI Settings:**
   - Visit https://claude.ai
   - Click your profile icon (top right)
   - Go to "Settings" → "Integrations" or "MCP Servers"

2. **Add MCP Server:**
   - Click "Add Server" or "Connect Server"
   - Fill in the details:
     ```
     Name: TickTick
     URL: https://YOUR-SERVICE-NAME.onrender.com
     API Key: <your_MCP_API_KEY_from_step_1>
     ```
   - Click "Save" or "Connect"

3. **Verify Connection:**
   - Claude should show "Connected" or "X tools available"
   - You should see ~20+ TickTick tools available

4. **Test It:**
   Try asking Claude:
   - "Show me all my TickTick projects"
   - "What tasks are due today?"
   - "Create a task called 'Test MCP' in my work project"

### For Claude Desktop (Alternative)

If you prefer Claude Desktop app:

1. **Edit Claude Desktop Config:**
   
   **macOS:**
   ```bash
   nano ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```
   
   **Windows:**
   ```bash
   notepad %APPDATA%\Claude\claude_desktop_config.json
   ```

2. **Add Configuration:**
   ```json
   {
     "mcpServers": {
       "ticktick": {
         "url": "https://YOUR-SERVICE-NAME.onrender.com",
         "apiKey": "YOUR_MCP_API_KEY_HERE"
       }
     }
   }
   ```

3. **Restart Claude Desktop**

## Step 4: Troubleshooting

### "Connection Failed" in Claude

1. **Check server is running:**
   ```bash
   curl https://YOUR-SERVICE-NAME.onrender.com/health
   ```

2. **Verify API Key:**
   - Make sure `MCP_API_KEY` in Render matches what you entered in Claude
   - Check for typos or extra spaces

3. **Check Render logs:**
   - Go to Render dashboard → Your service → Logs
   - Look for errors or warnings

4. **Free tier sleep:**
   - Render free tier sleeps after 15 min inactivity
   - First request after sleep takes ~10 seconds
   - This is normal - subsequent requests are fast

### "Invalid API key" Error

1. Verify `MCP_API_KEY` matches between:
   - Render environment variables
   - Claude AI settings
   - No extra spaces or quotes

2. Regenerate if needed:
   ```bash
   openssl rand -hex 32
   ```
   Update in both Render and Claude

### Server Not Responding

1. **Check Render status:**
   - Dashboard should show "Live" status
   - If "Sleeping", wait 10 seconds after first request

2. **Check logs:**
   - Render dashboard → Logs tab
   - Look for Python errors or import issues

3. **Verify environment variables:**
   - All required variables are set
   - No typos in variable names
   - Values are correct (especially tokens)

### Access Token Expired

If you get authentication errors:

1. **Re-authenticate locally:**
   ```bash
   cd /Users/mayank.bohra/Documents/Projects/remote-ticktick-mcp
   python get_tokens.py
   ```

2. **Update Render environment variables:**
   - Go to Render dashboard
   - Your service → Environment
   - Update `TICKTICK_ACCESS_TOKEN` with new token
   - Update `TICKTICK_REFRESH_TOKEN` if you got one

3. **Redeploy (if needed):**
   - Render auto-redeploys when env vars change
   - Or click "Manual Deploy" → "Deploy latest commit"

## Step 5: Testing with Claude AI

Once connected, test these commands:

### Basic Queries:
- "List all my TickTick projects"
- "Show me tasks due today"
- "What are my overdue tasks?"

### Task Management:
- "Create a task called 'Review PR' in my work project with high priority"
- "Mark task [task_id] as complete"
- "Update task [task_id] with due date tomorrow"

### Advanced:
- "Search for tasks about 'meeting'"
- "Show me my engaged tasks" (GTD framework)
- "What tasks are due this week?"

## Security Best Practices

1. **Never commit `.env` file:**
   - Already in `.gitignore`
   - Keep tokens secret

2. **Use strong MCP_API_KEY:**
   - At least 32 characters
   - Random and unpredictable
   - Don't share it publicly

3. **Rotate tokens periodically:**
   - Regenerate `MCP_API_KEY` if compromised
   - Re-authenticate TickTick tokens if expired

4. **Monitor usage:**
   - Check Render logs for unusual activity
   - Review TickTick API usage if available

## Cost

**Free Tier (Render):**
- ✅ 750 hours/month (runs 24/7)
- ⚠️ Sleeps after 15 min inactivity (~10 sec wake-up)
- ✅ Perfect for personal use

**Paid Tier (Optional):**
- 💵 $7/month for Render Starter
- ✅ Always-on, no sleep
- ✅ Better for production use

## Next Steps

1. ✅ Deploy to Render
2. ✅ Connect to Claude AI
3. ✅ Test with sample queries
4. 🎉 Start managing your TickTick tasks through Claude!

## Support

If you encounter issues:
1. Check Render logs
2. Verify environment variables
3. Test health endpoint: `curl https://YOUR-SERVICE.onrender.com/health`
4. Check Claude AI connection status

---

**Your server URL will be:** `https://YOUR-SERVICE-NAME.onrender.com`
**Keep this URL handy for Claude AI configuration!**

