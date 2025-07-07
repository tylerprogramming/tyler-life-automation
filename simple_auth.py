import os
import json
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Scopes for Google Calendar
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

def authenticate_google_calendar():
    """Simple authentication for Google Calendar"""
    
    print("🔐 Google Calendar Authentication")
    print("=" * 40)
    
    # Check if token already exists
    if os.path.exists('token.json'):
        print("✅ Found existing token.json")
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
        if creds.valid:
            print("✅ Token is valid!")
            return creds
        
        if creds.expired and creds.refresh_token:
            print("🔄 Refreshing expired token...")
            creds.refresh(Request())
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
            print("✅ Token refreshed!")
            return creds
    
    # Need to authenticate
    credentials_path = None
    for path in ['credentials/credentials.json', 'credentials.json']:
        if os.path.exists(path):
            credentials_path = path
            break
    
    if not credentials_path:
        print("❌ No credentials.json found!")
        print("Please place your credentials.json in one of these locations:")
        print("  - credentials/credentials.json")
        print("  - credentials.json")
        return None
    
    print(f"📄 Using credentials from: {credentials_path}")
    
    # Start OAuth flow
    flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
    
    print("\n🌐 Starting authentication...")
    print("This will open your browser for Google sign-in.")
    print("If it doesn't open automatically, copy the URL that appears.")
    
    try:
        # This will start a local server on port 8080
        creds = flow.run_local_server(port=8080, open_browser=False)
        
        # Save credentials
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
        
        print("✅ Authentication successful!")
        print("✅ Token saved to token.json")
        return creds
        
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        print("\n🔧 Make sure you have added this redirect URI in Google Cloud Console:")
        print("   http://localhost:8080")
        return None

def test_calendar_access(creds):
    """Test if calendar access works"""
    
    try:
        service = build('calendar', 'v3', credentials=creds)
        
        print("\n📅 Testing calendar access...")
        
        # Get calendar list
        calendar_list = service.calendarList().list().execute()
        calendars = calendar_list.get('items', [])
        
        print(f"✅ Found {len(calendars)} calendars")
        
        # Get some events
        events_result = service.events().list(
            calendarId='primary',
            maxResults=5,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        print(f"✅ Found {len(events)} recent events")
        
        print("\n🎉 Calendar API is working perfectly!")
        return True
        
    except Exception as e:
        print(f"❌ Calendar test failed: {e}")
        return False

def main():
    """Main function"""
    
    # Authenticate
    creds = authenticate_google_calendar()
    
    if not creds:
        print("\n❌ Authentication failed. Please check your setup.")
        return
    
    # Test access
    if test_calendar_access(creds):
        print("\n✅ SUCCESS! Your Google Calendar is now connected.")
        print("You can now use your Docker API endpoints:")
        print("  GET /google-calendar/current-month-events")
        print("  POST /google-calendar/sync-to-database")
    else:
        print("\n❌ Calendar access test failed.")

if __name__ == "__main__":
    main() 