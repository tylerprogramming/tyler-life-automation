from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse
from services.instagram_auth import instagram_auth_service
from dotenv import load_dotenv
import os
import httpx
import urllib.parse

load_dotenv()

# Instagram Basic Display API credentials for direct Instagram OAuth
INSTAGRAM_BASIC_CLIENT_ID = os.getenv("INSTAGRAM_CLIENT_ID")
INSTAGRAM_BASIC_CLIENT_SECRET = os.getenv("INSTAGRAM_CLIENT_SECRET")
BASE_URL = "https://choice-entirely-coyote.ngrok-free.app"
INSTAGRAM_BASIC_REDIRECT_URI = f"{BASE_URL}/instagram/callback"

# Frontend URL to redirect to after OAuth completion
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://funny-mooncake-29cf69.netlify.app")

router = APIRouter()

@router.get("/callback")
async def instagram_basic_callback(
    code: str = Query(..., description="Authorization code from Instagram"),
    state: str = Query(None, description="State parameter for CSRF protection"),
    error: str = Query(None, description="Error parameter if authorization failed"),
    error_reason: str = Query(None, description="Error reason if authorization failed"),
    error_description: str = Query(None, description="Error description if authorization failed")
):
    """
    Instagram Basic Display API OAuth callback endpoint
    Called by Instagram after user authorization
    """
    try:
        print(f"=== INSTAGRAM OAUTH CALLBACK ===")
        print(f"Code: {code[:20] if code else None}...")
        print(f"State: {state}")
        print(f"Error: {error}")
        
        # Check if there was an error in the OAuth flow
        if error:
            print(f"❌ OAuth Error: {error} - {error_description}")
            # Redirect to frontend with error parameters
            error_params = {
                "success": "false",
                "error": error,
                "error_description": error_description or error_reason or "Instagram authentication failed"
            }
            error_url = f"{FRONTEND_URL}/{urllib.parse.urlencode(error_params)}"
            print(f"🔀 Redirecting to frontend with error: {error_url}")
            return RedirectResponse(url=error_url)
        
        # Exchange authorization code for access token
        token_url = "https://api.instagram.com/oauth/access_token"
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {
            "client_id": INSTAGRAM_BASIC_CLIENT_ID,
            "client_secret": INSTAGRAM_BASIC_CLIENT_SECRET,
            "grant_type": "authorization_code",
            "redirect_uri": INSTAGRAM_BASIC_REDIRECT_URI,
            "code": code
        }
        
        print(f"🔄 Exchanging code for token...")
        
        async with httpx.AsyncClient() as client:
            resp = await client.post(token_url, data=data, headers=headers)
            
            print(f"📝 Response status: {resp.status_code}")
            
            if resp.status_code == 200:
                token_data = resp.json()
                
                # Exchange short-lived token for long-lived token
                long_lived_url = "https://graph.instagram.com/access_token"
                long_lived_params = {
                    "grant_type": "ig_exchange_token",
                    "client_secret": INSTAGRAM_BASIC_CLIENT_SECRET,
                    "access_token": token_data.get("access_token")
                }
                
                long_lived_resp = await client.get(long_lived_url, params=long_lived_params)
                
                response_data = {
                    "success": True,
                    "access_token": token_data.get("access_token"),
                    "user_id": token_data.get("user_id"),
                    "token_type": "short_lived"
                }
                
                if long_lived_resp.status_code == 200:
                    long_lived_data = long_lived_resp.json()
                    response_data.update({
                        "long_lived_access_token": long_lived_data.get("access_token"),
                        "expires_in": long_lived_data.get("expires_in"),
                        "token_type": "long_lived"
                    })
                    print(f"✅ Long-lived token obtained")
                else:
                    print(f"⚠️ Long-lived token exchange failed, using short-lived token")
                
                print(f"✅ Instagram OAuth successful!")
                print(f"👤 User ID: {response_data.get('user_id')}")
                print(f"🔑 Token type: {response_data.get('token_type')}")
                
                # Save user data securely to database
                try:
                    access_token = response_data.get("long_lived_access_token") or response_data.get("access_token")
                    user_id = str(response_data.get("user_id"))  # Ensure user_id is string
                    token_type = response_data.get("token_type")
                    expires_in = response_data.get("expires_in")
                    
                    saved_user = await instagram_auth_service.save_instagram_user(
                        access_token=access_token,
                        user_id=user_id,
                        token_type=token_type,
                        expires_in=expires_in
                    )
                    
                    print(f"💾 User data saved securely for @{saved_user.username}")
                    
                    # Redirect to frontend with success (without access token for security)
                    success_params = {
                        "success": "true",
                        "user_id": user_id,
                        "username": saved_user.username,
                        "account_type": saved_user.account_type,
                        "media_count": saved_user.media_count,
                        "token_type": token_type
                    }
                    success_url = f"{FRONTEND_URL}?{urllib.parse.urlencode(success_params)}"
                    print(f"🔀 Redirecting to frontend with success: {success_url}")
                    return RedirectResponse(url=success_url)
                    
                except Exception as save_error:
                    print(f"❌ Error saving user data: {str(save_error)}")
                    # Still redirect to frontend but with error
                    error_params = {
                        "success": "false",
                        "error": "save_failed",
                        "error_description": "Failed to save user data securely"
                    }
                    error_url = f"{FRONTEND_URL}?{urllib.parse.urlencode(error_params)}"
                    return RedirectResponse(url=error_url)
                
            else:
                error_response = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {"error_message": resp.text}
                error_message = error_response.get("error_message", "Unknown error")
                
                print(f"❌ Token exchange failed: {error_message}")
                
                # Redirect to frontend with error
                error_params = {
                    "success": "false",
                    "error": "token_exchange_failed",
                    "error_description": error_message
                }
                error_url = f"{FRONTEND_URL}/instagram/callback?{urllib.parse.urlencode(error_params)}"
                print(f"🔀 Redirecting to frontend with error: {error_url}")
                return RedirectResponse(url=error_url)
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Callback error: {str(e)}")
        # Redirect to frontend with error
        error_params = {
            "success": "false",
            "error": "callback_processing_failed",
            "error_description": str(e)
        }
        error_url = f"{FRONTEND_URL}/instagram/callback?{urllib.parse.urlencode(error_params)}"
        print(f"🔀 Redirecting to frontend with error: {error_url}")
        return RedirectResponse(url=error_url)

