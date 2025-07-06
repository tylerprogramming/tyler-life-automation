from fastapi import APIRouter, HTTPException, Query, status, BackgroundTasks
from services import skool as skool_service
from models.skool import (
    SkoolEventCreate,
    SkoolEventUpdate,
    SkoolEventResponse,
    SkoolEventStatus,
    BulkCreateRequest,
    BulkCreateResponse,
    SkoolEventPostResponse,
    SkoolEventDeleteResponse,
    SkoolEventQuickCreate,
    SkoolEventFilter
)
from typing import Optional, List
from datetime import datetime

router = APIRouter()

@router.get("/events", response_model=List[SkoolEventResponse])
def get_skool_events(
    status: Optional[SkoolEventStatus] = Query(None, description="Filter by status"),
    start_date: Optional[str] = Query(None, description="Filter events from this date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Filter events until this date (YYYY-MM-DD)"),
    limit: int = Query(100, description="Maximum number of events to return")
):
    """
    Get Skool events with optional filtering
    
    Query Parameters:
    - status: Filter by status (draft, scheduled, posted, failed)
    - start_date: Filter events from this date (YYYY-MM-DD)
    - end_date: Filter events until this date (YYYY-MM-DD)
    - limit: Maximum number of events to return
    """
    try:
        # Convert string dates to datetime objects if provided
        start_date_obj = datetime.fromisoformat(start_date) if start_date else None
        end_date_obj = datetime.fromisoformat(end_date) if end_date else None
        status_str = status.value if status else None
        
        events = skool_service.get_skool_events(
            status=status_str,
            start_date=start_date_obj,
            end_date=end_date_obj,
            limit=limit
        )
        
        # Convert to response models
        return [SkoolEventResponse.from_orm(event) for event in events]
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format. Use YYYY-MM-DD: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve Skool events"
        )

@router.post("/events", response_model=SkoolEventResponse, status_code=status.HTTP_201_CREATED)
def create_skool_event(event: SkoolEventCreate):
    """
    Create a new Skool event
    """
    try:
        # Convert location and privacy objects to dictionaries
        location_dict = event.location.dict() if event.location else None
        privacy_dict = event.privacy.dict() if event.privacy else None
        
        created_event = skool_service.create_skool_event(
            title=event.title,
            start_time=event.start_time,
            end_time=event.end_time,
            description=event.description or "",
            location_url=location_dict.get('location_info', '') if location_dict else '',
            timezone_str=event.timezone,
            reminder_disabled=event.reminder_disabled,
            cover_image=event.cover_image or "",
            privacy_type=privacy_dict.get('privacy_type', 0) if privacy_dict else 0,
            location_type=location_dict.get('location_type', 1) if location_dict else 1,
            group_id=event.group_id,
            notes=event.notes or "",
            tags=event.tags or []
        )
        
        if not created_event:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create Skool event"
            )
        
        return SkoolEventResponse.from_orm(created_event)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create Skool event: {str(e)}"
        )

@router.post("/events/quick", response_model=SkoolEventResponse, status_code=status.HTTP_201_CREATED)
def create_skool_event_quick(event: SkoolEventQuickCreate):
    """
    Quick create a Skool event from schedule format
    """
    try:
        created_event = skool_service.create_event_from_schedule_data(
            date_str=event.date_str,
            day_str="",  # Not needed for parsing
            time_str=event.time_str,
            title=event.title,
            description=event.description,
            location_url=event.location_url,
            duration_hours=event.duration_hours
        )
        
        if not created_event:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create Skool event from schedule data"
            )
        
        return SkoolEventResponse.from_orm(created_event)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create Skool event: {str(e)}"
        )

@router.post("/events/bulk", response_model=BulkCreateResponse, status_code=status.HTTP_201_CREATED)
def bulk_create_skool_events(request: BulkCreateRequest):
    """
    Create multiple Skool events from schedule data
    """
    try:
        # Convert to format expected by service
        schedule_data = []
        for event in request.events:
            schedule_data.append({
                'date': event.date,
                'day': event.day,
                'time': event.time,
                'title': event.title,
                'description': event.description,
                'location_url': event.location_url
            })
        
        created_events = skool_service.bulk_create_events_from_schedule(schedule_data)
        
        response_events = [SkoolEventResponse.from_orm(event) for event in created_events]
        failed_count = len(request.events) - len(created_events)
        
        return BulkCreateResponse(
            message=f"Successfully created {len(created_events)} out of {len(request.events)} events",
            created_events=response_events,
            total_created=len(created_events),
            failed_count=failed_count
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bulk create Skool events: {str(e)}"
        )

