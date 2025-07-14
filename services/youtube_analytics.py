from googleapiclient.discovery import build
import os
import re
from dotenv import load_dotenv
from datetime import datetime, timedelta
import dateutil.parser

load_dotenv()

API_KEY = os.getenv("YOUTUBE_API_KEY")
youtube = build("youtube", "v3", developerKey=API_KEY)

def get_latest_videos(channel_id, max_results=1):
    """Get the latest videos from a channel."""
    request = youtube.search().list(
        part="snippet",
        channelId=channel_id,
        order="date",
        type="video",
        maxResults=max_results
    )
    response = request.execute()

    videos = []
    for item in response.get("items", []):
        video_id = item["id"]["videoId"]
        title = item["snippet"]["title"]
        videos.append({"video_id": video_id, "title": title})
    
    return videos

def get_channel_id(username_or_url):
    """Retrieve the channel ID from a username or URL (legacy function)."""
    if "channel/" in username_or_url:
        # URL already contains the channel ID
        return username_or_url.split("channel/")[1].split("/")[0]
    elif "user/" in username_or_url:
        # Get ID from username
        username = username_or_url.split("user/")[1].split("/")[0]
        response = youtube.channels().list(part="id", forUsername=username).execute()
        return response["items"][0]["id"] if response["items"] else None
    else:
        # Try to get from custom URL or username directly
        response = youtube.search().list(part="snippet", q=username_or_url, type="channel", maxResults=1).execute()
        return response["items"][0]["snippet"]["channelId"] if response["items"] else None

def _parse_channel_url(url):
    """Parse YouTube URL and extract identifier with type information."""
    import re
    
    # Remove any trailing slashes and parameters
    clean_url = url.strip().rstrip('/').split('?')[0]
    
    # URL patterns with their types
    patterns = [
        (r'youtube\.com/channel/([UC][a-zA-Z0-9_-]{22})', 'channel_id'),
        (r'youtube\.com/@([a-zA-Z0-9_.-]+)', 'handle'),
        (r'youtube\.com/user/([a-zA-Z0-9_.-]+)', 'username'),
        (r'youtube\.com/c/([a-zA-Z0-9_.-]+)', 'custom'),
        (r'youtube\.com/([a-zA-Z0-9_.-]+)$', 'simple')
    ]
    
    for pattern, url_type in patterns:
        match = re.search(pattern, clean_url, re.IGNORECASE)
        if match:
            identifier = match.group(1)
            return identifier, url_type, clean_url
    
    return None, None, clean_url

def _resolve_channel_identifier(identifier, url_type):
    """Resolve channel identifier based on its type."""
    try:
        # Direct channel ID - no API call needed
        if url_type == 'channel_id' and identifier.startswith('UC') and len(identifier) == 24:
            return identifier
        
        # Handle @username and /c/ formats - use search API (100 quota)
        if url_type in ['handle', 'custom']:
            response = youtube.search().list(
                part="snippet",
                q=identifier,
                type="channel",
                maxResults=1
            ).execute()
            
            if response.get("items"):
                return response["items"][0]["snippet"]["channelId"]
        
        # Legacy username format - use channels API (1 quota)
        elif url_type == 'username':
            response = youtube.channels().list(
                part="id",
                forUsername=identifier
            ).execute()
            
            if response.get("items"):
                return response["items"][0]["id"]
        
        # Simple format - try search
        elif url_type == 'simple':
            response = youtube.search().list(
                part="snippet",
                q=identifier,
                type="channel",
                maxResults=1
            ).execute()
            
            if response.get("items"):
                return response["items"][0]["snippet"]["channelId"]
                
    except Exception as e:
        print(f"Error resolving {url_type} identifier '{identifier}': {e}")
    
    return None

