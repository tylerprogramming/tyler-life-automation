from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

class SkoolEventStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    POSTED = "posted"
    FAILED = "failed"

class SkoolLocationData(BaseModel):
    location_type: int = Field(default=1, description="Location type (1 = online/URL)")
    location_info: str = Field(description="Location information (e.g., Zoom URL)")

class SkoolPrivacyData(BaseModel):
    privacy_type: int = Field(default=0, description="Privacy type (0 = public)")

class SkoolEventCreate(BaseModel):
    title: str = Field(..., description="Event title")
    start_time: datetime = Field(..., description="Event start time")
    end_time: datetime = Field(..., description="Event end time")
    description: Optional[str] = Field(None, description="Event description")
    timezone: str = Field(default="America/New_York", description="Event timezone")
    reminder_disabled: bool = Field(default=False, description="Whether reminders are disabled")
    cover_image: Optional[str] = Field(None, description="URL to cover image")
    location: Optional[SkoolLocationData] = Field(None, description="Location information")
    privacy: Optional[SkoolPrivacyData] = Field(None, description="Privacy settings")
    group_id: Optional[str] = Field(None, description="Skool group ID (uses default if not provided)")
    notes: Optional[str] = Field(None, description="Internal notes")
    tags: Optional[List[str]] = Field(None, description="Tags for categorization")

class SkoolEventUpdate(BaseModel):
    title: Optional[str] = Field(None, description="Event title")
    start_time: Optional[datetime] = Field(None, description="Event start time")
    end_time: Optional[datetime] = Field(None, description="Event end time")
    description: Optional[str] = Field(None, description="Event description")
    timezone: Optional[str] = Field(None, description="Event timezone")
    reminder_disabled: Optional[bool] = Field(None, description="Whether reminders are disabled")
    cover_image: Optional[str] = Field(None, description="URL to cover image")
    location: Optional[SkoolLocationData] = Field(None, description="Location information")
    privacy: Optional[SkoolPrivacyData] = Field(None, description="Privacy settings")
    status: Optional[SkoolEventStatus] = Field(None, description="Event status")
    notes: Optional[str] = Field(None, description="Internal notes")
    tags: Optional[List[str]] = Field(None, description="Tags for categorization")

class SkoolEventResponse(BaseModel):
    id: int = Field(..., description="Database ID")
    event_uuid: str = Field(..., description="Unique event UUID")
    group_id: str = Field(..., description="Skool group ID")
    start_time: datetime = Field(..., description="Event start time")
    end_time: datetime = Field(..., description="Event end time")
    title: str = Field(..., description="Event title")
    description: Optional[str] = Field(None, description="Event description")
    timezone: str = Field(..., description="Event timezone")
    reminder_disabled: bool = Field(..., description="Whether reminders are disabled")
    cover_image: Optional[str] = Field(None, description="URL to cover image")
    location: Optional[Dict[str, Any]] = Field(None, description="Location information")
    privacy: Optional[Dict[str, Any]] = Field(None, description="Privacy settings")
    status: SkoolEventStatus = Field(..., description="Event status")
    skool_event_id: Optional[str] = Field(None, description="Skool API event ID")
    api_response: Optional[Dict[str, Any]] = Field(None, description="Full API response")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    posted_at: Optional[datetime] = Field(None, description="Posted timestamp")
    is_recurring: bool = Field(..., description="Whether event is recurring")
    recurrence_pattern: Optional[Dict[str, Any]] = Field(None, description="Recurrence pattern")
    parent_event_id: Optional[int] = Field(None, description="Parent event ID for recurring events")
    notes: Optional[str] = Field(None, description="Internal notes")
    tags: Optional[List[str]] = Field(None, description="Tags for categorization")

    class Config:
        from_attributes = True

class SkoolEventScheduleItem(BaseModel):
    date: str = Field(..., description="Date string (e.g., 'Jul 3')")
    day: str = Field(..., description="Day string (e.g., 'Thu')")
    time: str = Field(..., description="Time string (e.g., '8 – 9 pm')")
    title: str = Field(..., description="Event title")
    description: Optional[str] = Field("", description="Event description")
    location_url: Optional[str] = Field("", description="Event location URL")

class BulkCreateRequest(BaseModel):
    events: List[SkoolEventScheduleItem] = Field(..., description="List of events to create")

class BulkCreateResponse(BaseModel):
    message: str = Field(..., description="Response message")
    created_events: List[SkoolEventResponse] = Field(..., description="List of created events")
    total_created: int = Field(..., description="Number of events created")
    failed_count: int = Field(default=0, description="Number of events that failed to create")

class SkoolEventPostResponse(BaseModel):
    message: str = Field(..., description="Response message")
    success: bool = Field(..., description="Whether the post was successful")
    event_id: int = Field(..., description="Database ID of the event")
    skool_event_id: Optional[str] = Field(None, description="Skool API event ID")

class SkoolEventDeleteResponse(BaseModel):
    message: str = Field(..., description="Response message")
    deleted_id: int = Field(..., description="ID of deleted event")

class SkoolEventQuickCreate(BaseModel):
    """Quick create model for simple event creation"""
    title: str = Field(..., description="Event title")
    date_str: str = Field(..., description="Date string like 'Jul 3'")
    time_str: str = Field(..., description="Time string like '8 – 9 pm'")
    description: Optional[str] = Field("", description="Event description")
    location_url: Optional[str] = Field("", description="Event location URL")
    duration_hours: int = Field(default=1, description="Event duration in hours")

class SkoolEventFilter(BaseModel):
    """Filter parameters for getting events"""
    status: Optional[SkoolEventStatus] = Field(None, description="Filter by status")
    start_date: Optional[str] = Field(None, description="Filter events from this date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="Filter events until this date (YYYY-MM-DD)")
    limit: int = Field(default=100, description="Maximum number of events to return") 