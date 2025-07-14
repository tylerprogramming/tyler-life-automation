from fastapi import APIRouter, HTTPException, Query
from services import youtube_analytics, youtube_comments, youtube_transcription
from services import database as database_service
from models.youtube import (
    YouTubeTranscriptionUpdate, YouTubeDescriptionCreate, YouTubeOutput, YouTubeDescriptionUpdate,
    CommentCreate, CommentPin, CommentCreateAndPin, MultiChannelRequest, ReplyInfo, 
    CommentInfo, VideoInfo, VideosResponse, SavedChannelRequest
)
from ai_agents.youtube import youtube_agent_runner
import os
from dotenv import load_dotenv
from typing import Optional, List

load_dotenv()

router = APIRouter()

# All Pydantic models are now imported from models.youtube

@router.get("/get_all_transcriptions")
async def get_all_transcriptions():
    """
    Endpoint to retrieve all transcriptions.
    """
    return database_service.get_all_transcriptions()

@router.put("/update_transcription/{transcription_id}")
async def update_transcription(transcription_id: int, update_data: YouTubeTranscriptionUpdate):
    """
    Endpoint to update a transcription.
    """
    return database_service.update_transcription(transcription_id, update_data)

@router.delete("/delete_transcription/{transcription_id}")
async def delete_transcription(transcription_id: int):
    """
    Endpoint to delete a transcription.
    """
    return database_service.delete_transcription(transcription_id)

@router.get("/get_latest_youtube_video")
async def get_latest_youtube_video():
    """
    Endpoint to retrieve the latest YouTube video.
    """
    user_input = "tylerreedai"
    channel_id = youtube_analytics.get_channel_id(user_input)
    latest_video = youtube_analytics.get_latest_videos(channel_id)
    transcribed_video = youtube_transcription.process_video(latest_video[0], channel_id)
    
    database_service.insert_transcription(transcribed_video)
    
    return {"message": "Transcriptions inserted successfully"}

@router.get("/transcribe_local_video")
async def transcribe_local_video(video_path: str):
    """
    Endpoint to retrieve the latest YouTube video.
    """
    transcribed_video = youtube_transcription.transcribe_local_video(video_path)
    
    database_service.insert_transcription(transcribed_video)
    
    return {"message": "Transcriptions inserted successfully"}


@router.get("/create_youtube_description")
async def create_youtube_description():
    """
    Endpoint to create a YouTube description.
    """
    latest_youtube_transcription = database_service.check_latest_transcription()
    
    youtube_description_output = await youtube_agent_runner(latest_youtube_transcription.segments)
    print(youtube_description_output)
    
    return youtube_description_output

@router.get("/create_youtube_description/{id}")
async def create_youtube_description(id: int):
    """
    Endpoint to create a YouTube description by id.
    """
    latest_youtube_transcription = database_service.get_transcription_by_id(id)
    
    if not latest_youtube_transcription:
        raise HTTPException(status_code=404, detail="Transcription not found")
    
    youtube_description_output: YouTubeOutput = await youtube_agent_runner(latest_youtube_transcription.segments)
    
    description_to_save = YouTubeDescriptionCreate(
        youtube_transcription_id=latest_youtube_transcription.id,
        video_id=latest_youtube_transcription.video_id,
        description=youtube_description_output.description,
        chapters=youtube_description_output.chapters
    )
    
    saved_description = database_service.save_youtube_description(description_to_save)
    
    return saved_description

@router.get("/get_transcription_by_id/{transcription_id}")
async def get_transcription_by_id(transcription_id: int):
    """
    Endpoint to get a transcription by id.
    """
    youtube_transcription = database_service.get_transcription_by_id(transcription_id)
    youtube_description_output = await youtube_agent_runner(youtube_transcription.segments)
    
    return youtube_description_output

@router.post("/save_youtube_description")
async def save_youtube_description_endpoint(description_data: YouTubeDescriptionCreate):
    """
    Endpoint to save a generated YouTube description.
    """
    saved_description = database_service.save_youtube_description(description_data)
    return {"message": "Description saved successfully", "data": saved_description}