def _fallback_channel_search(url):
    """Last resort: search using the entire URL as query."""
    try:
        response = youtube.search().list(
            part="snippet",
            q=url,
            type="channel",
            maxResults=1
        ).execute()
        
        if response.get("items"):
            return response["items"][0]["snippet"]["channelId"]
    except Exception as e:
        print(f"Error in fallback search for URL {url}: {e}")
    
    return None

def extract_channel_id_from_url(url):
    """Extract channel ID from various YouTube URL formats."""
    # Parse the URL to get identifier and type
    identifier, url_type, clean_url = _parse_channel_url(url)
    
    # Try to resolve the identifier if we found one
    if identifier and url_type:
        channel_id = _resolve_channel_identifier(identifier, url_type)
        if channel_id:
            return channel_id
    
    # Fallback: search using the entire URL
    return _fallback_channel_search(clean_url)

def _setup_multi_channel_analysis(channel_urls, days_back, use_saved_channels):
    """Setup and validate parameters for multi-channel analysis."""
    from datetime import datetime, timedelta
    from services import database as db_service
    
    # Get saved channels if none provided
    if not channel_urls and use_saved_channels:
        channel_urls = db_service.get_channel_urls_for_analysis(active_only=True)
        
    # Return early if no channels
    if not channel_urls:
        return None, {
            "channels": [],
            "total_videos": 0,
            "date_range": {},
            "summary": {
                "channels_processed": 0,
                "channels_successful": 0,
                "channels_failed": 0,
                "total_videos_found": 0
            },
            "message": "No channels to analyze. Please add channels first."
        }
    
    # Setup analysis parameters
    cutoff_date = datetime.now() - timedelta(days=days_back)
    
    results = {
        "channels": [],
        "total_videos": 0,
        "date_range": {
            "from": cutoff_date.isoformat(),
            "to": datetime.now().isoformat(),
            "days_back": days_back
        },
        "summary": {},
        "used_saved_channels": not channel_urls or use_saved_channels
    }
    
    return channel_urls, results

def _process_single_channel(url, cutoff_date, max_videos_per_channel, save_channels):
    """Process a single YouTube channel and return its data."""
    from datetime import datetime
    from services import database as db_service
    
    channel_data = {
        "url": url,
        "channel_id": None,
        "channel_name": None,
        "videos": [],
        "error": None,
        "saved_to_db": False
    }
    
    try:
        # Extract channel ID from URL
        channel_id = extract_channel_id_from_url(url)
        
        if not channel_id:
            channel_data["error"] = f"Could not extract channel ID from URL: {url}"
            return channel_data
        
        channel_data["channel_id"] = channel_id
        
        # Get channel metadata
        channel_metadata = get_channel_metadata(channel_id)
        
        if not channel_metadata:
            channel_data["error"] = f"Channel not found: {channel_id}"
            return channel_data
        
        # Add metadata to channel data
        channel_data.update(channel_metadata)
        
        # Save channel to database if requested
        if save_channels:
            _save_channel_to_database(url, channel_id, channel_metadata, channel_data)
        
        # Get videos from this channel
        videos = get_recent_videos_from_channel(
            channel_id, 
            cutoff_date, 
            max_videos_per_channel
        )
        
        channel_data["videos"] = videos
        channel_data["video_count"] = len(videos)
        
        # Update channel stats if saved
        if save_channels and channel_data.get("saved_to_db"):
            _update_channel_analysis_stats(url, len(videos))
    
    except Exception as e:
        channel_data["error"] = f"Error processing channel {url}: {str(e)}"
    
    return channel_data

def _save_channel_to_database(url, channel_id, metadata, channel_data):
    """Save channel information to database."""
    from services import database as db_service
    
    try:
        saved_channel = db_service.save_youtube_channel(
            channel_url=url,
            channel_id=channel_id,
            channel_name=metadata.get("channel_name"),
            subscriber_count=metadata.get("subscriber_count"),
            description=metadata.get("description"),
            thumbnail_url=metadata.get("thumbnail_url")
        )
        if saved_channel:
            channel_data["saved_to_db"] = True
    except Exception as e:
        print(f"Error saving channel to database: {e}")
        channel_data["save_error"] = str(e)

