from services import database as database_service
from models.calendar import CalendarEventCreate, CalendarEventUpdate, AIScheduleRequest, CalendarEventOutput, CalendarEvent
from ai_agents.calendar import calendar_agent_runner, create_calendar_events_from_text_runner
from datetime import date, datetime
from typing import Optional, List
from datetime import time

def get_calendar_events(start_date: Optional[date] = None, end_date: Optional[date] = None, platform: Optional[str] = None, status: Optional[str] = None):
    """Get calendar events with optional filtering"""
    return database_service.get_calendar_events(start_date, end_date, platform, status)

def create_calendar_event(event_data: CalendarEventCreate):
    """Create a new calendar event"""
    return database_service.create_calendar_event(event_data)

def get_calendar_event_by_id(event_id: str):
    """Get a calendar event by its ID"""
    return database_service.get_calendar_event_by_id(event_id)

def update_calendar_event(event_id: str, update_data: CalendarEventUpdate):
    """Update an existing calendar event"""
    return database_service.update_calendar_event(event_id, update_data)

def delete_calendar_event(event_id: str) -> bool:
    """Delete a calendar event"""
    return database_service.delete_calendar_event(event_id)

def get_events_by_date_range(start_date: date, end_date: date, platform: Optional[str] = None):
    """Get events within a specific date range"""
    return database_service.get_events_by_date_range(start_date, end_date, platform)

def get_platform_content_by_ids(content_ids: List[int]):
    """Get platform content records for the specified content IDs with research data"""
    return database_service.get_platform_content_by_ids(content_ids)

async def ai_schedule_content(schedule_request: AIScheduleRequest) -> List:
    """
    AI-powered content scheduling
    This function will use an AI agent to intelligently schedule content
    """
    # Get platform content for the requested content_ids
    platform_content_data = get_platform_content_by_ids(schedule_request.content_ids)
    
    # Convert raw database results to readable format for AI agent
    formatted_content_data = []
    for platform_content, research_content in platform_content_data:
        content_item = {
            'content_id': platform_content.id,
            'research_id': platform_content.research_id,
            'platform': platform_content.platform,
            'content_data': platform_content.content_data,
            'used': platform_content.used,
            'created_at': str(platform_content.created_at),
            'updated_at': str(platform_content.updated_at),
            'research': {
                'query': research_content.query,
                'summary': research_content.summary,
                'key_highlights': research_content.key_highlights,
                'noteworthy_points': research_content.noteworthy_points,
                'action_items': research_content.action_items,
                'urls': research_content.urls
            }
        }
        formatted_content_data.append(content_item)
    
    # Get preferences / start date
    preferences = schedule_request.preferences
    start_date = schedule_request.start_date
    
    all_preferences = f"""
        Time slots: {preferences.time_slots}
        Days between posts: {preferences.days_between_posts}
        Avoid weekends: {preferences.avoid_weekends}
        Start date: {start_date}
    """
    
    print(f"Sending {len(formatted_content_data)} formatted content items to AI agent")
    
    # Get AI-generated calendar events with formatted data
    calendar_events_output = await calendar_agent_runner(formatted_content_data, all_preferences)
    
    print(calendar_events_output)
    
    # Extract calendar events from the output
    ai_generated_events = calendar_events_output.calendar_events
    
    # Create actual calendar events in the database
    created_events = []
    for event in ai_generated_events:
        # Create CalendarEventCreate object from the AI output
        event_create = CalendarEventCreate(
            content_id=event.content_id,
            research_id=event.research_id,
            platform=event.platform,
            title=event.title,
            scheduled_date=event.scheduled_date,
            scheduled_time=event.scheduled_time,
            status=event.status,
            notes=event.notes
        )
        
        # Save to database
        created_event = create_calendar_event(event_create)
        if created_event:
            created_events.append(created_event)
    
    print(f"AI Scheduling completed: {len(created_events)} events created")
    
    return created_events

async def create_events_from_text(text: str):
    """
    Create events from text.
    
    Returns:
        List of events
    """
    try:
        calendar_events_output = await create_calendar_events_from_text_runner(text)
        
        print(calendar_events_output)
    
        # Extract calendar events from the output
        ai_generated_events = calendar_events_output.calendar_events

        # Create actual calendar events in the database
        created_events = []
        for event in ai_generated_events:
            # Strip timezone info from scheduled_time to avoid PostgreSQL timezone errors
            scheduled_time = event.scheduled_time
            print(f"Original scheduled_time: {scheduled_time} (type: {type(scheduled_time)})")
            
            if hasattr(scheduled_time, 'tzinfo') and scheduled_time.tzinfo is not None:
                print(f"Stripping timezone: {scheduled_time.tzinfo}")
                scheduled_time = scheduled_time.replace(tzinfo=None)
                print(f"After stripping: {scheduled_time} (type: {type(scheduled_time)})")
                
            # Create CalendarEventCreate object from the AI output
            event_create = CalendarEventCreate(
                content_id=-1,
                research_id=-1,
                platform=event.platform,
                title=event.title,
                scheduled_date=event.scheduled_date,
                scheduled_time=scheduled_time,
                status=event.status,
                notes=event.notes
            )
            
            print(f"About to save event: {event.title} at {scheduled_time}")
            
            # Save to database
            created_event = database_service.create_calendar_event(event_create)
            if created_event:
                created_events.append(created_event)
            
        return created_events
    except Exception as error:
        print(f'An error occurred: {error}')
        raise error