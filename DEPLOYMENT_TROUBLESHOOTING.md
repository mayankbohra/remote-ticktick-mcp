# Deployment Troubleshooting Guide

## Issue: Deployment Times Out

If your Render deployment times out, here are the most common causes and fixes:

### 1. Health Check Not Configured

**Problem**: Render can't verify the service is healthy.

**Solution**: Make sure `render.yaml` includes:
```yaml
healthCheckPath: /health
```

### 2. Server Not Responding Fast Enough

**Problem**: Server takes too long to start or respond to health checks.

**Solutions**:

1. **Check server logs** in Render dashboard:
   - Look for errors during startup
   - Verify all environment variables are set
   - Check if the server actually starts

2. **Verify health endpoint works**:
   ```bash
   # After deployment, test:
   curl https://YOUR-SERVICE.onrender.com/health
   ```

3. **Increase startup timeout** (if needed):
   - Render free tier has limited timeout
   - Consider upgrading to Starter plan if consistently timing out

### 3. Missing Environment Variables

**Problem**: Server fails to start because required env vars are missing.

**Check**: All these must be set in Render:
- `TICKTICK_CLIENT_ID`
- `TICKTICK_CLIENT_SECRET`
- `TICKTICK_ACCESS_TOKEN`
- `TICKTICK_REFRESH_TOKEN` (can be placeholder if not available)
- `MCP_API_KEY` (highly recommended)

### 4. Port Binding Issues

**Problem**: Server not binding to the correct port.

**Solution**: The code already uses `PORT` env var correctly:
```python
port = int(os.getenv("PORT", 8000))
host = os.getenv("HOST", "0.0.0.0")
```

Render automatically sets `PORT`, so this should work.

### 5. Docker Build Issues

**Problem**: Docker image fails to build.

**Solutions**:
1. Check Dockerfile is correct
2. Verify `requirements.txt` has all dependencies
3. Check Render build logs for specific errors

### 6. FastMCP HTTP App Issues

**Problem**: FastMCP HTTP app not initializing correctly.

**Check logs for**:
- "StreamableHTTP session manager started" - should appear
- Any FastMCP-related errors
- Tool registration messages

## Quick Fixes

### If deployment keeps timing out:

1. **Verify health endpoint locally first**:
   ```bash
   python main.py
   # In another terminal:
   curl http://localhost:8000/health
   ```

2. **Check Render logs**:
   - Go to Render dashboard → Your service → Logs
   - Look for errors or warnings
   - Check if server actually starts

3. **Try manual deploy**:
   - Render dashboard → Manual Deploy → Deploy latest commit
   - Sometimes auto-deploy has issues

4. **Verify environment variables**:
   - All required vars are set
   - No typos in variable names
   - Values are correct (especially tokens)

### Common Error Messages

**"Timed Out"**:
- Health check not configured → Add `healthCheckPath: /health` to render.yaml
- Server not starting → Check logs for startup errors
- Missing env vars → Verify all required variables are set

**"Build Failed"**:
- Dockerfile issues → Check Dockerfile syntax
- Missing dependencies → Verify requirements.txt
- Python version → Check Dockerfile uses Python 3.11

**"Health Check Failed"**:
- Health endpoint not accessible → Verify `/health` route exists
- Server not responding → Check if server actually started
- Port issues → Verify PORT env var is set correctly

## Testing After Deployment

Once deployed, verify:

1. **Health endpoint**:
   ```bash
   curl https://YOUR-SERVICE.onrender.com/health
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

2. **Server logs**:
   - Should show "Starting Remote TickTick MCP server"
   - Should show "Registered X tools"
   - No error messages

3. **Connect to Claude AI**:
   - Use the Render URL
   - Use your MCP_API_KEY
   - Should connect successfully

## Still Having Issues?

1. Check Render documentation: https://render.com/docs/troubleshooting-deploys
2. Review server logs in Render dashboard
3. Test locally first to ensure code works
4. Verify all environment variables are set correctly