def _update_channel_analysis_stats(url, video_count):
    """Update channel analysis statistics."""
    from datetime import datetime
    from services import database as db_service
    
    try:
        db_service.update_channel_analysis_stats(
            channel_url=url,
            video_count=video_count,
            analysis_datetime=datetime.now()
        )
    except Exception as e:
        print(f"Error updating channel stats: {e}")

def _compile_channel_summary(channel_urls, results):
    """Compile summary statistics for multi-channel analysis."""
    results["summary"] = {
        "channels_processed": len(channel_urls),
        "channels_successful": len([c for c in results["channels"] if not c.get("error")]),
        "channels_failed": len([c for c in results["channels"] if c.get("error")]),
        "total_videos_found": results["total_videos"],
        "channels_saved": len([c for c in results["channels"] if c.get("saved_to_db")])
    }
    return results

def get_videos_from_multiple_channels(channel_urls=None, days_back=14, max_videos_per_channel=50, save_channels=True, use_saved_channels=True):
    """
    Get videos from multiple YouTube channels within a specified date range.
    If no channel_urls provided, uses saved channels from database.
    
    Args:
        channel_urls (list): List of YouTube channel URLs (if None, uses saved channels)
        days_back (int): Number of days to look back for videos (default: 14)
        max_videos_per_channel (int): Maximum videos to fetch per channel
        save_channels (bool): Whether to save channels to database for future use
        use_saved_channels (bool): Whether to use saved channels if no URLs provided
    
    Returns:
        dict: Results with channel info and videos
    """
    from datetime import datetime, timedelta
    
    # Setup and validate parameters
    channel_urls, results = _setup_multi_channel_analysis(
        channel_urls, days_back, use_saved_channels
    )
    
    # Return early if no channels found
    if channel_urls is None:
        return results
    
    # Calculate cutoff date for video filtering
    cutoff_date = datetime.now() - timedelta(days=days_back)
    
    # Process each channel
    for url in channel_urls:
        channel_data = _process_single_channel(
            url, cutoff_date, max_videos_per_channel, save_channels
        )
        
        # Add video count to total
        if not channel_data.get("error"):
            results["total_videos"] += len(channel_data.get("videos", []))
        
        results["channels"].append(channel_data)
    
    # Compile and return final results
    return _compile_channel_summary(channel_urls, results)

def get_channel_metadata(channel_id):
    """
    Get comprehensive metadata for a YouTube channel.
    
    Args:
        channel_id (str): YouTube channel ID
        
    Returns:
        dict: Channel metadata including name, subscriber count, description, etc.
    """
    try:
        # Get channel info
        channel_response = youtube.channels().list(
            part="snippet,statistics,brandingSettings",
            id=channel_id
        ).execute()
        
        if not channel_response.get("items"):
            return None
        
        channel_info = channel_response["items"][0]
        snippet = channel_info["snippet"]
        statistics = channel_info["statistics"]
        
        metadata = {
            "channel_name": snippet["title"],
            "description": snippet.get("description", "")[:1000],  # Limit description length
            "thumbnail_url": snippet["thumbnails"]["medium"]["url"] if "medium" in snippet["thumbnails"] else snippet["thumbnails"]["default"]["url"],
            "subscriber_count": int(statistics.get("subscriberCount", 0)),
            "video_count": int(statistics.get("videoCount", 0)),
            "view_count": int(statistics.get("viewCount", 0)),
            "custom_url": snippet.get("customUrl", ""),
            "country": snippet.get("country", ""),
            "published_at": snippet.get("publishedAt", "")
        }
        
        # Add branding info if available
        if "brandingSettings" in channel_info:
            branding = channel_info["brandingSettings"]
            if "channel" in branding:
                metadata.update({
                    "keywords": branding["channel"].get("keywords", ""),
                    "banner_url": branding.get("image", {}).get("bannerExternalUrl", "")
                })
        
        return metadata
        
    except Exception as e:
        print(f"Error getting channel metadata for {channel_id}: {e}")
        return None

