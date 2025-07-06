from pydantic import BaseModel

class TwitterReply(BaseModel):
    reply_tweet: str

class TwitterOutput(BaseModel):
    tweet: str
    reply_tweets: list[TwitterReply]

class TwitterPostCreate(BaseModel):
    youtube_transcription_id: int
    tweet: str

class TwitterPostUpdate(BaseModel):
    tweet: str = None