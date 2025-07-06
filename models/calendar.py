from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, time, datetime
from enum import Enum

class EventStatus(str, Enum):
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    DRAFT = "draft"
    CANCELLED = "cancelled"

class Platform(str, Enum):
    YOUTUBE = "youtube"
    X = "x"
    INSTAGRAM = "instagram"
    LINKEDIN = "linkedin"
    GOOGLE_CALENDAR = "google_calendar"

class CalendarEventBase(BaseModel):
    content_id: int
    research_id: int
    platform: Platform
    title: str = Field(..., max_length=500)
    scheduled_date: date
    scheduled_time: time
    status: EventStatus = EventStatus.SCHEDULED
    notes: Optional[str] = Field(None, max_length=1000)

class CalendarEventCreate(CalendarEventBase):
    pass

class CalendarEventUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=500)
    scheduled_date: Optional[date] = None
    scheduled_time: Optional[time] = None
    status: Optional[EventStatus] = None
    notes: Optional[str] = Field(None, max_length=1000)

class CalendarEvent(CalendarEventBase):
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class CalendarEventOutput(BaseModel):
    calendar_events: List[CalendarEvent]

class CalendarEventResponse(BaseModel):
    message: str
    deleted_id: Optional[str] = None

# AI Scheduler Models
class SchedulingPreferences(BaseModel):
    time_slots: Optional[List[str]] = Field(None, description="Preferred time slots (HH:MM format)")
    days_between_posts: Optional[int] = Field(1, description="Days between posts", ge=1)
    avoid_weekends: Optional[bool] = Field(False, description="Avoid scheduling on weekends")

class AIScheduleRequest(BaseModel):
    content_ids: List[int] = Field(..., description="Array of content IDs to schedule")
    start_date: Optional[str] = Field(None, description="Start date for scheduling (YYYY-MM-DD)")
    preferences: Optional[SchedulingPreferences] = Field(None, description="Scheduling preferences")

class AIScheduleResponse(BaseModel):
    message: str
    scheduled_events: List[CalendarEvent]
    total_scheduled: int 