def get_recent_videos_from_channel(channel_id, cutoff_date, max_results=50):
    """
    Get recent videos from a single channel within the cutoff date.
    """
    import dateutil.parser
    
    try:
        # Get videos from search (more recent videos)
        search_response = youtube.search().list(
            part="snippet",
            channelId=channel_id,
            order="date",
            type="video",
            maxResults=min(max_results, 50),  # API limit
            publishedAfter=cutoff_date.isoformat() + 'Z'
        ).execute()
        
        video_ids = [item["id"]["videoId"] for item in search_response.get("items", [])]
        
        if not video_ids:
            return []
        
        # Get detailed video information
        videos_response = youtube.videos().list(
            part="snippet,statistics,contentDetails",
            id=",".join(video_ids)
        ).execute()
        
        videos = []
        for video in videos_response.get("items", []):
            # Double-check the date (search sometimes returns older videos)
            published_date = dateutil.parser.parse(video["snippet"]["publishedAt"]).replace(tzinfo=None)
            
            if published_date >= cutoff_date:
                video_data = {
                    "video_id": video["id"],
                    "title": video["snippet"]["title"],
                    "description": video["snippet"]["description"][:500] + "..." if len(video["snippet"]["description"]) > 500 else video["snippet"]["description"],
                    "published_at": video["snippet"]["publishedAt"],
                    "thumbnail": video["snippet"]["thumbnails"]["medium"]["url"] if "medium" in video["snippet"]["thumbnails"] else video["snippet"]["thumbnails"]["default"]["url"],
                    "duration": video["contentDetails"]["duration"],
                    "view_count": int(video["statistics"].get("viewCount", 0)),
                    "like_count": int(video["statistics"].get("likeCount", 0)),
                    "comment_count": int(video["statistics"].get("commentCount", 0)),
                    "video_url": f"https://www.youtube.com/watch?v={video['id']}",
                    "tags": video["snippet"].get("tags", [])[:10],  # Limit tags
                    "category_id": video["snippet"]["categoryId"]
                }
                videos.append(video_data)
        
        # Sort by publish date (most recent first)
        videos.sort(key=lambda x: x["published_at"], reverse=True)
        
        return videos
        
    except Exception as e:
        print(f"Error getting videos from channel {channel_id}: {e}")
        return []

def get_video_details(video_id):
    """
    Get detailed information about a specific YouTube video.
    """
    try:
        response = youtube.videos().list(
            part="snippet,statistics,contentDetails",
            id=video_id
        ).execute()
        
        if not response.get("items"):
            return None
            
        video = response["items"][0]
        
        return {
            "title": video["snippet"]["title"],
            "description": video["snippet"]["description"],
            "channel_id": video["snippet"]["channelId"],
            "channel_title": video["snippet"]["channelTitle"],
            "published_at": video["snippet"]["publishedAt"],
            "thumbnail": video["snippet"]["thumbnails"]["medium"]["url"],
            "duration": video["contentDetails"]["duration"],
            "view_count": int(video["statistics"].get("viewCount", 0)),
            "like_count": int(video["statistics"].get("likeCount", 0)),
            "comment_count": int(video["statistics"].get("commentCount", 0)),
            "tags": video["snippet"].get("tags", []),
            "category_id": video["snippet"]["categoryId"],
            "video_url": f"https://www.youtube.com/watch?v={video_id}"
        }
    except Exception as e:
        print(f"Error getting video details for {video_id}: {str(e)}")
        return None

