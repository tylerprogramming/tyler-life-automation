from pydantic import BaseModel

class InstagramOutput(BaseModel):
    caption: str

class InstagramPostCreate(BaseModel):
    youtube_transcription_id: int
    caption: str
    image_url: str = None

class InstagramPostUpdate(BaseModel):
    caption: str = None
    image_url: str = None