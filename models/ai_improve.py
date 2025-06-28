from pydantic import BaseModel
from typing import List, Union

class YouTubeImproved(BaseModel):
    description: str

class TwitterReplyImproved(BaseModel):
    reply_tweet: str

class TwitterImproved(BaseModel):
    tweet: str
    reply_tweets: List[TwitterReplyImproved] = []

class InstagramImproved(BaseModel):
    caption: str

class LinkedinImproved(BaseModel):
    commentary: str

class AIImproveRequest(BaseModel):
    content_id: int

class AIImproveResponse(BaseModel):
    message: str
    improved_content: Union[YouTubeImproved, TwitterImproved, InstagramImproved, LinkedinImproved]
    content_id: int 