def _prepare_outlier_analysis_data(channel_urls, use_saved_channels, video_data):
    """Prepare and validate data for outlier analysis."""
    from datetime import datetime, timedelta
    import dateutil.parser
    
    # Use provided video data or fetch new data if none provided
    if video_data is None:
        video_data = get_videos_from_multiple_channels(
            channel_urls=channel_urls,
            days_back=28,
            max_videos_per_channel=100,
            save_channels=True,
            use_saved_channels=use_saved_channels
        )
    else:
        # Check if we have enough baseline data (videos older than 14 days)
        current_time = datetime.now()
        cutoff_14_days = current_time - timedelta(days=14)
        
        needs_baseline_data = False
        for channel in video_data.get("channels", []):
            if channel.get("videos"):
                baseline_count = sum(1 for video in channel["videos"] 
                                   if _get_days_since_published(video, current_time) >= 14)
                if baseline_count < 3:
                    needs_baseline_data = True
                    break
        
        # Fetch 28 days if we need more baseline data
        if needs_baseline_data:
            print("DEBUG: Provided video_data lacks sufficient baseline data, fetching 28 days...")
            video_data = get_videos_from_multiple_channels(
                channel_urls=channel_urls,
                days_back=28,
                max_videos_per_channel=100,
                save_channels=True,
                use_saved_channels=use_saved_channels
            )
    
    return video_data

def _get_days_since_published(video, current_time):
    """Get days since video was published."""
    import dateutil.parser
    try:
        published_date = dateutil.parser.parse(video["published_at"]).replace(tzinfo=None)
        return (current_time - published_date).days
    except:
        return 0

def _separate_videos_by_period(videos, current_time):
    """Separate videos into baseline (15-28 days) and analysis (1-14 days) periods."""
    baseline_videos = []
    analysis_videos = []
    
    for video in videos:
        days_since_published = _get_days_since_published(video, current_time)
        if days_since_published >= 14:
            baseline_videos.append(video)
        else:
            analysis_videos.append(video)
    
    return baseline_videos, analysis_videos

def _calculate_video_metrics(video, current_time):
    """Calculate key metrics for a video."""
    days_since_published = max(1, _get_days_since_published(video, current_time))
    
    views_per_day = video["view_count"] / days_since_published
    total_engagement = video["like_count"] + video["comment_count"]
    engagement_rate = (total_engagement / video["view_count"]) * 100 if video["view_count"] > 0 else 0
    like_ratio = (video["like_count"] / video["view_count"]) * 100 if video["view_count"] > 0 else 0
    comment_ratio = (video["comment_count"] / video["view_count"]) * 100 if video["view_count"] > 0 else 0
    
    return {
        "views_per_day": views_per_day,
        "engagement_rate": engagement_rate,
        "like_ratio": like_ratio,
        "comment_ratio": comment_ratio,
        "days_since_published": days_since_published
    }

def _calculate_baseline_statistics(baseline_videos, current_time):
    """Calculate baseline statistics from historical videos."""
    import statistics
    
    baseline_views_per_day = []
    baseline_engagement_rates = []
    baseline_like_ratios = []
    baseline_comment_ratios = []
    
    for video in baseline_videos:
        try:
            metrics = _calculate_video_metrics(video, current_time)
            baseline_views_per_day.append(metrics["views_per_day"])
            baseline_engagement_rates.append(metrics["engagement_rate"])
            baseline_like_ratios.append(metrics["like_ratio"])
            baseline_comment_ratios.append(metrics["comment_ratio"])
        except Exception as e:
            print(f"Error processing baseline video {video.get('video_id', 'unknown')}: {e}")
            continue
    
    if not baseline_views_per_day:
        return None
    
    return {
        "views_per_day": {
            "mean": statistics.mean(baseline_views_per_day),
            "median": statistics.median(baseline_views_per_day),
            "std_dev": statistics.stdev(baseline_views_per_day) if len(baseline_views_per_day) > 1 else 0
        },
        "engagement_rate": {
            "mean": statistics.mean(baseline_engagement_rates),
            "std_dev": statistics.stdev(baseline_engagement_rates) if len(baseline_engagement_rates) > 1 else 0
        },
        "like_ratio": {
            "mean": statistics.mean(baseline_like_ratios),
            "std_dev": statistics.stdev(baseline_like_ratios) if len(baseline_like_ratios) > 1 else 0
        },
        "comment_ratio": {
            "mean": statistics.mean(baseline_comment_ratios),
            "std_dev": statistics.stdev(baseline_comment_ratios) if len(baseline_comment_ratios) > 1 else 0
        },
        "baseline_video_count": len(baseline_videos)
    }

