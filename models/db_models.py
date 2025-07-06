from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, ForeignKey, Date, Time, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

Base = declarative_base()

class PlatformContent(Base):
    __tablename__ = "platform_content"
    id = Column(Integer, primary_key=True, index=True)
    research_id = Column(Integer, ForeignKey('content_results.id'), nullable=False)
    platform = Column(String, nullable=False)
    content_data = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    used = Column(Boolean, default=False)

class YouTubeTranscription(Base):
    __tablename__ = "youtube_transcriptions"
    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(String, nullable=False)
    channel_id = Column(String, nullable=False)
    transcription = Column(Text, nullable=False)
    segments = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    used = Column(Boolean, default=False)

    description = relationship("YouTubeDescription", back_populates="transcription", uselist=False, cascade="all, delete-orphan")

class YouTubeDescription(Base):
    __tablename__ = "youtube_descriptions"
    id = Column(Integer, primary_key=True, index=True)
    youtube_transcription_id = Column(Integer, ForeignKey('youtube_transcriptions.id'), nullable=False, unique=True)
    video_id = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    chapters = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    used = Column(Boolean, default=False)
    
    transcription = relationship("YouTubeTranscription", back_populates="description")
    
class ContentResult(Base):
    __tablename__ = "content_results"
    id = Column(Integer, primary_key=True, index=True)
    query = Column(String, nullable=False)
    urls = Column(JSON, nullable=False)
    scraped_content = Column(JSON, nullable=False)
    summary = Column(Text, nullable=False)
    key_highlights = Column(JSON, nullable=False)
    noteworthy_points = Column(JSON, nullable=False)
    action_items = Column(JSON, nullable=True)
    used_for_linkedin = Column(Boolean, default=False)
    used_for_youtube = Column(Boolean, default=False)
    used_for_x = Column(Boolean, default=False)
    used_for_instagram = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class InstagramPost(Base):
    __tablename__ = "instagram_posts"
    id = Column(Integer, primary_key=True, index=True)
    youtube_transcription_id = Column(Integer, ForeignKey('youtube_transcriptions.id'), nullable=False)
    post_id = Column(String, nullable=True, default=str(uuid.uuid4()))
    caption = Column(Text, nullable=False)
    image_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class TwitterPost(Base):
    __tablename__ = "twitter_posts"
    id = Column(Integer, primary_key=True, index=True)
    youtube_transcription_id = Column(Integer, ForeignKey('youtube_transcriptions.id'), nullable=False)
    tweet_id = Column(String, nullable=True, default=str(uuid.uuid4()))
    tweet = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class LinkedinPost(Base):
    __tablename__ = "linkedin_posts"
    id = Column(Integer, primary_key=True, index=True)
    youtube_transcription_id = Column(Integer, ForeignKey('youtube_transcriptions.id'), nullable=True)
    post_urn = Column(String, nullable=False, unique=True)
    commentary = Column(Text, nullable=False)
    visibility = Column(String, nullable=False, default="PUBLIC")
    author = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class CalendarEvent(Base):
    __tablename__ = "calendar_events"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    content_id = Column(Integer, nullable=False)
    research_id = Column(Integer, nullable=False)
    platform = Column(String(50), nullable=False)
    title = Column(Text, nullable=False)
    scheduled_date = Column(Date, nullable=False)
    scheduled_time = Column(Time, nullable=False)
    status = Column(String(20), default='scheduled', nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Indexes for performance
    __table_args__ = (
        Index('idx_calendar_events_date', 'scheduled_date'),
        Index('idx_calendar_events_content', 'content_id'),
        Index('idx_calendar_events_research', 'research_id'),
        Index('idx_calendar_events_platform', 'platform'),
        Index('idx_calendar_events_status', 'status'),
    )

class InstagramUser(Base):
    __tablename__ = "instagram_users"
    id = Column(Integer, primary_key=True, index=True)
    instagram_user_id = Column(String, nullable=False, unique=True)  # Instagram's user ID
    username = Column(String, nullable=False)
    account_type = Column(String, nullable=True)  # PERSONAL, BUSINESS, etc.
    media_count = Column(Integer, nullable=True)
    access_token_encrypted = Column(Text, nullable=False)  # Encrypted access token
    token_type = Column(String, nullable=False, default="long_lived")
    expires_in = Column(Integer, nullable=True)  # Token expiration in seconds
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_used_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

    # Indexes for performance
    __table_args__ = (
        Index('idx_instagram_users_instagram_id', 'instagram_user_id'),
        Index('idx_instagram_users_username', 'username'),
        Index('idx_instagram_users_active', 'is_active'),
    )

class SkoolEvent(Base):
    __tablename__ = "skool_events"
    id = Column(Integer, primary_key=True, index=True)
    event_uuid = Column(String, default=lambda: str(uuid.uuid4()), unique=True, nullable=False)
    
    # Skool API fields
    group_id = Column(String, nullable=False)  # Skool group ID
    start_time = Column(DateTime, nullable=False)  # Event start time (ISO format with timezone)
    end_time = Column(DateTime, nullable=False)  # Event end time (ISO format with timezone)
    
    # Event metadata
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    timezone = Column(String, nullable=False, default="America/New_York")
    reminder_disabled = Column(Boolean, default=False)
    cover_image = Column(String, nullable=True)  # URL to cover image
    
    # Location information (stored as JSON)
    location = Column(JSON, nullable=True)  # {"location_type": 1, "location_info": "zoom_url"}
    
    # Privacy settings (stored as JSON)
    privacy = Column(JSON, nullable=True)  # {"privacy_type": 0}
    
    # Status tracking
    status = Column(String, default='draft', nullable=False)  # draft, scheduled, posted, failed
    skool_event_id = Column(String, nullable=True)  # ID returned from Skool API after posting
    
    # API response data
    api_response = Column(JSON, nullable=True)  # Store full API response for debugging
    error_message = Column(Text, nullable=True)  # Store any error messages
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    posted_at = Column(DateTime, nullable=True)  # When the event was successfully posted to Skool
    
    # Recurring event support
    is_recurring = Column(Boolean, default=False)
    recurrence_pattern = Column(JSON, nullable=True)  # Store recurrence rules if needed
    parent_event_id = Column(Integer, ForeignKey('skool_events.id'), nullable=True)  # For recurring events
    
    # Additional metadata
    notes = Column(Text, nullable=True)  # Internal notes
    tags = Column(JSON, nullable=True)  # Array of tags for categorization
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_skool_events_group_id', 'group_id'),
        Index('idx_skool_events_start_time', 'start_time'),
        Index('idx_skool_events_status', 'status'),
        Index('idx_skool_events_created_at', 'created_at'),
        Index('idx_skool_events_uuid', 'event_uuid'),
    ) 