@router.get("/events/{event_id}", response_model=SkoolEventResponse)
def get_skool_event(event_id: int):
    """Get a specific Skool event by ID"""
    try:
        event = skool_service.get_skool_event_by_id(event_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Skool event with ID {event_id} not found"
            )
        
        return SkoolEventResponse.from_orm(event)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve Skool event"
        )

@router.put("/events/{event_id}", response_model=SkoolEventResponse)
def update_skool_event(event_id: int, event: SkoolEventUpdate):
    """
    Update an existing Skool event
    """
    try:
        # Prepare update data
        update_data = {}
        
        for field, value in event.dict(exclude_unset=True).items():
            if field == 'location' and value:
                update_data['location'] = value
            elif field == 'privacy' and value:
                update_data['privacy'] = value
            elif field == 'status' and value:
                update_data['status'] = value.value
            elif value is not None:
                update_data[field] = value
        
        updated_event = skool_service.update_skool_event(event_id, **update_data)
        
        if not updated_event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Skool event with ID {event_id} not found"
            )
        
        return SkoolEventResponse.from_orm(updated_event)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update Skool event: {str(e)}"
        )

@router.delete("/events/{event_id}", response_model=SkoolEventDeleteResponse)
def delete_skool_event(event_id: int):
    """
    Delete a Skool event
    """
    try:
        deleted = skool_service.delete_skool_event(event_id)
        if deleted:
            return SkoolEventDeleteResponse(
                message="Skool event deleted successfully",
                deleted_id=event_id
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Skool event with ID {event_id} not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete Skool event"
        )

@router.post("/events/{event_id}/post", response_model=SkoolEventPostResponse)
async def post_skool_event_to_api(event_id: int, background_tasks: BackgroundTasks):
    """
    Post a Skool event to the Skool API
    """
    try:
        # Verify event exists
        event = skool_service.get_skool_event_by_id(event_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Skool event with ID {event_id} not found"
            )
        
        # Check if already posted
        if event.status == 'posted':
            return SkoolEventPostResponse(
                message="Event already posted to Skool",
                success=True,
                event_id=event_id,
                skool_event_id=event.skool_event_id
            )
        
        # Post to Skool API
        success = await skool_service.post_event_to_skool(event_id)
        
        # Get updated event
        updated_event = skool_service.get_skool_event_by_id(event_id)
        
        return SkoolEventPostResponse(
            message="Successfully posted event to Skool" if success else "Failed to post event to Skool",
            success=success,
            event_id=event_id,
            skool_event_id=updated_event.skool_event_id if updated_event else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to post event to Skool: {str(e)}"
        )

@router.post("/events/batch-post")
async def batch_post_skool_events(
    status_filter: SkoolEventStatus = Query(SkoolEventStatus.DRAFT, description="Status of events to post"),
    limit: int = Query(10, description="Maximum number of events to post")
):
    """
    Post multiple Skool events to the Skool API in batch
    """
    try:
        # Get events with specified status
        events = skool_service.get_skool_events(
            status=status_filter.value,
            limit=limit
        )
        
        if not events:
            return {
                "message": f"No events found with status '{status_filter.value}'",
                "total_posted": 0,
                "successful": [],
                "failed": []
            }
        
        successful = []
        failed = []
        
        # Post each event
        for event in events:
            try:
                success = await skool_service.post_event_to_skool(event.id)
                if success:
                    successful.append(event.id)
                else:
                    failed.append(event.id)
            except Exception as e:
                print(f"Failed to post event {event.id}: {str(e)}")
                failed.append(event.id)
        
        return {
            "message": f"Batch posting completed. {len(successful)} successful, {len(failed)} failed",
            "total_posted": len(successful),
            "successful": successful,
            "failed": failed
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to batch post events: {str(e)}"
        ) 