def _classify_outlier_type(views_z_score):
    """Classify outlier type and confidence level based on z-score."""
    outlier_type = "normal"
    confidence_level = "low"
    
    # Determine confidence level
    if abs(views_z_score) >= 2.5:
        confidence_level = "high"
    elif abs(views_z_score) >= 2.0:
        confidence_level = "medium"
    elif abs(views_z_score) >= 1.5:
        confidence_level = "low"
    
    # Classify outlier type
    if views_z_score >= 2.5:
        outlier_type = "viral_hit"
    elif views_z_score >= 1.5:
        outlier_type = "trending_up"
    elif views_z_score <= -2.5:
        outlier_type = "underperformer"
    elif views_z_score <= -1.5:
        outlier_type = "trending_down"
    else:
        outlier_type = "normal"
    
    return outlier_type, confidence_level

def _analyze_single_video_outlier(video, baseline_stats, current_time):
    """Analyze a single video for outlier classification."""
    metrics = _calculate_video_metrics(video, current_time)
    
    # Calculate z-scores
    views_z_score = 0
    if baseline_stats["views_per_day"]["std_dev"] > 0:
        views_z_score = (metrics["views_per_day"] - baseline_stats["views_per_day"]["mean"]) / baseline_stats["views_per_day"]["std_dev"]
    
    engagement_z_score = 0
    if baseline_stats["engagement_rate"]["std_dev"] > 0:
        engagement_z_score = (metrics["engagement_rate"] - baseline_stats["engagement_rate"]["mean"]) / baseline_stats["engagement_rate"]["std_dev"]
    
    # Classify outlier
    outlier_type, confidence_level = _classify_outlier_type(views_z_score)
    
    # Calculate percentage difference
    views_percentage_diff = ((metrics["views_per_day"] - baseline_stats["views_per_day"]["mean"]) / baseline_stats["views_per_day"]["mean"]) * 100
    
    return {
        "video_id": video["video_id"],
        "title": video["title"],
        "published_at": video["published_at"],
        "days_since_published": metrics["days_since_published"],
        "video_url": video["video_url"],
        "thumbnail": video["thumbnail"],
        "current_metrics": {
            "view_count": video["view_count"],
            "views_per_day": round(metrics["views_per_day"], 2),
            "engagement_rate": round(metrics["engagement_rate"], 3),
            "like_count": video["like_count"],
            "comment_count": video["comment_count"],
            "like_ratio": round(metrics["like_ratio"], 3),
            "comment_ratio": round(metrics["comment_ratio"], 3)
        },
        "outlier_analysis": {
            "outlier_type": outlier_type,
            "confidence_level": confidence_level,
            "views_z_score": round(views_z_score, 2),
            "engagement_z_score": round(engagement_z_score, 2),
            "views_percentage_diff": round(views_percentage_diff, 1),
            "vs_baseline": {
                "views_per_day_baseline": round(baseline_stats["views_per_day"]["mean"], 2),
                "engagement_rate_baseline": round(baseline_stats["engagement_rate"]["mean"], 3)
            }
        }
    }

