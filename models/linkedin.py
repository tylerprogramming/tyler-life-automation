from pydantic import BaseModel

class LinkedinOutput(BaseModel):
    commentary: str

class LinkedinPostCreate(BaseModel):
    commentary: str
    image_urn: str = None
    alt_text: str = ""
    visibility: str = "PUBLIC"

class LinkedinPostUpdate(BaseModel):
    commentary: str = None
    visibility: str = None

class LinkedinPostResponse(BaseModel):
    post_urn: str
    commentary: str
    visibility: str
    author: str
    created_at: str = None