from fastapi import APIRouter, HTTPException, Query
from services import google_calendar as google_calendar_service
from typing import Optional, List, Dict, Any
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

@router.get("/current-month-events")
async def get_current_month_events(
    calendar_id: Optional[str] = Query("primary", description="Calendar ID to fetch events from"),
    max_results: Optional[int] = Query(50, description="Maximum number of events to return")
):
    """
    Endpoint to retrieve all Google Calendar events for the current month.
    
    Query Parameters:
    - calendar_id: The calendar ID to fetch events from (default: 'primary')
    - max_results: Maximum number of events to return (default: 50)
    """
    try:
        events = google_calendar_service.get_current_month_events(
            calendar_id=calendar_id,
            max_results=max_results
        )
        
        return {
            "message": f"Successfully retrieved {len(events)} events for the current month",
            "events": events,
            "total_events": len(events)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve calendar events: {str(e)}"
        )

@router.get("/upcoming-events")
async def get_upcoming_events(
    days_ahead: Optional[int] = Query(7, description="Number of days to look ahead"),
    calendar_id: Optional[str] = Query("primary", description="Calendar ID to fetch events from"),
    max_results: Optional[int] = Query(10, description="Maximum number of events to return")
):
    """
    Endpoint to retrieve upcoming Google Calendar events.
    
    Query Parameters:
    - days_ahead: Number of days to look ahead (default: 7)
    - calendar_id: The calendar ID to fetch events from (default: 'primary')
    - max_results: Maximum number of events to return (default: 10)
    """
    try:
        events = google_calendar_service.get_upcoming_events(
            days_ahead=days_ahead,
            calendar_id=calendar_id,
            max_results=max_results
        )
        
        return {
            "message": f"Successfully retrieved {len(events)} upcoming events for the next {days_ahead} days",
            "events": events,
            "total_events": len(events),
            "days_ahead": days_ahead
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve upcoming events: {str(e)}"
        )

@router.get("/calendars")
async def list_calendars():
    """
    Endpoint to retrieve all accessible Google Calendars.
    """
    try:
        calendars = google_calendar_service.list_calendars()
        
        return {
            "message": f"Successfully retrieved {len(calendars)} calendars",
            "calendars": calendars,
            "total_calendars": len(calendars)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve calendars: {str(e)}"
        )

@router.get("/events-by-calendar/{calendar_id}")
async def get_events_by_calendar(
    calendar_id: str,
    max_results: Optional[int] = Query(50, description="Maximum number of events to return")
):
    """
    Endpoint to retrieve current month events from a specific calendar.
    
    Path Parameters:
    - calendar_id: The specific calendar ID to fetch events from
    
    Query Parameters:
    - max_results: Maximum number of events to return (default: 50)
    """
    try:
        events = google_calendar_service.get_current_month_events(
            calendar_id=calendar_id,
            max_results=max_results
        )
        
        return {
            "message": f"Successfully retrieved {len(events)} events for calendar {calendar_id}",
            "calendar_id": calendar_id,
            "events": events,
            "total_events": len(events)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve events for calendar {calendar_id}: {str(e)}"
        )

@router.post("/sync-to-database")
async def sync_google_calendar_to_database(
    calendar_id: Optional[str] = Query("primary", description="Calendar ID to sync from"),
    max_results: Optional[int] = Query(50, description="Maximum number of events to sync")
):
    """
    🔄 SYNC BUTTON: Sync Google Calendar events for the current month to the database.
    
    This endpoint fetches all Google Calendar events for the current month and integrates 
    them into your calendar database table. It avoids duplicates and provides detailed results.
    
    Query Parameters:
    - calendar_id: The calendar ID to sync from (default: 'primary')
    - max_results: Maximum number of events to sync (default: 50)
    """
    try:
        sync_results = google_calendar_service.sync_google_calendar_to_database(
            calendar_id=calendar_id,
            max_results=max_results
        )
        
        return {
            "message": f"✅ Sync completed successfully!",
            "summary": {
                "total_google_events_found": sync_results['total_google_events'],
                "events_created_in_database": sync_results['created_events'],
                "events_skipped": sync_results['skipped_events']
            },
            "detailed_results": sync_results,
            "calendar_id": calendar_id
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to sync Google Calendar events to database: {str(e)}"
        ) 