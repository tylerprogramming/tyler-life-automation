from pydantic import BaseModel

class TwitterOutput(BaseModel):
    tweet: str

class TwitterPostCreate(BaseModel):
    youtube_transcription_id: int
    tweet: str

class TwitterPostUpdate(BaseModel):
    tweet: str = None