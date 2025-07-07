from fastapi import APIRouter, HTTPException, Query
from services import instagram as instagram_service
from models.instagram import InstagramPostCreate, InstagramPostUpdate
from dotenv import load_dotenv

load_dotenv()

import os
import requests
import httpx
import secrets
import urllib.parse
from fastapi.responses import RedirectResponse, HTMLResponse

# Use consistent client credentials - Instagram Basic Display uses Facebook App credentials
CLIENT_ID = os.getenv("FACEBOOK_CLIENT_ID")  # Fixed: Use Facebook App ID for Instagram
CLIENT_SECRET = os.getenv("FACEBOOK_CLIENT_SECRET")  # Fixed: Use Facebook App Secret

# Make sure redirect URI matches EXACTLY what frontend sends
BASE_URL = "https://choice-entirely-coyote.ngrok-free.app"
REDIRECT_URI = f"{BASE_URL}/instagram/callback"  # No trailing slash, unencoded
SCOPES = "instagram_basic,instagram_content_publish"  # Match frontend scopes exactly

# NEW: Instagram Basic Display API credentials for direct Instagram OAuth
INSTAGRAM_BASIC_CLIENT_ID = os.getenv("INSTAGRAM_CLIENT_ID")
INSTAGRAM_BASIC_CLIENT_SECRET = os.getenv("INSTAGRAM_CLIENT_SECRET")
INSTAGRAM_BASIC_REDIRECT_URI = f"{BASE_URL}/instagram/basic/callback"
INSTAGRAM_BASIC_SCOPES = "user_profile,user_media"

FACEBOOK_CLIENT_ID = os.getenv("FACEBOOK_CLIENT_ID")
FACEBOOK_CLIENT_SECRET = os.getenv("FACEBOOK_CLIENT_SECRET")

router = APIRouter()

@router.post("/post_instagram_image")
async def post_instagram_image_route(image_urls: list[str]):
    return await instagram_service.post_instagram_image(image_urls)

@router.post("/post_instagram_reels")
async def post_instagram_reels_route(video_url: str):
    return await instagram_service.create_reels_container(video_url)

@router.post("/publish_instagram_container")
async def publish_instagram_container_route(container_id: str):
    return await instagram_service.publish_media_to_instagram(container_id)

@router.post("/poll_container_status")
async def poll_container_status_route(container_id: str):
    return await instagram_service.poll_until_ready(container_id)

@router.get("/refresh_instagram_access_token")
async def refresh_instagram_access_token_route():
    return instagram_service.refresh_instagram_access_token()

@router.get("/login")
async def instagram_login():
    state = secrets.token_urlsafe(16)
    
    # Match the EXACT same approach as frontend - Facebook OAuth endpoint
    auth_url = (
        f"https://www.facebook.com/dialog/oauth"
        f"?client_id={CLIENT_ID}"
        f"&display=page"
        f"&extras=%7B%22setup%22%3A%7B%22channel%22%3A%22IG_API_ONBOARDING%22%7D%7D"  # URL encoded JSON
        f"&redirect_uri={REDIRECT_URI}"  # Unencoded, matching frontend
        f"&response_type=code"
        f"&scope={SCOPES}"
    )
    
    print(f"=== LOGIN DEBUG ===")
    print(f"Using Facebook OAuth endpoint (matching frontend)")
    print(f"CLIENT_ID: {CLIENT_ID}")
    print(f"REDIRECT_URI: {REDIRECT_URI}")
    print(f"SCOPES: {SCOPES}")
    print(f"Full login URL: {auth_url}")
    print(f"✅ Now matching frontend exactly!")
    print(f"=== END LOGIN DEBUG ===")
    
    return RedirectResponse(auth_url)

@router.get("/debug-config")
async def debug_instagram_config():
    """Debug endpoint to show Instagram OAuth configuration"""
    return {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "redirect_uri_encoded": urllib.parse.quote(REDIRECT_URI, safe=''),
        "scopes": SCOPES,
        "environment_vars": {
            "FACEBOOK_CLIENT_ID": os.getenv("FACEBOOK_CLIENT_ID"),
            "FACEBOOK_CLIENT_SECRET": "***" if os.getenv("FACEBOOK_CLIENT_SECRET") else None,
            "INSTAGRAM_CLIENT_ID": os.getenv("INSTAGRAM_CLIENT_ID"),
            "INSTAGRAM_CLIENT_SECRET": "***" if os.getenv("INSTAGRAM_CLIENT_SECRET") else None,
        }
    }

