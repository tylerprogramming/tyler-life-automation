from fastapi import APIRouter, HTTPException, Query, status
from services import calendar as calendar_service
from models.calendar import (
    CalendarEventCreate, 
    CalendarEventUpdate, 
    CalendarEvent, 
    CalendarEventResponse,
    EventStatus,
    Platform,
    AIScheduleRequest,
    AIScheduleResponse
)
from typing import Optional, List
from datetime import date

router = APIRouter()

@router.get("/events", response_model=List[CalendarEvent])
def get_calendar_events(
    start_date: Optional[str] = Query(None, description="Filter events from this date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Filter events until this date (YYYY-MM-DD)"),
    platform: Optional[Platform] = Query(None, description="Filter by platform"),
    status: Optional[EventStatus] = Query(None, description="Filter by status")
):
    """
    Get calendar events with optional filtering
    
    Query Parameters:
    - start_date: Filter events from this date (YYYY-MM-DD)
    - end_date: Filter events until this date (YYYY-MM-DD)
    - platform: Filter by platform (youtube, x, instagram, linkedin)
    - status: Filter by status (scheduled, published, draft, cancelled)
    """
    try:
        # Convert string dates to date objects if provided
        start_date_obj = date.fromisoformat(start_date) if start_date else None
        end_date_obj = date.fromisoformat(end_date) if end_date else None
        platform_str = platform.value if platform else None
        status_str = status.value if status else None
        
        events = calendar_service.get_calendar_events(
            start_date=start_date_obj,
            end_date=end_date_obj,
            platform=platform_str,
            status=status_str
        )
        return events
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format. Use YYYY-MM-DD: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve calendar events"
        )

@router.post("/events", response_model=CalendarEvent, status_code=status.HTTP_201_CREATED)
def create_calendar_event(event: CalendarEventCreate):
    """
    Create a new calendar event
    """
    try:
        created_event = calendar_service.create_calendar_event(event)
        if not created_event:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create calendar event"
            )
        return created_event
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create calendar event"
        )

@router.get("/events/range", response_model=List[CalendarEvent])
def get_events_by_date_range(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    platform: Optional[Platform] = Query(None, description="Filter by platform")
):
    """
    Get events within a specific date range
    Useful for calendar month view
    """
    try:
        start_date_obj = date.fromisoformat(start_date)
        end_date_obj = date.fromisoformat(end_date)
        platform_str = platform.value if platform else None
        
        events = calendar_service.get_events_by_date_range(
            start_date=start_date_obj,
            end_date=end_date_obj,
            platform=platform_str
        )
        return events
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format. Use YYYY-MM-DD: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve events by date range"
        )

@router.get("/events/{event_id}", response_model=CalendarEvent)
def get_calendar_event(event_id: str):
    """Get a specific calendar event by ID"""
    try:
        event = calendar_service.get_calendar_event_by_id(event_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Calendar event with ID {event_id} not found"
            )
        return event
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve calendar event"
        )

@router.put("/events/{event_id}", response_model=CalendarEvent)
def update_calendar_event(event_id: str, event: CalendarEventUpdate):
    """
    Update an existing calendar event
    """
    try:
        updated_event = calendar_service.update_calendar_event(event_id, event)
        if not updated_event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Calendar event with ID {event_id} not found"
            )
        return updated_event
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update calendar event"
        )

@router.delete("/events/{event_id}", response_model=CalendarEventResponse)
def delete_calendar_event(event_id: str):
    """
    Delete a calendar event
    """
    try:
        deleted = calendar_service.delete_calendar_event(event_id)
        if deleted:
            return CalendarEventResponse(
                message="Calendar event deleted successfully",
                deleted_id=event_id
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Calendar event with ID {event_id} not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete calendar event"
        )

@router.post("/ai-schedule", response_model=AIScheduleResponse, status_code=status.HTTP_201_CREATED)
async def ai_schedule_content(request: AIScheduleRequest):
    """
    AI-powered content scheduling
    
    Accepts an array of content IDs and scheduling preferences,
    then uses AI to optimally schedule them across the calendar.
    """
    try:
        if not request.content_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one content ID must be provided"
            )
            
        scheduled_events = await calendar_service.ai_schedule_content(request)
        
        return AIScheduleResponse(
            message=f"Successfully scheduled {len(scheduled_events)} content items",
            scheduled_events=scheduled_events,
            total_scheduled=len(scheduled_events)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI scheduling failed: {str(e)}"
        )
        
from pydantic import BaseModel

class CreateEventsRequest(BaseModel):
    text: str

@router.post("/create-events-from-text")
async def create_events_from_text(
    request: CreateEventsRequest
):
    """
    Endpoint to create events from text.
    
    Request Body (JSON):
    {
        "text": "Your text to create events from"
    }
    """
    try:
        events = await calendar_service.create_events_from_text(request.text)
        return {
            "message": f"Successfully created {len(events)} events",
            "events": events,
            "total_events": len(events)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create events from text: {str(e)}"
        )