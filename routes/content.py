from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel
from services import content_creation as content_service
from models.content import (
    ContentCreationResult, 
    SearchQuery, 
    ContentGenerationRequest, 
    ContentSaveResponse, 
    ContentGenerationResponse, 
    SavePlatformContentRequest, 
    PlatformSaveResponse
)
from models.ai_improve import AIImproveRequest, AIImproveResponse

router = APIRouter()

@router.get("/recent-research")
def get_recent_research(limit: int = Query(5, ge=1, le=50)):
    """Get recent research results with optional limit"""
    try:
        recent_research = content_service.get_recent_research(limit)
        return recent_research
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve recent research"
        )
        
@router.get("/get_all_content")
def get_all_content():
    """Get all content results"""
    try:
        content = content_service.get_all_content()
        return content
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve content"
        )

@router.get("/get_content_by_id")
def get_content_by_id(research_id: int):
    """Get content by research ID"""
    try:
        content = content_service.get_content_by_id(research_id)
        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Content with ID {research_id} not found"
            )
        return content
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve content"
        )

@router.post("/search")
def search_content(search_query: SearchQuery):
    """
    Accepts a search query, uses an agent to find relevant URLs,
    scrapes them, and returns the structured content.
    """
    try:
        result = content_service.content_search(search_query.query)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Search failed or returned no results"
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search operation failed"
        )

@router.post("/save", response_model=ContentSaveResponse)
def save_content(content_result: ContentCreationResult):
    """Save content creation result"""
    try:
        response = content_service.save_content_result(content_result)
        if not response:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to save content"
            )
        return ContentSaveResponse(
            message="Content saved successfully",
            research_id=response.id
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save content"
        )

@router.post("/generate", response_model=ContentGenerationResponse)
async def generate_content(request: ContentGenerationRequest):
    """Generate platform-specific content"""
    try:
        created_content = await content_service.create_platform_content(request)
        if not created_content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to generate content"
            )
        return ContentGenerationResponse(
            research_id=request.research_id,
            generated_content=created_content,
            platforms_used=request.platforms
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Content generation failed"
        )

@router.post("/save-platform", response_model=PlatformSaveResponse)
def save_platform_content(request: SavePlatformContentRequest):
    """Save or update platform-specific content"""
    try:
        content_result = content_service.save_or_update_platform_content(
            research_id=request.research_id,
            platform=request.platform,
            content=request.content
        )
        if not content_result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to save platform content"
            )
        return PlatformSaveResponse(
            message=f"{request.platform.title()} content saved/updated successfully",
            content_id=content_result.id,
            platform=request.platform
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save platform content"
        )

@router.get("/platform-posts")
def get_platform_posts_route():
    """Get all platform posts with research queries"""
    try:
        posts = content_service.get_platform_posts()
        return posts
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve platform posts"
        )

@router.get("/platform-posts-only")
def get_platform_posts_only():
    """Get platform posts only (without research queries)"""
    try:
        posts = content_service.get_platform_posts_only()
        return posts
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve platform posts"
        )

@router.get("/platform-used")
def platform_used(research_id: int = Query(...), platform: str = Query(...)):
    """Check if a platform has already been used for a research ID"""
    try:
        used = content_service.check_platform_already_used(research_id, platform)
        return {"research_id": research_id, "platform": platform, "used": used}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check platform usage"
        )

@router.delete("/platform-posts/{content_id}")
def delete_platform_post_route(content_id: int):
    """Delete a platform post by ID"""
    try:
        deleted = content_service.delete_platform_post(content_id)
        if deleted:
            return {"message": f"Platform post {content_id} deleted successfully."}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Platform post {content_id} not found."
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete platform post"
        )

@router.post("/ai-improve", response_model=AIImproveResponse)
async def improve_content_with_ai(request: AIImproveRequest):
    """Improve content using AI"""
    try:
        result = await content_service.ai_improve_content(request.content_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content not found"
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI content improvement failed"
        )

@router.get("/dashboard/stats")
def dashboard_stats():
    """Get dashboard statistics"""
    try:
        stats = content_service.get_dashboard_stats()
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dashboard stats"
        )

@router.get("/dashboard/weekly")
def dashboard_weekly():
    """Get weekly dashboard data"""
    try:
        weekly_data = content_service.get_weekly_dashboard()
        return weekly_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve weekly dashboard data"
        )