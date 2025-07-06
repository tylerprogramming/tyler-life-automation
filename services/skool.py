import requests
import os
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
from services import database as database_service
from models.db_models import SkoolEvent

load_dotenv()

# Skool API configuration
SKOOL_API_URL = "https://api.skool.com/calendar-events"
SKOOL_GROUP_ID = os.getenv("SKOOL_GROUP_ID", "ba634fbfaf9e41e9a412e2a08fe050a7")  # Default from your example
SKOOL_X_AWS_WAF_TOKEN = os.getenv("SKOOL_X_AWS_WAF_TOKEN")  # Store your WAF token securely

def get_skool_headers() -> Dict[str, str]:
    """Get the headers required for Skool API requests"""
    headers = {
        "Content-Type": "application/json",
        "Referer": "https://www.skool.com/",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
    }
    
    # Only add WAF token if it exists and is valid
    if SKOOL_X_AWS_WAF_TOKEN and SKOOL_X_AWS_WAF_TOKEN.strip():
        headers["x-aws-waf-token"] = SKOOL_X_AWS_WAF_TOKEN.strip()
    
    # Remove any headers that start with ':' (HTTP/2 pseudo-headers)
    cleaned_headers = {k: v for k, v in headers.items() if not k.startswith(':')}
    
    return cleaned_headers

def create_skool_event(
    title: str,
    start_time: datetime,
    end_time: datetime,
    description: str = "",
    location_url: str = "",
    timezone_str: str = "America/New_York",
    reminder_disabled: bool = False,
    cover_image: str = "",
    privacy_type: int = 0,
    location_type: int = 1,
    group_id: str = None,
    notes: str = "",
    tags: List[str] = None
) -> Optional[SkoolEvent]:
    """
    Create a new Skool event in the database
    
    Args:
        title: Event title
        start_time: Event start time (datetime object)
        end_time: Event end time (datetime object)
        description: Event description
        location_url: URL for the event location (e.g., Zoom link)
        timezone_str: Timezone string (default: America/New_York)
        reminder_disabled: Whether reminders are disabled
        cover_image: URL to cover image
        privacy_type: Privacy type (0 = public)
        location_type: Location type (1 = online/URL)
        group_id: Skool group ID (uses default if not provided)
        notes: Internal notes
        tags: List of tags for categorization
    
    Returns:
        Created SkoolEvent object or None if failed
    """
    # Use provided group_id or default
    final_group_id = group_id or SKOOL_GROUP_ID
    
    # Format location data
    location_data = {
        "location_type": location_type,
        "location_info": location_url
    } if location_url else None
    
    # Format privacy data
    privacy_data = {
        "privacy_type": privacy_type
    }
    
    return database_service.create_skool_event(
        title=title,
        start_time=start_time,
        end_time=end_time,
        description=description,
        location=location_data,
        privacy=privacy_data,
        timezone_str=timezone_str,
        reminder_disabled=reminder_disabled,
        cover_image=cover_image,
        group_id=final_group_id,
        notes=notes,
        tags=tags
    )

def get_skool_events(
    status: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 100
) -> List[SkoolEvent]:
    """
    Get Skool events with optional filtering
    
    Args:
        status: Filter by status (draft, scheduled, posted, failed)
        start_date: Filter events starting after this date
        end_date: Filter events starting before this date
        limit: Maximum number of events to return
    
    Returns:
        List of SkoolEvent objects
    """
    return database_service.get_skool_events(
        status=status,
        start_date=start_date,
        end_date=end_date,
        limit=limit
    )

def get_skool_event_by_id(event_id: int) -> Optional[SkoolEvent]:
    """Get a Skool event by its database ID"""
    return database_service.get_skool_event_by_id(event_id)

def update_skool_event(event_id: int, **kwargs) -> Optional[SkoolEvent]:
    """
    Update a Skool event
    
    Args:
        event_id: Database ID of the event
        **kwargs: Fields to update
    
    Returns:
        Updated SkoolEvent object or None if failed
    """
    return database_service.update_skool_event(event_id, **kwargs)

def delete_skool_event(event_id: int) -> bool:
    """Delete a Skool event from the database"""
    return database_service.delete_skool_event(event_id)

def format_event_for_skool_api(event: SkoolEvent) -> Dict[str, Any]:
    """
    Format a SkoolEvent object for the Skool API payload
    
    Args:
        event: SkoolEvent object
    
    Returns:
        Dictionary formatted for Skool API
    """
    # Format datetime to ISO string with timezone
    start_time_str = event.start_time.strftime("%Y-%m-%dT%H:%M:%S-04:00")  # Assuming Eastern time
    end_time_str = event.end_time.strftime("%Y-%m-%dT%H:%M:%S-04:00")
    
    payload = {
        "group_id": event.group_id,
        "start_time": start_time_str,
        "end_time": end_time_str,
        "metadata": {
            "title": event.title,
            "description": event.description or "",
            "timezone": event.timezone,
            "reminder_disabled": 1 if event.reminder_disabled else 0,
            "cover_image": event.cover_image or "",
            "location": event.location or {"location_type": 1, "location_info": ""},
            "privacy": event.privacy or {"privacy_type": 0}
        }
    }
    
    return payload

