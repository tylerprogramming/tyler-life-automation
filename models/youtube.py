from pydantic import BaseModel
from typing import Optional, List

class YouTubeTranscriptionCreate(BaseModel):
    video_id: str
    channel_id: Optional[str] = None
    transcription: str
    segments: list[dict]
    used: bool = False

class YouTubeTranscriptionUpdate(BaseModel):
    video_id: Optional[str] = None
    channel_id: Optional[str] = None
    transcription: Optional[str] = None
    used: Optional[bool] = None
    
class YouTubeOutput(BaseModel):
    description: str
    chapters: list[str]

class YouTubeDescriptionCreate(BaseModel):
    youtube_transcription_id: int
    video_id: str
    description: str
    chapters: list[str]

class YouTubeDescriptionUpdate(BaseModel):
    description: Optional[str] = None
    chapters: Optional[list[str]] = None

# Comment-related models
class CommentCreate(BaseModel):
    video_id: str
    comment_text: str

class CommentPin(BaseModel):
    comment_id: str

class CommentCreateAndPin(BaseModel):
    video_id: str
    comment_text: str

class ReplyInfo(BaseModel):
    reply_id: str
    text: str
    author: str
    like_count: int
    published_at: str
    parent_id: str

class CommentInfo(BaseModel):
    comment_id: str
    text: str
    author: str
    like_count: int
    published_at: str
    can_reply: bool
    replies: List[ReplyInfo] = []
    reply_count: int = 0

# Video-related models
class VideoInfo(BaseModel):
    video_id: str
    title: str
    description: str
    published_at: str
    thumbnail: str
    channel_id: str
    channel_title: str
    duration: str
    view_count: int
    like_count: int
    comment_count: int
    tags: list
    category_id: str
    video_url: str
    comments: List[CommentInfo] = []
    comments_retrieved: int = 0
    comments_error: Optional[str] = None

class VideosResponse(BaseModel):
    videos: List[VideoInfo]
    count: int
    message: str
    include_comments: bool = False

# Multi-channel analysis models
class MultiChannelRequest(BaseModel):
    channel_urls: Optional[List[str]] = None  # Now optional - will use saved channels if None
    days_back: int = 14
    max_videos_per_channel: int = 50
    save_channels: bool = True  # Whether to save channels to database
    use_saved_channels: bool = True  # Whether to use saved channels if no URLs provided

# Saved channel models
class SavedChannelRequest(BaseModel):
    channel_url: str
    priority: int = 1
    notes: Optional[str] = None
    tags: Optional[List[str]] = None