@router.get("/callback")
async def instagram_callback(
    code: str = Query(..., description="Authorization code from Instagram"),
    state: str = Query(None, description="State parameter for CSRF protection"),
    error: str = Query(None, description="Error parameter if authorization failed"),
    error_reason: str = Query(None, description="Error reason if authorization failed"),
    error_description: str = Query(None, description="Error description if authorization failed")
):
    """
    Instagram OAuth callback endpoint
    Handles the callback from Instagram's OAuth flow.
    """
    try:
        print(f"=== CALLBACK DEBUG ===")
        print(f"Code: {code[:50]}...")  # Truncate for security
        print(f"State: {state}")
        print(f"Error: {error}")
        print(f"CLIENT_ID used: {CLIENT_ID}")
        print(f"REDIRECT_URI used: {REDIRECT_URI}")
        print(f"=== END CALLBACK DEBUG ===")
        
        # Check if there was an error in the OAuth flow
        if error:
            print(f"OAuth Error: {error} - {error_description}")
            raise HTTPException(
                status_code=400,
                detail={
                    "error": error,
                    "error_reason": error_reason,
                    "error_description": error_description,
                    "message": "Instagram authorization failed"
                }
            )
        
        # Exchange authorization code for access token
        # Since frontend uses Facebook OAuth, use Facebook's token endpoint
        token_url = "https://graph.facebook.com/v18.0/oauth/access_token"
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        # Try both redirect_uri formats - frontend sends UNENCODED via Facebook OAuth
        redirect_uris_to_try = [
            REDIRECT_URI,  # Unencoded FIRST (frontend uses Facebook OAuth which sends unencoded)
            urllib.parse.quote(REDIRECT_URI, safe=''),  # Encoded second (fallback)
        ]
        
        for i, redirect_uri_attempt in enumerate(redirect_uris_to_try, 1):
            print(f"\n=== TOKEN EXCHANGE ATTEMPT {i} ===")
            print(f"Trying redirect_uri: {redirect_uri_attempt}")
            
            # Use form data with proper headers (Instagram is picky about this)
            data = {
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri_attempt,
                "code": code
            }
            
            print(f"Token exchange request:")
            print(f"URL: {token_url}")
            print(f"Headers: {headers}")
            print(f"Data: {data}")
            
            async with httpx.AsyncClient() as client:
                resp = await client.post(token_url, data=data, headers=headers)
                
                print(f"Response status: {resp.status_code}")
                print(f"Response headers: {dict(resp.headers)}")
                print(f"Response text: {resp.text}")
                
                if resp.status_code == 200:
                    token_data = resp.json()
                    print("Token data received:")
                    print(token_data)
                    
                    # Return success page instead of JSON for better UX
                    success_html = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>Instagram OAuth Success</title>
                        <style>
                            body {{ font-family: Arial, sans-serif; margin: 40px; background: #f0f0f0; }}
                            .container {{ background: white; padding: 30px; border-radius: 10px; max-width: 600px; margin: 0 auto; }}
                            .success {{ color: #28a745; font-size: 24px; margin-bottom: 20px; }}
                            .info {{ background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0; }}
                            .token {{ font-family: monospace; word-break: break-all; background: #e9ecef; padding: 10px; border-radius: 3px; }}
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <div class="success">✅ Instagram OAuth Successful!</div>
                            
                            <div class="info">
                                <h3>Token Information:</h3>
                                <p><strong>Access Token:</strong></p>
                                <div class="token">{token_data.get("access_token", "N/A")}</div>
                                <p><strong>User ID:</strong> {token_data.get("user_id", "N/A")}</p>
                                <p><strong>Working redirect_uri:</strong> {redirect_uri_attempt}</p>
                            </div>
                            
                            <div class="info">
                                <h3>Next Steps:</h3>
                                <p>✅ OAuth flow is working correctly</p>
                                <p>✅ Your frontend should use this redirect_uri format</p>
                                <p>📝 Save the access token to your environment variables</p>
                            </div>
                            
                            <p><a href="/instagram/debug-config">View Configuration</a> | <a href="/instagram/login">Test Again</a></p>
                        </div>
                    </body>
                    </html>
                    """
                    
                    return HTMLResponse(content=success_html)
                else:
                    error_response = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {"error_message": resp.text}
                    error_message = error_response.get("error_message", "Unknown error")
                    
                    # Handle specific error cases
                    if "authorization code has been used" in error_message:
                        print(f"Attempt {i}: Authorization code already used - this is expected if we're retrying")
                        if i < len(redirect_uris_to_try):
                            continue  # Try next approach
                        else:
                            error_html = f"""
                            <!DOCTYPE html>
                            <html>
                            <head>
                                <title>Authorization Code Already Used</title>
                                <style>
                                    body {{ font-family: Arial, sans-serif; margin: 40px; background: #f0f0f0; }}
                                    .container {{ background: white; padding: 30px; border-radius: 10px; max-width: 600px; margin: 0 auto; }}
                                    .warning {{ color: #ffc107; font-size: 24px; margin-bottom: 20px; }}
                                    .info {{ background: #fff3cd; padding: 15px; border-radius: 5px; margin: 10px 0; border-left: 4px solid #ffc107; }}
                                </style>
                            </head>
                            <body>
                                <div class="container">
                                    <div class="warning">⚠️ Authorization Code Already Used</div>
                                    
                                    <div class="info">
                                        <h3>This is Normal!</h3>
                                        <p>Instagram authorization codes can only be used once. If you're seeing this error, it means:</p>
                                        <ul>
                                            <li>✅ The OAuth flow is working correctly</li>
                                            <li>✅ Your redirect URI configuration is correct</li>
                                            <li>⚠️ You tried to use the same authorization code twice</li>
                                        </ul>
                                        
                                        <h3>To get a fresh token:</h3>
                                        <p>Click the button below to start a new OAuth flow with a fresh authorization code.</p>
                                    </div>
                                    
                                    <p><a href="/instagram/login" style="background: #E4405F; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px;">Get New Authorization Code</a></p>
                                </div>
                            </body>
                            </html>
                            """
                            return HTMLResponse(content=error_html, status_code=400)
                    elif "redirect_uri" in error_message.lower():
                        print(f"Attempt {i}: Redirect URI mismatch with {redirect_uri_attempt}")
                        if i < len(redirect_uris_to_try):
                            continue  # Try next approach
                        else:
                            raise HTTPException(
                                status_code=400,
                                detail=f"Failed to exchange code for token after trying all redirect_uri formats. Last error: {error_message}"
                            )
                    else:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Failed to exchange code for token: {error_message}"
                        )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Callback error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process Instagram OAuth callback: {str(e)}"
        )

@router.get("/instagram_posts")
def get_all_instagram_posts():
    posts = instagram_service.get_all_instagram_posts()
    return posts

@router.get("/instagram_posts/{post_id}")
def get_instagram_post(post_id: int):
    post = instagram_service.get_instagram_post_by_id(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Instagram post not found")
    return post

@router.put("/instagram_posts/{post_id}")
def update_instagram_post(post_id: int, update_data: InstagramPostUpdate):
    updated = instagram_service.update_instagram_post(post_id, update_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Instagram post not found")
    return updated

@router.delete("/instagram_posts/{post_id}")
def delete_instagram_post(post_id: int):
    deleted = instagram_service.delete_instagram_post(post_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Instagram post not found")
    return {"success": True}

@router.get("/get-instagram-account")
async def get_instagram_account(access_token: str = Query(..., description="Facebook access token")):
    """
    Get Instagram Business Account ID using Facebook access token
    This is required to make Instagram API calls
    """
    try:
        # Get Facebook pages associated with this token
        pages_url = "https://graph.facebook.com/v18.0/me/accounts"
        params = {
            "fields": "instagram_business_account",
            "access_token": access_token
        }
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(pages_url, params=params)
            
            print(f"Pages response: {resp.status_code} - {resp.text}")
            
            if resp.status_code == 200:
                pages_data = resp.json()
                
                # Find Instagram business accounts
                instagram_accounts = []
                for page in pages_data.get("data", []):
                    if "instagram_business_account" in page:
                        instagram_accounts.append({
                            "page_id": page.get("id"),
                            "page_name": page.get("name"),
                            "instagram_business_account_id": page["instagram_business_account"]["id"]
                        })
                
                if instagram_accounts:
                    return {
                        "success": True,
                        "instagram_accounts": instagram_accounts,
                        "message": "Found Instagram Business Account(s)",
                        "next_step": "Save the instagram_business_account_id to your environment as INSTAGRAM_ACCOUNT_ID"
                    }
                else:
                    return {
                        "success": False,
                        "message": "No Instagram Business Accounts found. Make sure your Instagram account is connected to a Facebook Page and is a Business account.",
                        "pages_data": pages_data
                    }
            else:
                return {
                    "success": False,
                    "error": f"Failed to get pages: {resp.text}",
                    "status_code": resp.status_code
                }
                
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting Instagram account: {str(e)}"
        )

@router.post("/post-image")
async def post_instagram_image(
    access_token: str = Query(..., description="Facebook access token"),
    instagram_account_id: str = Query(..., description="Instagram Business Account ID"),
    image_url: str = Query(..., description="Public URL of the image to post"),
    caption: str = Query("", description="Caption for the post")
):
    """
    Post an image to Instagram using the user's access token
    """
    try:
        # Step 1: Create media container
        media_url = f"https://graph.facebook.com/v18.0/{instagram_account_id}/media"
        media_data = {
            "image_url": image_url,
            "caption": caption,
            "access_token": access_token
        }
        
        async with httpx.AsyncClient() as client:
            # Create media container
            media_resp = await client.post(media_url, data=media_data)
            print(f"Media creation response: {media_resp.status_code} - {media_resp.text}")
            
            if media_resp.status_code != 200:
                return {
                    "success": False,
                    "error": f"Failed to create media container: {media_resp.text}"
                }
            
            media_result = media_resp.json()
            creation_id = media_result.get("id")
            
            if not creation_id:
                return {
                    "success": False,
                    "error": "No creation ID returned from media creation"
                }
            
            # Step 2: Publish the media
            publish_url = f"https://graph.facebook.com/v18.0/{instagram_account_id}/media_publish"
            publish_data = {
                "creation_id": creation_id,
                "access_token": access_token
            }
            
            publish_resp = await client.post(publish_url, data=publish_data)
            print(f"Publish response: {publish_resp.status_code} - {publish_resp.text}")
            
            if publish_resp.status_code == 200:
                publish_result = publish_resp.json()
                return {
                    "success": True,
                    "media_id": publish_result.get("id"),
                    "creation_id": creation_id,
                    "message": "Successfully posted to Instagram!"
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to publish media: {publish_resp.text}",
                    "creation_id": creation_id
                }
                
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error posting to Instagram: {str(e)}"
        )

@router.get("/get-media")
async def get_instagram_media(
    access_token: str = Query(..., description="Facebook access token"),
    instagram_account_id: str = Query(..., description="Instagram Business Account ID"),
    limit: int = Query(10, description="Number of media items to retrieve")
):
    """
    Get Instagram media posts using the user's access token
    """
    try:
        media_url = f"https://graph.facebook.com/v18.0/{instagram_account_id}/media"
        params = {
            "fields": "id,caption,media_type,media_url,thumbnail_url,timestamp,permalink",
            "limit": limit,
            "access_token": access_token
        }
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(media_url, params=params)
            
            print(f"Media response: {resp.status_code} - {resp.text}")
            
            if resp.status_code == 200:
                media_data = resp.json()
                return {
                    "success": True,
                    "media": media_data.get("data", []),
                    "paging": media_data.get("paging", {}),
                    "count": len(media_data.get("data", []))
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to get media: {resp.text}",
                    "status_code": resp.status_code
                }
                
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting Instagram media: {str(e)}"
        )