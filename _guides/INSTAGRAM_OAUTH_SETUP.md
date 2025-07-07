# Instagram OAuth Setup Guide - Simplified

This project uses **Direct Instagram OAuth** with the Instagram Basic Display API for a clean, simple authentication experience.

## Why This Approach?
- ✅ **No Facebook login required** - Users authenticate directly with Instagram
- ✅ **Simpler user experience** - One-step authentication 
- ✅ **Minimal codebase** - Clean, focused implementation
- ✅ **Works for personal accounts** - No business account requirement

## Setup Steps

### 1. Create Instagram Basic Display App

1. Go to [Facebook for Developers](https://developers.facebook.com/)
2. Create a new app or use existing one
3. Add "Instagram Basic Display" product
4. **Important:** This is separate from Instagram Graph API

### 2. Configure OAuth Redirect URI

In your app dashboard: Products > Instagram Basic Display > Basic Display
- Add OAuth Redirect URI: `https://your-domain.com/instagram/basic/callback`
- **Must match exactly** what your frontend sends

### 3. Environment Variables

Add to your `.env` file:
```env
INSTAGRAM_CLIENT_ID=your_instagram_basic_display_app_id
INSTAGRAM_CLIENT_SECRET=your_instagram_basic_display_app_secret
FRONTEND_URL=https://funny-mooncake-29cf69.netlify.app/
```

**Note:** Set `FRONTEND_URL` to your frontend's base URL. After OAuth completion, users will be redirected to `{FRONTEND_URL}/instagram/callback`.

### 4. Frontend Integration

Use this exact authorization URL in your frontend:

```javascript
const instagramAuthUrl = 'https://api.instagram.com/oauth/authorize' +
  '?client_id=YOUR_INSTAGRAM_APP_ID' +
  '&redirect_uri=https://your-domain.com/instagram/callback' +
  '&scope=user_profile,user_media' +
  '&response_type=code' +
  '&state=' + Math.random().toString(36).substring(7);

// Redirect user to Instagram
window.location.href = instagramAuthUrl;
```

**Important:** 
- Use Instagram Basic Display App ID (not Facebook App ID)
- Redirect URI must match backend route exactly: `/instagram/callback`
- Use scopes: `user_profile,user_media`
- Backend will redirect to your frontend after processing

## Available API Endpoints

### OAuth Flow
- `GET /instagram/callback` - Handle Instagram OAuth callback (called by Instagram, redirects to frontend)

### User Information  
- `GET /instagram/basic/user-info?access_token=TOKEN` - Get user profile and media count

## User Flow

1. Frontend redirects user to Instagram authorization URL
2. User logs in with Instagram credentials on instagram.com
3. User authorizes your app 
4. Instagram redirects to your `/instagram/callback` endpoint
5. Backend exchanges code for access token
6. Backend redirects to your frontend with token data in URL parameters
7. Frontend extracts tokens from URL and can call `/instagram/basic/user-info`

## Response Format

### Frontend Redirect URLs:

**Success:**
```
{FRONTEND_URL}/instagram/callback?success=true&access_token=IGQVJ...&user_id=12345&token_type=long_lived&expires_in=5183944
```

**Error:**
```
{FRONTEND_URL}/instagram/callback?success=false&error=token_exchange_failed&error_description=Invalid+platform+app
```

### User Info Response:
```json
{
  "success": true,
  "user": {
    "id": "12345",
    "username": "john_doe",
    "account_type": "PERSONAL",
    "media_count": 42
  }
}
```

## Terminal Output

When testing, you'll see clean terminal output like:
```
=== INSTAGRAM OAUTH CALLBACK ===
Code: ABC123...
State: xyz789
Error: None
🔄 Exchanging code for token...
📝 Response status: 200
✅ Long-lived token obtained
✅ Instagram OAuth successful!
👤 User ID: 12345
🔑 Token type: long_lived
```

## Testing

Test the OAuth flow:
1. Set up your Instagram app and environment variables
2. Create the frontend authorization URL with your credentials
3. Visit the URL in your browser
4. Complete Instagram OAuth
5. Check terminal output for success messages

This provides a **clean, minimal Instagram authentication solution** without the complexity of Facebook OAuth! 🎉 