@router.get("/latest_youtube_videos")
async def latest_youtube_videos(
    max_results: int = 10, 
    include_comments: bool = True, 
    comment_limit: int = 20,
    include_sentiment: bool = True
):
    """
    Endpoint to retrieve the latest YouTube videos (excluding Shorts) with all information needed for comment creation.
    Optionally includes comments and sentiment analysis for each video.
    """
    try:
        videos = youtube_comments.get_my_channel_videos(max_results, include_comments, comment_limit)
        
        # Add sentiment summaries if requested
        if include_sentiment and videos:
            from services import database as db_service
            video_ids = [video["video_id"] for video in videos]
            sentiment_summaries = db_service.get_videos_with_sentiment_summaries(video_ids)
            
            # Add sentiment data to each video
            for video in videos:
                video_id = video["video_id"]
                if video_id in sentiment_summaries:
                    video["sentiment_analysis"] = sentiment_summaries[video_id]
                else:
                    video["sentiment_analysis"] = None
        
        return {
            "videos": videos,
            "count": len(videos),
            "include_comments": include_comments,
            "include_sentiment": include_sentiment,
            "message": f"Retrieved {len(videos)} latest videos (excluding Shorts)" + 
                      (f" with comments (limit: {comment_limit})" if include_comments else "") +
                      (f" with sentiment analysis" if include_sentiment else "")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting latest videos: {str(e)}")

@router.get("/latest_youtube_videos/{channel_id}")
async def latest_youtube_videos_by_channel(
    channel_id: str, 
    max_results: int = 10, 
    exclude_shorts: bool = False,
    include_comments: bool = False, 
    comment_limit: int = 20,
    include_sentiment: bool = True
):
    """
    Endpoint to retrieve the latest YouTube videos from a specific channel.
    Optionally excludes Shorts and includes comments and sentiment analysis for each video.
    """
    try:
        videos = youtube_comments.get_latest_videos_detailed(
            channel_id, 
            max_results, 
            exclude_shorts=exclude_shorts,
            include_comments=include_comments,
            comment_limit=comment_limit
        )
        
        # Add sentiment summaries if requested
        if include_sentiment and videos:
            from services import database as db_service
            video_ids = [video["video_id"] for video in videos]
            sentiment_summaries = db_service.get_videos_with_sentiment_summaries(video_ids)
            
            # Add sentiment data to each video
            for video in videos:
                video_id = video["video_id"]
                if video_id in sentiment_summaries:
                    video["sentiment_analysis"] = sentiment_summaries[video_id]
                else:
                    video["sentiment_analysis"] = None
        
        return {
            "videos": videos,
            "count": len(videos),
            "channel_id": channel_id,
            "exclude_shorts": exclude_shorts,
            "include_comments": include_comments,
            "include_sentiment": include_sentiment,
            "message": f"Retrieved {len(videos)} latest videos from channel {channel_id}" +
                      (f" (excluding Shorts)" if exclude_shorts else "") +
                      (f" with comments (limit: {comment_limit})" if include_comments else "") +
                      (f" with sentiment analysis" if include_sentiment else "")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting latest videos: {str(e)}")

@router.put("/update_description/{description_id}")
async def update_description_endpoint(description_id: int, update_data: YouTubeDescriptionUpdate):
    """
    Endpoint to update a YouTube description by its ID.
    """
    updated_description = database_service.update_youtube_description(description_id, update_data)
    if not updated_description:
        raise HTTPException(status_code=404, detail="Description not found")
    return updated_description

# YouTube Comment Management Endpoints

@router.get("/comments/{video_id}")
async def get_video_comments(video_id: str, max_results: int = 100):
    """
    Endpoint to get comments from a YouTube video.
    """
    try:
        comments = youtube_comments.get_video_comments(video_id, max_results)
        return {"video_id": video_id, "comments": comments}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting comments: {str(e)}")

@router.post("/comments/create")
async def create_comment_endpoint(comment_data: CommentCreate):
    """
    Endpoint to create a comment on a YouTube video.
    """
    try:
        result = youtube_comments.create_comment(comment_data.video_id, comment_data.comment_text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating comment: {str(e)}")

@router.post("/comments/pin")
async def pin_comment_endpoint(pin_data: CommentPin):
    """
    Endpoint to pin a comment to a YouTube video.
    """
    try:
        result = youtube_comments.pin_comment(pin_data.comment_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error pinning comment: {str(e)}")

@router.post("/comments/create-and-pin")
async def create_and_pin_comment_endpoint(comment_data: CommentCreateAndPin):
    """
    Endpoint to create a comment and immediately pin it to a YouTube video.
    """
    try:
        result = youtube_comments.create_and_pin_comment(comment_data.video_id, comment_data.comment_text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating and pinning comment: {str(e)}")

@router.get("/oauth/status")
async def check_oauth_status():
    """
    Endpoint to check if YouTube OAuth is properly configured.
    """
    try:
        # Try to get the OAuth service (this will check if credentials exist)
        youtube_comments.get_youtube_oauth_service()
        return {"status": "authenticated", "message": "YouTube OAuth is properly configured"}
    except Exception as e:
        return {"status": "not_authenticated", "message": str(e)}

# Multi-Channel Analysis Endpoints

@router.post("/multi-channel/analyze")
async def analyze_multiple_channels(request: MultiChannelRequest):
    """
    Analyze multiple YouTube channels and get their latest videos from the specified time period.
    Also performs outlier analysis to identify viral hits and underperforming videos.
    If no channel_urls provided, uses saved channels from the database.
    
    Body:
    - channel_urls: List of YouTube channel URLs (optional - uses saved channels if not provided)
    - days_back: Number of days to look back for videos (default: 14)
    - max_videos_per_channel: Maximum videos to fetch per channel (default: 50)
    - save_channels: Whether to save new channels to database (default: true)
    - use_saved_channels: Whether to use saved channels if no URLs provided (default: true)
    
    Example URLs supported:
    - https://www.youtube.com/channel/UCxxxxxx
    - https://www.youtube.com/@username
    - https://www.youtube.com/user/username
    - https://www.youtube.com/c/channelname
    
    Returns:
    - video_data: Raw video data from channels
    - outlier_analysis: Outlier analysis comparing last 14 days against baseline
    """
    try:
        if request.days_back < 1 or request.days_back > 365:
            raise HTTPException(status_code=400, detail="days_back must be between 1 and 365")
        
        if request.max_videos_per_channel < 1 or request.max_videos_per_channel > 100:
            raise HTTPException(status_code=400, detail="max_videos_per_channel must be between 1 and 100")
        
        # Get video data from channels
        video_results = youtube_analytics.get_videos_from_multiple_channels(
            channel_urls=request.channel_urls,
            days_back=request.days_back,
            max_videos_per_channel=request.max_videos_per_channel,
            save_channels=request.save_channels,
            use_saved_channels=request.use_saved_channels
        )
        
        # Perform outlier analysis using the already-fetched video data
        # This avoids double API calls and saves ~50% quota usage
        outlier_results = youtube_analytics.analyze_video_outliers(
            channel_urls=request.channel_urls,
            use_saved_channels=request.use_saved_channels,
            video_data=video_results  # Pass the already-fetched data
        )
        
        # Combine results
        combined_results = {
            "video_data": video_results,
            "outlier_analysis": outlier_results,
            "analysis_metadata": {
                "days_back_requested": request.days_back,
                "max_videos_per_channel": request.max_videos_per_channel,
                "save_channels": request.save_channels,
                "use_saved_channels": request.use_saved_channels,
                "outlier_analysis_period": "Last 14 days vs Days 15-28 baseline"
            }
        }
        
        return combined_results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing channels: {str(e)}")

@router.get("/multi-channel/analyze")
async def analyze_multiple_channels_get(
    channel_urls: List[str] = Query(..., description="List of YouTube channel URLs"),
    days_back: int = Query(14, description="Number of days to look back for videos"),
    max_videos_per_channel: int = Query(50, description="Maximum videos to fetch per channel")
):
    """
    GET version of multi-channel analysis. Use POST version for cleaner request format.
    
    Query parameters:
    - channel_urls: YouTube channel URLs (can specify multiple times)
    - days_back: Number of days to look back (default: 14)
    - max_videos_per_channel: Max videos per channel (default: 50)
    
    Example: /multi-channel/analyze?channel_urls=https://youtube.com/@mrbreast&channel_urls=https://youtube.com/@pewdiepie&days_back=7
    """
    try:
        request = MultiChannelRequest(
            channel_urls=channel_urls,
            days_back=days_back,
            max_videos_per_channel=max_videos_per_channel
        )
        return await analyze_multiple_channels(request)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing channels: {str(e)}")

@router.get("/channel/extract-id")
async def extract_channel_id(url: str = Query(..., description="YouTube channel URL")):
    """
    Extract channel ID from a YouTube URL for testing purposes.
    
    Supports various URL formats:
    - https://www.youtube.com/channel/UCxxxxxx
    - https://www.youtube.com/@username  
    - https://www.youtube.com/user/username
    - https://www.youtube.com/c/channelname
    """
    try:
        channel_id = youtube_analytics.extract_channel_id_from_url(url)
        
        if not channel_id:
            raise HTTPException(status_code=404, detail=f"Could not extract channel ID from URL: {url}")
        
        return {
            "original_url": url,
            "channel_id": channel_id,
            "channel_url": f"https://www.youtube.com/channel/{channel_id}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting channel ID: {str(e)}")

# Saved Channel Management Endpoints

@router.get("/saved-channels")
async def get_saved_channels(active_only: bool = True):
    """
    Get all saved YouTube channels.
    
    Query parameters:
    - active_only: Whether to only return active channels (default: true)
    """
    try:
        from services import database as db_service
        
        channels = db_service.get_saved_youtube_channels(active_only=active_only)
        
        # Convert to dictionaries for JSON response
        channel_list = []
        for channel in channels:
            channel_dict = {
                "id": channel.id,
                "channel_url": channel.channel_url,
                "channel_id": channel.channel_id,
                "channel_name": channel.channel_name,
                "subscriber_count": channel.subscriber_count,
                "description": channel.description,
                "thumbnail_url": channel.thumbnail_url,
                "is_active": channel.is_active,
                "priority": channel.priority,
                "tags": channel.tags,
                "notes": channel.notes,
                "max_videos_override": channel.max_videos_override,
                "days_back_override": channel.days_back_override,
                "total_videos_found": channel.total_videos_found,
                "last_video_count": channel.last_video_count,
                "avg_videos_per_analysis": channel.avg_videos_per_analysis,
                "created_at": channel.created_at.isoformat() if channel.created_at else None,
                "updated_at": channel.updated_at.isoformat() if channel.updated_at else None,
                "last_analyzed_at": channel.last_analyzed_at.isoformat() if channel.last_analyzed_at else None,
                "last_fetched_at": channel.last_fetched_at.isoformat() if channel.last_fetched_at else None
            }
            channel_list.append(channel_dict)
        
        return {
            "channels": channel_list,
            "count": len(channel_list),
            "active_only": active_only
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting saved channels: {str(e)}")

@router.post("/saved-channels")
async def add_saved_channel(request: SavedChannelRequest):
    """
    Add a new YouTube channel to the saved channels list.
    
    Body:
    - channel_url: YouTube channel URL
    - priority: Priority for analysis (1=highest, 5=lowest, default: 1)
    - notes: Optional notes about this channel
    - tags: Optional tags for organization
    """
    try:
        from services import database as db_service
        
        # Extract channel ID and get metadata
        channel_id = youtube_analytics.extract_channel_id_from_url(request.channel_url)
        
        if not channel_id:
            raise HTTPException(status_code=400, detail=f"Could not extract channel ID from URL: {request.channel_url}")
        
        # Get channel metadata
        metadata = youtube_analytics.get_channel_metadata(channel_id)
        
        if not metadata:
            raise HTTPException(status_code=404, detail=f"Channel not found: {channel_id}")
        
        # Save channel
        saved_channel = db_service.save_youtube_channel(
            channel_url=request.channel_url,
            channel_id=channel_id,
            channel_name=metadata.get("channel_name"),
            subscriber_count=metadata.get("subscriber_count"),
            description=metadata.get("description"),
            thumbnail_url=metadata.get("thumbnail_url"),
            tags=request.tags,
            notes=request.notes,
            priority=request.priority
        )
        
        if not saved_channel:
            raise HTTPException(status_code=500, detail="Failed to save channel")
        
        return {
            "id": saved_channel.id,
            "channel_url": saved_channel.channel_url,
            "channel_id": saved_channel.channel_id,
            "channel_name": saved_channel.channel_name,
            "subscriber_count": saved_channel.subscriber_count,
            "priority": saved_channel.priority,
            "is_active": saved_channel.is_active,
            "created_at": saved_channel.created_at.isoformat(),
            "message": "Channel saved successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving channel: {str(e)}")

@router.delete("/saved-channels")
async def remove_saved_channel(channel_url: str):
    """
    Remove a saved YouTube channel.
    
    Query parameters:
    - channel_url: URL of the channel to remove
    """
    try:
        from services import database as db_service
        
        success = db_service.delete_saved_youtube_channel(channel_url)
        
        if not success:
            raise HTTPException(status_code=404, detail="Channel not found")
        
        return {
            "channel_url": channel_url,
            "message": "Channel removed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error removing channel: {str(e)}")

@router.patch("/saved-channels/toggle")
async def toggle_saved_channel(channel_url: str):
    """
    Toggle the active status of a saved YouTube channel.
    
    Query parameters:
    - channel_url: URL of the channel to toggle
    """
    try:
        from services import database as db_service
        
        channel = db_service.toggle_saved_youtube_channel_status(channel_url)
        
        if not channel:
            raise HTTPException(status_code=404, detail="Channel not found")
        
        return {
            "channel_url": channel_url,
            "channel_name": channel.channel_name,
            "is_active": channel.is_active,
            "message": f"Channel {'activated' if channel.is_active else 'deactivated'} successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error toggling channel status: {str(e)}")

@router.patch("/saved-channels")
async def update_saved_channel(channel_url: str, update_data: dict):
    """
    Update settings for a saved YouTube channel.
    
    Query parameters:
    - channel_url: URL of the channel to update
    
    Body: Dictionary with fields to update (priority, notes, tags, etc.)
    """
    try:
        from services import database as db_service
        
        channel = db_service.update_saved_youtube_channel(channel_url, **update_data)
        
        if not channel:
            raise HTTPException(status_code=404, detail="Channel not found")
        
        return {
            "id": channel.id,
            "channel_url": channel.channel_url,
            "channel_name": channel.channel_name,
            "is_active": channel.is_active,
            "priority": channel.priority,
            "tags": channel.tags,
            "notes": channel.notes,
            "updated_at": channel.updated_at.isoformat(),
            "message": "Channel updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating channel: {str(e)}")
