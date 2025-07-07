# Instagram Direct OAuth - Frontend Integration Guide

This guide shows how to integrate the direct Instagram OAuth flow into your frontend application.

## 🎯 Direct Instagram OAuth Flow

### Overview
1. User clicks "Connect Instagram" in your frontend
2. Frontend calls backend to get OAuth URL
3. User is redirected to Instagram for authentication
4. Instagram redirects back to your backend callback
5. Backend processes tokens and redirects back to frontend with results
6. Frontend saves user data and tokens

## Backend Endpoints Available

### 1. Start OAuth Flow (for Frontend)
```
GET /instagram/basic/login-frontend?frontend_redirect={your_frontend_url}
```

**Response:**
```json
{
  "auth_url": "https://api.instagram.com/oauth/authorize?client_id=...",
  "state": "random_csrf_token",
  "callback_uri": "https://yourapi.com/instagram/basic/callback-frontend",
  "frontend_redirect": "https://yourfrontend.com/instagram/success",
  "message": "Direct to this URL to start Instagram OAuth flow"
}
```

### 2. OAuth Callback (handles Instagram redirect)
```
GET /instagram/basic/callback-frontend?code={auth_code}&frontend_redirect={your_frontend_url}
```

**Redirects to your frontend with:**
- ✅ Success: `{frontend_url}?success=true&access_token={token}&user_id={id}&token_type=long_lived&expires_in={seconds}`
- ❌ Error: `{frontend_url}?success=false&error={error_type}&error_description={details}`

### 3. Save User Data
```
POST /instagram/basic/save-user?access_token={token}&user_id={id}&expires_in={seconds}
```

### 4. Get User Info
```
GET /instagram/basic/user-info?access_token={token}
```

### 5. Get User Media
```
GET /instagram/basic/user-media?access_token={token}&limit=10
```

## Frontend Implementation Examples

### React Example

```javascript
// InstagramConnect.jsx
import React, { useState, useEffect } from 'react';

const InstagramConnect = () => {
  const [isConnecting, setIsConnecting] = useState(false);
  const [user, setUser] = useState(null);
  const [error, setError] = useState(null);

  const API_BASE = 'http://localhost:8000'; // Your backend URL
  const FRONTEND_REDIRECT = 'http://localhost:3000/instagram/callback'; // Your frontend callback

  // Handle Instagram OAuth
  const connectInstagram = async () => {
    try {
      setIsConnecting(true);
      setError(null);

      // Get OAuth URL from backend
      const response = await fetch(
        `${API_BASE}/instagram/basic/login-frontend?frontend_redirect=${encodeURIComponent(FRONTEND_REDIRECT)}`
      );
      const data = await response.json();

      if (data.auth_url) {
        // Redirect user to Instagram
        window.location.href = data.auth_url;
      } else {
        throw new Error('Failed to get Instagram auth URL');
      }
    } catch (err) {
      setError(err.message);
      setIsConnecting(false);
    }
  };

  // Handle callback from Instagram (called when user returns)
  useEffect(() => {
    const handleInstagramCallback = async () => {
      const urlParams = new URLSearchParams(window.location.search);
      const success = urlParams.get('success');
      const accessToken = urlParams.get('access_token');
      const userId = urlParams.get('user_id');
      const expiresIn = urlParams.get('expires_in');
      const error = urlParams.get('error');

      if (success === 'true' && accessToken) {
        try {
          // Save user data to backend
          const saveResponse = await fetch(
            `${API_BASE}/instagram/basic/save-user?access_token=${accessToken}&user_id=${userId}&expires_in=${expiresIn}`,
            { method: 'POST' }
          );
          const saveData = await saveResponse.json();

          if (saveData.success) {
            setUser(saveData.user);
            localStorage.setItem('instagram_token', accessToken);
            localStorage.setItem('instagram_user', JSON.stringify(saveData.user));
            
            // Clean up URL
            window.history.replaceState({}, document.title, window.location.pathname);
          } else {
            throw new Error(saveData.error || 'Failed to save Instagram user');
          }
        } catch (err) {
          setError(err.message);
        } finally {
          setIsConnecting(false);
        }
      } else if (error) {
        setError(`Instagram authentication failed: ${error}`);
        setIsConnecting(false);
      }
    };

    // Check if this is a callback from Instagram
    if (window.location.pathname === '/instagram/callback') {
      handleInstagramCallback();
    }

    // Check if user is already connected
    const savedUser = localStorage.getItem('instagram_user');
    if (savedUser) {
      setUser(JSON.parse(savedUser));
    }
  }, []);

  const disconnectInstagram = () => {
    setUser(null);
    localStorage.removeItem('instagram_token');
    localStorage.removeItem('instagram_user');
  };

  if (user) {
    return (
      <div className="instagram-connected">
        <h3>Instagram Connected! ✅</h3>
        <div className="user-info">
          <p><strong>Username:</strong> @{user.username}</p>
          <p><strong>Account Type:</strong> {user.account_type}</p>
          <p><strong>Media Count:</strong> {user.media_count}</p>
        </div>
        <button onClick={disconnectInstagram} className="disconnect-btn">
          Disconnect Instagram
        </button>
      </div>
    );
  }

  return (
    <div className="instagram-connect">
      <h3>Connect Your Instagram Account</h3>
      <p>Quick and easy - just Instagram login required!</p>
      
      {error && (
        <div className="error-message">
          ❌ {error}
        </div>
      )}
      
      <button 
        onClick={connectInstagram} 
        disabled={isConnecting}
        className="connect-btn"
      >
        {isConnecting ? 'Connecting...' : '📷 Connect Instagram'}
      </button>
      
      <div className="benefits">
        <p>✅ No Facebook account required</p>
        <p>✅ Direct Instagram authentication</p>
        <p>✅ Access your photos and profile</p>
      </div>
    </div>
  );
};

export default InstagramConnect;
```

