from pydantic import BaseModel
from typing import Optional

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