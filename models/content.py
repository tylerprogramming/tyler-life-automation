from pydantic import BaseModel, Field
from typing import List, Optional, Union
from models.twitter import TwitterOutput
from models.instagram import InstagramOutput
from models.linkedin import LinkedinOutput

class ScrapeURLs(BaseModel):
    """A Pydantic model to validate the output of the URL selection agent."""
    urls: List[str] = Field(..., description="A list of URLs to be scraped.")

class ScrapedData(BaseModel):
    """A Pydantic model to hold the scraped content for a single URL."""
    url: str = Field(..., description="The URL of the scraped page.")
    markdown: str = Field(..., description="The scraped content in Markdown format.")

class ContentCreationResult(BaseModel):
    """The final, structured output containing the selected URLs and their content."""
    query: str = Field(..., description="The original search query or instruction that led to this content retrieval.")
    urls: List[str] = Field(..., description="The list of URLs that were selected for scraping.")
    scraped_content: List[ScrapedData] = Field(..., description="A list of objects, each containing a URL and its scraped markdown content.")

    summary: str = Field(..., description="A well-written paragraph summarizing the overall content of the scraped websites.")
    key_highlights: List[str] = Field(
        default_factory=list,
        description="A list of the most important facts, statistics, or ideas extracted from the content."
    )
    noteworthy_points: List[str] = Field(
        default_factory=list,
        description="Interesting, surprising, or recurring themes found across the websites."
    )
    action_items: Optional[List[str]] = Field(
        default=None,
        description="Suggested actions or follow-up steps derived from the content, if applicable."
    )
    used_for_youtube: bool = False
    used_for_x: bool = False
    used_for_instagram: bool = False
    used_for_linkedin: bool = False
    
class SearchQuery(BaseModel):
    query: str
    
class ContentGenerationRequest(BaseModel):
    query: str
    summary: str
    key_highlights: List[str]
    noteworthy_points: List[str]
    action_items: Optional[List[str]] = None
    platforms: List[str] = Field(..., description="List of platforms: youtube, x, instagram, linkedin")

class PlatformContentResponse(BaseModel):
    youtube: Optional[str] = None
    x_content: Optional[TwitterOutput] = None
    instagram_content: Optional[InstagramOutput] = None
    linkedin_content: Optional[LinkedinOutput] = None
    
class ContentSaveResponse(BaseModel):
    message: str
    research_id: int
    
class ContentGenerationRequest(BaseModel):
    research_id: int
    platforms: List[str] = Field(..., description="List of platforms: youtube, x, instagram, linkedin")
    
class ContentGenerationResponse(BaseModel):
    research_id: int
    generated_content: PlatformContentResponse
    platforms_used: List[str]
    
class SavePlatformContentRequest(BaseModel):
    research_id: int
    platform: str  # "youtube", "x", "instagram", "linkedin"
    content: Union[str, TwitterOutput, InstagramOutput, LinkedinOutput]
    
class PlatformSaveResponse(BaseModel):
    message: str
    content_id: int
    platform: str