@router.get("/user-info")
async def get_instagram_user_info(
    user_id: str = Query(..., description="Instagram user ID")
):
    """
    Get Instagram user info from database (secure, no access token needed in request)
    """
    try:
        print(f"🔍 Getting user info for ID: {user_id}")
        
        # Get user from database
        user = instagram_auth_service.get_user_by_instagram_id(user_id)
        if not user:
            return {
                "success": False,
                "error": "User not found",
                "message": "Instagram user not found in database"
            }
        
        # Update last used timestamp
        instagram_auth_service.update_last_used(user)
        
        print(f"✅ User info retrieved for @{user.username}")
        return {
            "success": True,
            "user": {
                "id": user.instagram_user_id,
                "username": user.username,
                "account_type": user.account_type,
                "media_count": user.media_count,
                "token_type": user.token_type,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_used_at": user.last_used_at.isoformat() if user.last_used_at else None
            }
        }
                
    except Exception as e:
        print(f"❌ Error getting user info: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting Instagram user info: {str(e)}"
        )

@router.post("/disconnect")
async def disconnect_instagram_user(
    user_id: str = Query(..., description="Instagram user ID to disconnect")
):
    """
    Disconnect (deactivate) an Instagram user
    """
    try:
        print(f"🔌 Disconnecting Instagram user: {user_id}")
        
        success = instagram_auth_service.deactivate_user(user_id)
        if success:
            return {
                "success": True,
                "message": "Instagram account disconnected successfully"
            }
        else:
            return {
                "success": False,
                "error": "User not found",
                "message": "Instagram user not found"
            }
                
    except Exception as e:
        print(f"❌ Error disconnecting user: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error disconnecting Instagram user: {str(e)}"
        )

@router.get("/user-with-token")
async def get_user_with_token(user_id: int = Query(...)):
    """Get Instagram user by ID with decrypted access token (for internal use)"""
    try:
        print(f"🔍 Getting user with token for ID: {user_id}")
        user_data = instagram_auth_service.get_user_by_id_with_token(user_id)
        
        if not user_data:
            print(f"❌ User not found for ID: {user_id}")
            raise HTTPException(status_code=404, detail="Instagram user not found")
        
        # Check if token decryption failed
        if not user_data["access_token"]:
            print(f"❌ Token decryption failed for @{user_data['user']['username']}")
            return {
                "success": False,
                "error": "decryption_failed",
                "message": "Access token could not be decrypted. User needs to re-authenticate.",
                "user": user_data["user"],
                "access_token": None,
                "token_length": 0,
                "token_preview": "Decryption failed"
            }
        
        print(f"✅ Successfully retrieved and decrypted token for @{user_data['user']['username']}")
        return {
            "success": True,
            "user": user_data["user"],
            "access_token": user_data["access_token"],
            "token_length": len(user_data["access_token"]),
            "token_preview": f"{user_data['access_token'][:15]}...{user_data['access_token'][-10:]}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting user with token: {str(e)}")
        print(f"❌ Error type: {type(e)}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to get user with token: {str(e)}")

@router.post("/disconnect")
async def disconnect_user(user_id: int = Query(...)):
    """Disconnect/deactivate an Instagram user"""
    try:
        success = instagram_auth_service.deactivate_user(str(user_id))
        
        if not success:
            raise HTTPException(status_code=404, detail="Instagram user not found")
        
        return {
            "success": True,
            "message": "Instagram account disconnected successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error disconnecting user: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to disconnect user")

@router.get("/users")
async def get_all_instagram_users(include_inactive: bool = Query(False, description="Include inactive users")):
    """Get all Instagram users from the database"""
    try:
        users = instagram_auth_service.get_all_users(include_inactive=include_inactive)
        
        return {
            "success": True,
            "count": len(users),
            "users": users,
            "message": f"Found {len(users)} Instagram users"
        }
        
    except Exception as e:
        print(f"Error getting all Instagram users: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve Instagram users") 