def _compile_outlier_results(analysis_results):
    """Compile final summary statistics for outlier analysis."""
    for channel_analysis in analysis_results["channels"]:
        if "videos_analyzed" in channel_analysis:
            # Sort videos by outlier significance
            channel_analysis["videos_analyzed"].sort(
                key=lambda x: abs(x["outlier_analysis"]["views_z_score"]), 
                reverse=True
            )
            
            # Update summary stats
            analysis_results["analysis_summary"]["total_videos_analyzed"] += len(channel_analysis["videos_analyzed"])
            
            outliers_found = (channel_analysis["outlier_summary"]["viral_hits"] + 
                             channel_analysis["outlier_summary"]["underperformers"] +
                             channel_analysis["outlier_summary"]["trending_up"] +
                             channel_analysis["outlier_summary"]["trending_down"])
            
            analysis_results["analysis_summary"]["total_outliers_found"] += outliers_found
            
            if outliers_found > 0:
                analysis_results["analysis_summary"]["channels_with_outliers"] += 1
    
    return analysis_results

def analyze_video_outliers(channel_urls=None, use_saved_channels=True, video_data=None):
    """
    Analyze video outliers by comparing last 14 days against previous 14 days baseline.
    
    Args:
        channel_urls (list): List of YouTube channel URLs (if None, uses saved channels)
        use_saved_channels (bool): Whether to use saved channels if no URLs provided
        video_data (dict): Pre-fetched video data to analyze (if None, will fetch 28 days of data)
    
    Returns:
        dict: Outlier analysis results with channel data and outlier classifications
    """
    from datetime import datetime, timedelta
    
    # Prepare and validate data
    video_data = _prepare_outlier_analysis_data(channel_urls, use_saved_channels, video_data)
    
    if not video_data.get("channels"):
        return {
            "error": "No channels found for analysis",
            "channels": [],
            "analysis_summary": {}
        }
    
    current_time = datetime.now()
    
    analysis_results = {
        "channels": [],
        "analysis_summary": {
            "total_channels": len(video_data["channels"]),
            "channels_with_outliers": 0,
            "total_videos_analyzed": 0,
            "total_outliers_found": 0,
            "analysis_period": {
                "baseline_period": "Days 15-28",
                "analysis_period": "Days 1-14",
                "current_time": current_time.isoformat()
            }
        }
    }
    
    # Process each channel
    for channel in video_data["channels"]:
        if channel.get("error") or not channel.get("videos"):
            continue
            
        # Setup channel analysis structure
        channel_analysis = {
            "channel_id": channel["channel_id"],
            "channel_name": channel["channel_name"],
            "channel_url": channel["url"],
            "subscriber_count": channel.get("subscriber_count", 0),
            "videos_analyzed": [],
            "baseline_stats": {},
            "outlier_summary": {
                "viral_hits": 0,
                "underperformers": 0,
                "trending_up": 0,
                "trending_down": 0,
                "normal": 0
            }
        }
        
        # Separate videos into baseline and analysis periods
        baseline_videos, analysis_videos = _separate_videos_by_period(channel["videos"], current_time)
        
        # Check for sufficient baseline data
        if len(baseline_videos) < 3:
            channel_analysis["error"] = f"Not enough baseline videos ({len(baseline_videos)}). Need at least 3 videos from days 15-28."
            analysis_results["channels"].append(channel_analysis)
            continue
        
        # Calculate baseline statistics
        baseline_stats = _calculate_baseline_statistics(baseline_videos, current_time)
        
        if not baseline_stats:
            channel_analysis["error"] = "Could not calculate baseline statistics"
            analysis_results["channels"].append(channel_analysis)
            continue
        
        channel_analysis["baseline_stats"] = baseline_stats
        
        # Analyze each video from the last 14 days
        for video in analysis_videos:
            try:
                video_analysis = _analyze_single_video_outlier(video, baseline_stats, current_time)
                outlier_type = video_analysis["outlier_analysis"]["outlier_type"]
                
                channel_analysis["videos_analyzed"].append(video_analysis)
                channel_analysis["outlier_summary"][outlier_type] += 1
                
            except Exception as e:
                print(f"Error analyzing video {video.get('video_id', 'unknown')}: {e}")
                continue
        
        analysis_results["channels"].append(channel_analysis)
    
    # Compile final results with summary statistics
    return _compile_outlier_results(analysis_results) 