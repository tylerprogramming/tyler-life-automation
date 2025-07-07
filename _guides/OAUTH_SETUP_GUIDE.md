# 🔐 OAuth Authentication Setup Guide

This guide will help you fix the `401 authorization required` error when using the `mine` parameter in YouTube API calls.

## 🚨 **Error You're Seeing**

```json
{
  "detail": "Error getting latest videos: <HttpError 401 when requesting https://youtube.googleapis.com/youtube/v3/channels?part=snippet&mine=true&key=AIzaSyB1Wldp7UVDCKmAA8HO7Wc3f5NHnBG9ASk&alt=json returned \"The request uses the <code>mine</code> parameter but is not properly authorized.\""
}
```

**The Problem:** The API is using an API key instead of OAuth authentication. The `mine=True` parameter requires OAuth, not just an API key.

## 🔧 **Solution Steps**

### Step 1: Set Up Google Cloud Project

1. **Go to [Google Cloud Console](https://console.cloud.google.com/)**
2. **Select your project** (or create a new one)
3. **Enable YouTube Data API v3:**
   - Go to APIs & Services > Library
   - Search for "YouTube Data API v3"
   - Click "Enable"

### Step 2: Create OAuth 2.0 Credentials

1. **Go to APIs & Services > Credentials**
2. **Click "Create Credentials" > "OAuth 2.0 Client IDs"**
3. **Choose "Desktop Application"**
4. **Name it** (e.g., "YouTube Analytics App")
5. **Download the JSON file**

### Step 3: Set Up Credentials in Your Project

1. **Create the credentials directory:**
   ```bash
   mkdir -p tyler-skool-members/youtube_credentials
   ```

2. **Copy your downloaded JSON file:**
   ```bash
   # Rename your downloaded file to client_secrets.json
   cp ~/Downloads/client_secret_XXXXX.json tyler-skool-members/youtube_credentials/client_secrets.json
   ```

3. **Check file structure:**
   ```
   tyler-skool-members/
   ├── youtube_credentials/
   │   └── client_secrets.json     # Your OAuth credentials
   ├── services/
   │   └── youtube.py
   └── ...
   ```

### Step 4: Test Authentication Locally

**Run this outside of Docker first:**

```bash
cd tyler-skool-members

# Test OAuth authentication
python3 -c "
import sys
sys.path.append('.')
from services.youtube import get_youtube_oauth_service

try:
    service = get_youtube_oauth_service()
    print('✅ OAuth authentication successful!')
    
    # Test getting your channel
    response = service.channels().list(part='snippet', mine=True).execute()
    if response.get('items'):
        channel = response['items'][0]
        print(f'✅ Found your channel: {channel[\"snippet\"][\"title\"]}')
    else:
        print('❌ No channel found')
        
except Exception as e:
    print(f'❌ Authentication failed: {e}')
"
```

This will:
- Open a browser for OAuth authorization
- Create `youtube_credentials/token.json` 
- Test that you can access your channel data

### Step 5: Update Docker Configuration

**Add volume mount to your `docker-compose.yml`:**

```yaml
services:
  fastapi-socialmedia:
    # ... other config ...
    volumes:
      - ./youtube_credentials:/app/youtube_credentials
      # ... other volumes ...
```

### Step 6: Restart Docker Services

```bash
# Stop and restart to pick up the new credentials
docker-compose down
docker-compose up -d
```

## 🧪 **Test Your Setup**

**Test the fixed endpoint:**

```bash
# Test getting your latest videos
curl "http://localhost:8000/youtube/latest_youtube_videos?max_results=2&include_comments=false"
```

**Expected Response:**
```json
{
  "videos": [
    {
      "video_id": "xxxxx",
      "title": "Your Video Title",
      "description": "...",
      // ... more video data
    }
  ],
  "count": 2,
  "message": "Retrieved 2 latest videos (excluding Shorts)"
}
```

## 🛠 **Troubleshooting**

### Issue: "Could not locate runnable browser"

**Solution:** This happens in Docker. Authenticate locally first:

```bash
# Stop Docker
docker-compose down

# Authenticate locally (this opens a browser)
cd tyler-skool-members
python3 -c "from services.youtube import get_youtube_oauth_service; get_youtube_oauth_service()"

# Restart Docker
docker-compose up -d
```

### Issue: "Credentials not found"

**Check these:**

```bash
# Verify file exists
ls -la tyler-skool-members/youtube_credentials/client_secrets.json

# Check file contents (should be valid JSON)
head tyler-skool-members/youtube_credentials/client_secrets.json
```

### Issue: "Invalid scope"

**Delete token and re-authenticate:**

```bash
# Delete existing token
rm tyler-skool-members/youtube_credentials/token.json

# Re-authenticate
python3 -c "from services.youtube import get_youtube_oauth_service; get_youtube_oauth_service()"
```

### Issue: "Channel not found"

**Verify you have a YouTube channel:**
- Go to [YouTube Studio](https://studio.youtube.com/)
- Make sure you have a channel created
- The OAuth account must be the channel owner

## 📋 **Required Scopes**

Your OAuth application needs these scopes:
- `https://www.googleapis.com/auth/youtube.readonly`
- `https://www.googleapis.com/auth/yt-analytics.readonly`
- `https://www.googleapis.com/auth/youtube.force-ssl`

These are automatically configured in the service.

## ✅ **Success Checklist**

- [ ] Google Cloud project created with YouTube Data API enabled
- [ ] OAuth 2.0 credentials created and downloaded
- [ ] `client_secrets.json` in `youtube_credentials/` folder
- [ ] Local authentication completed (browser flow)
- [ ] `token.json` file generated
- [ ] Docker volumes mounted correctly
- [ ] API endpoint returns your channel videos

## 🔒 **Security Notes**

1. **Never commit credentials to Git:**
   ```bash
   echo "youtube_credentials/" >> .gitignore
   ```

2. **Protect your credentials:**
   ```bash
   chmod 600 youtube_credentials/*.json
   ```

3. **Use environment variables in production**

Once you complete these steps, the `mine=True` parameter will work correctly and you'll be able to access your channel's videos and comments! 🎉 