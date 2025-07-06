import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from ai_agents.calendar import create_calendar_events_from_text_runner
from dotenv import load_dotenv
from services import calendar as calendar_service
from services import database as database_service
from models.calendar import CalendarEventCreate, Platform, EventStatus

load_dotenv()

# If modifying these scopes, delete the token file.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

def get_google_calendar_service():
    """
    Get authenticated Google Calendar service.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens.
    if os.path.exists('credentials/token.json'):
        creds = Credentials.from_authorized_user_file('credentials/token.json', SCOPES)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Check if credentials file exists
            credentials_path = 'credentials/credentials.json'
            if not os.path.exists(credentials_path):
                credentials_path = 'credentials.json'
            
            if os.path.exists(credentials_path):
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
            else:
                raise Exception("No Google Calendar credentials found. Please add credentials.json file.")
        
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('calendar', 'v3', credentials=creds)
    return service

def get_current_month_events(calendar_id: str = 'primary', max_results: int = 50) -> List[Dict[str, Any]]:
    """
    Get all events from Google Calendar for the current month.
    
    Args:
        calendar_id: The calendar ID to fetch events from (default: 'primary')
        max_results: Maximum number of events to return
    
    Returns:
        List of calendar events
    """
    try:
        service = get_google_calendar_service()
        
        # Get the current date
        now = datetime.now()
        
        # Get the first day of the current month
        first_day = datetime(now.year, now.month, 1)
        
        # Get the first day of the next month
        if now.month == 12:
            next_month = datetime(now.year + 1, 1, 1)
        else:
            next_month = datetime(now.year, now.month + 1, 1)
        
        # Convert to RFC3339 format
        time_min = first_day.isoformat() + 'Z'
        time_max = next_month.isoformat() + 'Z'
        
        print(f'Getting events from {first_day.strftime("%Y-%m-%d")} to {next_month.strftime("%Y-%m-%d")}')
        
        # Call the Calendar API
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        # Format events for easier consumption
        formatted_events = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            
            formatted_event = {
                'id': event.get('id'),
                'summary': event.get('summary', 'No Title'),
                'description': event.get('description', ''),
                'start': start,
                'end': end,
                'location': event.get('location', ''),
                'creator': event.get('creator', {}),
                'attendees': event.get('attendees', []),
                'status': event.get('status', ''),
                'htmlLink': event.get('htmlLink', ''),
                'created': event.get('created', ''),
                'updated': event.get('updated', ''),
                'organizer': event.get('organizer', {}),
                'recurring_event_id': event.get('recurringEventId', ''),
                'original_start_time': event.get('originalStartTime', {})
            }
            formatted_events.append(formatted_event)
        
        print(f'Found {len(formatted_events)} events for the current month')
        return formatted_events
        
    except Exception as error:
        print(f'An error occurred: {error}')
        raise error

def get_upcoming_events(days_ahead: int = 7, calendar_id: str = 'primary', max_results: int = 10) -> List[Dict[str, Any]]:
    """
    Get upcoming events for the next N days.
    
    Args:
        days_ahead: Number of days to look ahead
        calendar_id: The calendar ID to fetch events from
        max_results: Maximum number of events to return
    
    Returns:
        List of upcoming calendar events
    """
    try:
        service = get_google_calendar_service()
        
        # Get current time
        now = datetime.now()
        end_time = now + timedelta(days=days_ahead)
        
        # Convert to RFC3339 format
        time_min = now.isoformat() + 'Z'
        time_max = end_time.isoformat() + 'Z'
        
        print(f'Getting upcoming events for the next {days_ahead} days')
        
        # Call the Calendar API
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        # Format events
        formatted_events = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            
            formatted_event = {
                'id': event.get('id'),
                'summary': event.get('summary', 'No Title'),
                'description': event.get('description', ''),
                'start': start,
                'end': end,
                'location': event.get('location', ''),
                'creator': event.get('creator', {}),
                'attendees': event.get('attendees', []),
                'status': event.get('status', ''),
                'htmlLink': event.get('htmlLink', ''),
            }
            formatted_events.append(formatted_event)
        
        print(f'Found {len(formatted_events)} upcoming events')
        return formatted_events
        
    except Exception as error:
        print(f'An error occurred: {error}')
        raise error

def list_calendars() -> List[Dict[str, Any]]:
    """
    Get list of all calendars accessible to the user.
    
    Returns:
        List of calendars
    """
    try:
        service = get_google_calendar_service()
        
        calendar_list = service.calendarList().list().execute()
        calendars = calendar_list.get('items', [])
        
        formatted_calendars = []
        for calendar in calendars:
            formatted_calendar = {
                'id': calendar.get('id'),
                'summary': calendar.get('summary'),
                'description': calendar.get('description', ''),
                'primary': calendar.get('primary', False),
                'access_role': calendar.get('accessRole', ''),
                'selected': calendar.get('selected', False)
            }
            formatted_calendars.append(formatted_calendar)
        
        return formatted_calendars
        
    except Exception as error:
        print(f'An error occurred: {error}')
        raise error

def sync_google_calendar_to_database(calendar_id: str = 'primary', max_results: int = 50) -> Dict[str, Any]:
    """
    Sync Google Calendar events for the current month to the database.
    
    Args:
        calendar_id: The calendar ID to fetch events from (default: 'primary')
        max_results: Maximum number of events to return
    
    Returns:
        Dictionary with sync results
    """
    try:
        # Get Google Calendar events for current month
        google_events = get_current_month_events(calendar_id, max_results)
        
        created_events = []
        skipped_events = []
        
        for google_event in google_events:
            try:
                # Parse the start datetime
                start_str = google_event['start']
                if 'T' in start_str:  # datetime format
                    start_dt = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
                    scheduled_date = start_dt.date()
                    scheduled_time = start_dt.time()
                else:  # date-only format (all-day events)
                    scheduled_date = datetime.fromisoformat(start_str).date()
                    scheduled_time = datetime.strptime("09:00", "%H:%M").time()  # Default time for all-day events
                
                # Create calendar event for database
                # Build notes carefully to stay under 1000 character limit
                event_id = google_event['id']
                description = google_event.get('description', '')
                location = google_event.get('location', '')
                
                # Calculate space available for description after other fields
                base_notes = f"Google Calendar Event ID: {event_id}\nDescription: \nLocation: {location}"
                available_space = 950 - len(base_notes)  # Leave some buffer
                
                # Truncate description if needed
                if len(description) > available_space:
                    description = description[:available_space] + "..."
                
                notes = f"Google Calendar Event ID: {event_id}\nDescription: {description}\nLocation: {location}"
                
                calendar_event_data = CalendarEventCreate(
                    content_id=-1,  # Placeholder for Google Calendar events
                    research_id=-1,  # Placeholder for Google Calendar events
                    platform=Platform.GOOGLE_CALENDAR,
                    title=google_event['summary'][:500],  # Truncate if too long
                    scheduled_date=scheduled_date,
                    scheduled_time=scheduled_time,
                    status=EventStatus.SCHEDULED,
                    notes=notes[:1000]  # Final safety truncation
                )
                
                # Check if event already exists (avoid duplicates)
                existing_events = calendar_service.get_calendar_events(
                    start_date=scheduled_date,
                    end_date=scheduled_date,
                    platform="google_calendar"
                )
                
                # Check if an event with same title and time already exists
                duplicate_found = False
                for existing_event in existing_events:
                    if (existing_event.title == calendar_event_data.title and 
                        existing_event.scheduled_time == calendar_event_data.scheduled_time and
                        google_event['id'] in existing_event.notes):
                        duplicate_found = True
                        skipped_events.append({
                            'title': google_event['summary'],
                            'date': str(scheduled_date),
                            'reason': 'Already exists in database'
                        })
                        break
                
                if not duplicate_found:
                    # Create the event in database
                    created_event = calendar_service.create_calendar_event(calendar_event_data)
                    if created_event:
                        created_events.append(created_event)
                    
            except Exception as event_error:
                print(f"Error processing event {google_event.get('summary', 'Unknown')}: {event_error}")
                skipped_events.append({
                    'title': google_event.get('summary', 'Unknown'),
                    'date': google_event.get('start', 'Unknown'),
                    'reason': f'Processing error: {str(event_error)}'
                })
                continue
        
        return {
            'total_google_events': len(google_events),
            'created_events': len(created_events),
            'skipped_events': len(skipped_events),
            'created_event_details': created_events,
            'skipped_event_details': skipped_events
        }
        
    except Exception as error:
        print(f'An error occurred during sync: {error}')
        raise error