### Vanilla JavaScript Example

```html
<!DOCTYPE html>
<html>
<head>
    <title>Instagram Connect</title>
</head>
<body>
    <div id="instagram-app">
        <div id="connect-section">
            <h3>Connect Your Instagram</h3>
            <button onclick="connectInstagram()">📷 Connect Instagram</button>
            <div id="status"></div>
        </div>
        
        <div id="user-section" style="display: none;">
            <h3>Instagram Connected! ✅</h3>
            <div id="user-info"></div>
            <button onclick="disconnectInstagram()">Disconnect</button>
        </div>
    </div>

    <script>
        const API_BASE = 'http://localhost:8000';
        const FRONTEND_REDIRECT = 'http://localhost:3000/instagram/callback';

        async function connectInstagram() {
            try {
                document.getElementById('status').innerHTML = 'Connecting...';
                
                const response = await fetch(
                    `${API_BASE}/instagram/basic/login-frontend?frontend_redirect=${encodeURIComponent(FRONTEND_REDIRECT)}`
                );
                const data = await response.json();
                
                if (data.auth_url) {
                    window.location.href = data.auth_url;
                } else {
                    throw new Error('Failed to get auth URL');
                }
            } catch (error) {
                document.getElementById('status').innerHTML = `❌ ${error.message}`;
            }
        }

        async function handleCallback() {
            const urlParams = new URLSearchParams(window.location.search);
            const success = urlParams.get('success');
            const accessToken = urlParams.get('access_token');
            const userId = urlParams.get('user_id');
            const expiresIn = urlParams.get('expires_in');

            if (success === 'true' && accessToken) {
                try {
                    const saveResponse = await fetch(
                        `${API_BASE}/instagram/basic/save-user?access_token=${accessToken}&user_id=${userId}&expires_in=${expiresIn}`,
                        { method: 'POST' }
                    );
                    const saveData = await saveResponse.json();

                    if (saveData.success) {
                        localStorage.setItem('instagram_user', JSON.stringify(saveData.user));
                        showUserInfo(saveData.user);
                        window.history.replaceState({}, document.title, '/');
                    }
                } catch (error) {
                    document.getElementById('status').innerHTML = `❌ ${error.message}`;
                }
            }
        }

        function showUserInfo(user) {
            document.getElementById('connect-section').style.display = 'none';
            document.getElementById('user-section').style.display = 'block';
            document.getElementById('user-info').innerHTML = `
                <p><strong>Username:</strong> @${user.username}</p>
                <p><strong>Account Type:</strong> ${user.account_type}</p>
                <p><strong>Media Count:</strong> ${user.media_count}</p>
            `;
        }

        function disconnectInstagram() {
            localStorage.removeItem('instagram_user');
            document.getElementById('connect-section').style.display = 'block';
            document.getElementById('user-section').style.display = 'none';
        }

        // Check for existing user or callback
        window.onload = function() {
            const savedUser = localStorage.getItem('instagram_user');
            if (savedUser) {
                showUserInfo(JSON.parse(savedUser));
            } else if (window.location.pathname === '/instagram/callback') {
                handleCallback();
            }
        };
    </script>
</body>
</html>
```

## Router Setup (React Router Example)

```javascript
// App.js
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import InstagramConnect from './components/InstagramConnect';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<InstagramConnect />} />
        <Route path="/instagram/callback" element={<InstagramConnect />} />
        {/* Other routes */}
      </Routes>
    </Router>
  );
}
```

## Environment Variables Needed

Add these to your backend environment:

```env
# Instagram Basic Display API
INSTAGRAM_BASIC_CLIENT_ID=your_instagram_basic_app_id
INSTAGRAM_BASIC_CLIENT_SECRET=your_instagram_basic_app_secret
```

## Testing the Flow

1. **Start your backend**: `uvicorn social_server:app --reload`
2. **Start your frontend**: `npm start` (or your preferred method)
3. **Click "Connect Instagram"** in your frontend
4. **Login with Instagram** when redirected
5. **Get redirected back** to your frontend with tokens

## Production Considerations

1. **HTTPS Required**: Instagram requires HTTPS in production
2. **Environment Variables**: Keep client secrets secure
3. **Token Storage**: Consider encrypting stored access tokens
4. **Error Handling**: Implement comprehensive error handling
5. **Token Refresh**: Instagram Basic Display tokens expire after 60 days

## Available Data

With Instagram Basic Display API, you can access:
- ✅ User profile (id, username, account_type)
- ✅ User's media (photos, videos)
- ✅ Media details (captions, URLs, timestamps)
- ❌ Cannot post content (read-only access)

For posting content, you'd need the Facebook-based Instagram API flow.

## Summary

This direct Instagram OAuth approach gives you:
- 🎯 **Simpler user experience** - no Facebook login required
- ⚡ **Faster integration** - fewer steps for users
- 🔒 **Secure flow** - proper OAuth 2.0 implementation
- 📱 **Instagram-focused** - perfect for Instagram-only features

The callback endpoints handle all the complex OAuth token exchange, so your frontend just needs to redirect users and handle the success/error responses! 🚀 