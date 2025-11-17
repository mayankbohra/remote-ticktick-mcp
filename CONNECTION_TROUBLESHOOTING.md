# Connection Troubleshooting Guide

## Issue: Claude AI Shows "Disconnected" Status

If your TickTick connector shows "Disconnected" in Claude AI, here are the most common causes and fixes:

### 1. API Key Authentication Blocking Connection

**Problem**: Your server requires `MCP_API_KEY` but Claude AI's custom connector doesn't support API key authentication yet.

**Solution**: Temporarily disable API key authentication:

1. **In Render Dashboard:**
   - Go to your service → Environment
   - **Remove or leave `MCP_API_KEY` empty**
   - Save changes (Render will auto-redeploy)

2. **Verify the change:**
   ```bash
   curl https://remote-ticktick-mcp.onrender.com/health
   ```
   Should show: `"authentication": "disabled"`

3. **Try connecting in Claude AI again**

**Security Note**: Without API key, your server is publicly accessible. Only your TickTick tokens are protected (stored on server).

### 2. Root Path Returning 404

**Problem**: Claude AI probes the root path `/` during connection, but it returns 404.

**Solution**: Already fixed! The code now includes a root endpoint that returns service information.

**Verify**:
```bash
curl https://remote-ticktick-mcp.onrender.com/
```
Should return JSON with service info.

### 3. MCP Endpoint Not Accessible

**Problem**: The `/mcp` endpoint might not be accessible or returning errors.

**Check**:
1. **Verify MCP endpoint exists:**
   ```bash
   curl -X POST https://remote-ticktick-mcp.onrender.com/mcp \
     -H "Content-Type: application/json" \
     -H "Accept: application/json, text/event-stream" \
     -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
   ```

2. **If you get 401 (Unauthorized):**
   - API key is blocking - disable it (see solution #1)

3. **If you get 404:**
   - Check server logs in Render
   - Verify FastMCP is mounting correctly

### 4. CORS Issues

**Problem**: Browser blocking requests due to CORS.

**Solution**: Already configured! The server allows:
- `https://claude.ai`
- `https://claude.com`
- `https://*.anthropic.com`

### 5. Server Not Responding

**Problem**: Server is sleeping (free tier) or crashed.

**Check**:
1. **Health endpoint:**
   ```bash
   curl https://remote-ticktick-mcp.onrender.com/health
   ```

2. **Render logs:**
   - Check for errors
   - Verify server started successfully
   - Look for "Your service is live 🎉"

3. **Free tier sleep:**
   - First request after sleep takes ~10 seconds
   - This is normal - wait and retry

### 6. Wrong URL in Claude AI

**Problem**: Typo or incorrect URL in Claude AI connector settings.

**Verify**:
- URL should be: `https://remote-ticktick-mcp.onrender.com`
- No trailing slash
- Must be HTTPS (not HTTP)
- Check for typos

## Step-by-Step Debugging

### Step 1: Check Server Status

```bash
# Test health endpoint
curl https://remote-ticktick-mcp.onrender.com/health

# Test root endpoint
curl https://remote-ticktick-mcp.onrender.com/

# Check server logs in Render dashboard
```

### Step 2: Test MCP Endpoint

```bash
# Without API key (if disabled)
curl -X POST https://remote-ticktick-mcp.onrender.com/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'

# With API key (if enabled)
curl -X POST https://remote-ticktick-mcp.onrender.com/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Authorization: Bearer YOUR_MCP_API_KEY" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

### Step 3: Check Claude AI Connection

1. **In Claude AI:**
   - Settings → Connectors
   - Find "TickTick" connector
   - Click "Configure" or "Connect"
   - Check for error messages

2. **Common errors:**
   - "Connection failed" → Server not accessible (check Step 1)
   - "Invalid API key" → API key mismatch or not supported
   - "Timeout" → Server sleeping or slow response

### Step 4: Review Render Logs

Look for:
- ✅ "Your service is live 🎉"
- ✅ "Registered X tools"
- ❌ 401 errors (authentication issues)
- ❌ 404 errors (endpoint not found)
- ❌ 500 errors (server errors)

## Quick Fix Checklist

- [ ] Server is running (check Render logs)
- [ ] Health endpoint works: `curl https://YOUR-SERVICE.onrender.com/health`
- [ ] Root endpoint works: `curl https://YOUR-SERVICE.onrender.com/`
- [ ] API key disabled (if Claude AI doesn't support it)
- [ ] URL is correct in Claude AI (no typos, HTTPS)
- [ ] CORS is configured (already done)
- [ ] All environment variables set in Render

## Most Likely Solution

Based on the logs showing 404s and "Disconnected" status:

**Most likely cause**: API key authentication is blocking Claude AI's connection attempts.

**Quick fix**:
1. Go to Render → Your service → Environment
2. Remove `MCP_API_KEY` (or set to empty string)
3. Save (auto-redeploys)
4. Wait 1-2 minutes
5. Try connecting in Claude AI again

## After Fixing

Once connected, you should see:
- ✅ "Connected" status in Claude AI
- ✅ Tool count (e.g., "20+ tools available")
- ✅ Can query TickTick through Claude

Test with:
- "Show me all my TickTick projects"
- "What tasks are due today?"