async def post_event_to_skool(event_id: int) -> bool:
    """
    Post a Skool event to the Skool API
    
    Args:
        event_id: Database ID of the event to post
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Get the event from database
        event = get_skool_event_by_id(event_id)
        if not event:
            print(f"Event with ID {event_id} not found")
            return False
        
        # Format for API
        payload = format_event_for_skool_api(event)
        headers = get_skool_headers()
        
        # Debug: Print headers and payload (remove in production)
        print(f"Headers: {headers}")
        print(f"Payload: {payload}")
        
        # Validate headers before making request
        for key, value in headers.items():
            if not key or not isinstance(key, str) or key.startswith(':'):
                raise ValueError(f"Invalid header key: {key}")
            if value is None or not isinstance(value, str):
                raise ValueError(f"Invalid header value for {key}: {value}")
        
        # Make API request
        response = requests.post(SKOOL_API_URL, json=payload, headers=headers)
        
        # Handle response
        if response.status_code == 200:
            response_data = response.json()
            
            # Update event status and store API response
            update_skool_event(
                event_id,
                status='posted',
                api_response=response_data,
                posted_at=datetime.now(timezone.utc),
                skool_event_id=response_data.get('id', '')
            )
            
            print(f"Successfully posted event to Skool: {event.title}")
            return True
        else:
            # Update event with error
            error_message = f"API error {response.status_code}: {response.text}"
            update_skool_event(
                event_id,
                status='failed',
                error_message=error_message
            )
            
            print(f"Failed to post event to Skool: {error_message}")
            return False
            
    except requests.exceptions.InvalidHeader as e:
        error_message = f"Invalid header error: {str(e)}"
        print(f"Header validation failed: {error_message}")
        update_skool_event(
            event_id,
            status='failed',
            error_message=error_message
        )
        return False
    except Exception as e:
        error_message = f"Exception posting to Skool: {str(e)}"
        update_skool_event(
            event_id,
            status='failed',
            error_message=error_message
        )
        print(error_message)
        return False

def create_event_from_schedule_data(
    date_str: str,
    day_str: str,
    time_str: str,
    title: str,
    description: str = "",
    location_url: str = "",
    duration_hours: int = 1
) -> Optional[SkoolEvent]:
    """
    Create a Skool event from schedule data like your examples
    
    Args:
        date_str: Date string like "Jul 3"
        day_str: Day string like "Thu"
        time_str: Time string like "8 – 9 pm"
        title: Event title
        description: Event description
        location_url: URL for the event location
        duration_hours: Event duration in hours (default: 1)
    
    Returns:
        Created SkoolEvent object or None if failed
    """
    try:
        # Parse the date and time
        # Note: This is a simplified parser - you might want to make it more robust
        current_year = datetime.now().year
        
        # Parse date like "Jul 3"
        month_day = date_str.split()
        month_name = month_day[0]
        day = int(month_day[1])
        
        # Convert month name to number
        month_map = {
            'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
            'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
        }
        month = month_map.get(month_name, 1)
        
        # Parse time like "8 – 9 pm" or "4 – 5 pm"
        time_parts = time_str.replace('–', '-').split(' - ')
        start_time_str = time_parts[0].strip()
        
        # Extract hour and convert to 24-hour format
        if 'pm' in time_str and not start_time_str.startswith('12'):
            hour = int(start_time_str) + 12
        elif 'am' in time_str and start_time_str.startswith('12'):
            hour = 0
        else:
            hour = int(start_time_str)
        
        # Create datetime objects
        start_time = datetime(current_year, month, day, hour, 0, 0)
        end_time = datetime(current_year, month, day, hour + duration_hours, 0, 0)
        
        # Create the event
        return create_skool_event(
            title=title,
            start_time=start_time,
            end_time=end_time,
            description=description,
            location_url=location_url
        )
        
    except Exception as e:
        print(f"Error creating event from schedule data: {str(e)}")
        return None

def bulk_create_events_from_schedule(schedule_data: List[Dict[str, str]]) -> List[SkoolEvent]:
    """
    Create multiple Skool events from a list of schedule data
    
    Args:
        schedule_data: List of dictionaries with keys: date, day, time, title, description, location_url
    
    Returns:
        List of created SkoolEvent objects
    """
    created_events = []
    
    for item in schedule_data:
        event = create_event_from_schedule_data(
            date_str=item['date'],
            day_str=item['day'],
            time_str=item['time'],
            title=item['title'],
            description=item.get('description', ''),
            location_url=item.get('location_url', '')
        )
        
        if event:
            created_events.append(event)
    
    return created_events 