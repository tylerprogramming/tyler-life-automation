#!/usr/bin/env python3
"""
YouTube OAuth Setup Script
This script helps you set up YouTube OAuth authentication for comment management.
"""

import os
import sys
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# YouTube OAuth Configuration
SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]
CLIENT_SECRETS_FILE = "youtube_credentials/client_secrets.json"
TOKEN_FILE = "youtube_credentials/token.json"

def setup_youtube_oauth():
    """
    Set up YouTube OAuth authentication.
    """
    print("🚀 YouTube OAuth Setup")
    print("=" * 50)
    
    # Check if credentials file exists
    if not os.path.exists(CLIENT_SECRETS_FILE):
        print(f"❌ Error: {CLIENT_SECRETS_FILE} not found!")
        print("\n📋 Setup Instructions:")
        print("1. Go to Google Cloud Console (https://console.cloud.google.com/)")
        print("2. Create a new project or select an existing one")
        print("3. Enable the YouTube Data API v3")
        print("4. Go to 'Credentials' in the left sidebar")
        print("5. Click 'Create Credentials' > 'OAuth 2.0 Client IDs'")
        print("6. Choose 'Desktop application'")
        print("7. Download the JSON file and rename it to 'youtube_credentials.json'")
        print("8. Place it in the same directory as this script")
        print("\n🔧 Required OAuth Scopes:")
        print("- https://www.googleapis.com/auth/youtube.force-ssl")
        return False
    
    print(f"✅ Found {CLIENT_SECRETS_FILE}")
    
    creds = None
    
    # Check if token already exists
    if os.path.exists(TOKEN_FILE):
        print(f"✅ Found existing {TOKEN_FILE}")
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing expired token...")
            creds.refresh(Request())
        else:
            print("🔐 Starting OAuth flow...")
            print("Your browser will open for authentication.")
            print("Please log in with the YouTube account you want to manage.")
            
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRETS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for future use
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
        print(f"✅ Saved credentials to {TOKEN_FILE}")
    
    # Test the credentials
    try:
        print("🧪 Testing YouTube API connection...")
        youtube = build('youtube', 'v3', credentials=creds)
        
        # Test API call - get channel info
        request = youtube.channels().list(part="snippet", mine=True)
        response = request.execute()
        
        if response.get("items"):
            channel = response["items"][0]["snippet"]
            print(f"✅ Successfully connected to YouTube!")
            print(f"📺 Channel: {channel['title']}")
            print(f"🆔 Channel ID: {response['items'][0]['id']}")
        else:
            print("⚠️  Warning: No channels found for this account")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing YouTube API: {e}")
        return False

def main():
    """
    Main function to run the setup process.
    """
    if setup_youtube_oauth():
        print("\n🎉 YouTube OAuth setup complete!")
        print("\nYou can now use the following API endpoints:")
        print("• GET /youtube/comments/{video_id} - Get comments from a video")
        print("• POST /youtube/comments/create - Create a comment")
        print("• POST /youtube/comments/pin - Pin a comment")
        print("• POST /youtube/comments/create-and-pin - Create and pin a comment")
        print("• GET /youtube/oauth/status - Check OAuth status")
        
        print("\n📝 Example usage:")
        print("curl -X POST http://localhost:8000/youtube/comments/create \\")
        print('  -H "Content-Type: application/json" \\')
        print('  -d \'{"video_id": "YOUR_VIDEO_ID", "comment_text": "Great video!"}\'')
        
    else:
        print("\n❌ Setup failed. Please check the instructions above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 