from googleapiclient.discovery import build
import os
import re
from dotenv import load_dotenv
from openai import OpenAI
import yt_dlp
from models.youtube import YouTubeTranscriptionCreate
import json 
from services import database as database_service
from ai_agents.youtube import youtube_agent_runner
from moviepy import VideoFileClip
from datetime import datetime, timedelta
import dateutil.parser

# YouTube OAuth imports
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

load_dotenv()

API_KEY = os.getenv("YOUTUBE_API_KEY")

youtube = build("youtube", "v3", developerKey=API_KEY)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# YouTube OAuth Configuration
SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]
CLIENT_SECRETS_FILE = "credentials/client_secrets.json"
CLIENT_TOKEN_FILE = "credentials/token.json"

# Function to get the latest videos from a channel
def get_latest_videos(channel_id, max_results=1):
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

def download_youtube_video(url, output_path="."):
    """Downloads a YouTube video to a specified location.

    Args:
        url: The YouTube video URL.
        output_path: The directory to save the video (default: current directory).
    """
    ydl_opts = {
        'outtmpl': f'{output_path}/%(title)s-%(id)s.%(ext)s',  # Customize the filename
        'format': 'bestvideo+bestaudio/best', # Try best quality video and audio, defaults to MP4 if available
        'noplaylist': True,  # Download only the video, not entire playlists
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print(f"Downloaded video from {url} to {output_path}")
    except yt_dlp.utils.DownloadError as e:
        print(f"Download error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# Function to transcribe and process video
def transcribe_video(video_id):
    # Download the video using yt-dlp
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'temp_audio.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])

    # Use OpenAI to process the transcription
    with open("temp_audio.mp3", "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="verbose_json",
            timestamp_granularities=["segment"]
        )
        
    print(transcription)
    
    segment_data = [
        {"start": s.start, "end": s.end, "text": s.text}
        for s in transcription.segments
    ]
    
    print(segment_data)
    
    # Clean up temporary files
    os.remove("temp_audio.mp3")

    return YouTubeTranscriptionCreate(
        video_id=video_id,
        channel_id='',
        transcription=transcription.text,
        segments=segment_data,
        used=False
    )
    
# Function to transcribe and process video
def transcribe_local_video(video_filename):
    file_path = f"/app/videos/{video_filename}"
    # Load your MP4 file
    video = VideoFileClip(file_path)

    # Extract and write the audio to MP3
    video.audio.write_audiofile("temp_audio.mp3")
    
    # Use OpenAI to process the transcription
    with open("temp_audio.mp3", "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="verbose_json",
            timestamp_granularities=["segment"]
        )
        
    print(transcription)
    
    segment_data = [
        {"start": s.start, "end": s.end, "text": s.text}
        for s in transcription.segments
    ]
    
    print(segment_data)
    
    # Clean up temporary files
    os.remove("temp_audio.mp3")

    return YouTubeTranscriptionCreate(
        video_id=video_filename,
        channel_id='',
        transcription=transcription.text,
        segments=segment_data,
        used=False
    )

def get_channel_id(username_or_url):
    """Retrieve the channel ID from a username or URL."""
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

def extract_channel_id_from_url(url):
    """Extract channel ID from various YouTube URL formats."""
    import re
    
    # Remove any trailing slashes and parameters
    url = url.strip().rstrip('/').split('?')[0]
    
    # Handle different URL formats
    patterns = [
        # Direct channel ID: https://www.youtube.com/channel/UCxxxxxx
        r'youtube\.com/channel/([UC][a-zA-Z0-9_-]{22})',
        
        # Handle @username format: https://www.youtube.com/@username
        r'youtube\.com/@([a-zA-Z0-9_.-]+)',
        
        # User format: https://www.youtube.com/user/username
        r'youtube\.com/user/([a-zA-Z0-9_.-]+)',
        
        # Custom channel format: https://www.youtube.com/c/channelname
        r'youtube\.com/c/([a-zA-Z0-9_.-]+)',
        
        # Simple format: youtube.com/channelname
        r'youtube\.com/([a-zA-Z0-9_.-]+)$'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url, re.IGNORECASE)
        if match:
            identifier = match.group(1)
            
            # If it's already a channel ID (starts with UC), return it
            if identifier.startswith('UC') and len(identifier) == 24:
                return identifier
            
            # Otherwise, try to resolve it
            try:
                # Try custom URL or handle format first
                if url.find('/@') != -1 or url.find('/c/') != -1:
                    # For @username and /c/ format, search by name
                    response = youtube.search().list(
                        part="snippet",
                        q=identifier,
                        type="channel",
                        maxResults=1
                    ).execute()
                    
                    if response.get("items"):
                        return response["items"][0]["snippet"]["channelId"]
                
                elif url.find('/user/') != -1:
                    # For /user/ format, use forUsername
                    response = youtube.channels().list(
                        part="id",
                        forUsername=identifier
                    ).execute()
                    
                    if response.get("items"):
                        return response["items"][0]["id"]
                
                # Fallback: search by name
                response = youtube.search().list(
                    part="snippet",
                    q=identifier,
                    type="channel",
                    maxResults=1
                ).execute()
                
                if response.get("items"):
                    return response["items"][0]["snippet"]["channelId"]
                    
            except Exception as e:
                print(f"Error resolving channel ID for {identifier}: {e}")
                continue
    
    # If no pattern matched, try searching the entire URL as a query
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
        print(f"Error searching for channel with URL {url}: {e}")
    
    return None

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
    import dateutil.parser
    
    # Import database service here to avoid circular imports
    from services import database as db_service
    
    # If no URLs provided, get from saved channels
    if not channel_urls and use_saved_channels:
        channel_urls = db_service.get_channel_urls_for_analysis(active_only=True)
        
    if not channel_urls:
        return {
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
    
    # Calculate cutoff date
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
    
    for url in channel_urls:
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
                results["channels"].append(channel_data)
                continue
            
            channel_data["channel_id"] = channel_id
            
            # Get channel info with metadata
            channel_metadata = get_channel_metadata(channel_id)
            
            if not channel_metadata:
                channel_data["error"] = f"Channel not found: {channel_id}"
                results["channels"].append(channel_data)
                continue
            
            # Add channel metadata to response
            channel_data.update(channel_metadata)
            
            # Save channel to database if requested
            if save_channels:
                try:
                    saved_channel = db_service.save_youtube_channel(
                        channel_url=url,
                        channel_id=channel_id,
                        channel_name=channel_metadata.get("channel_name"),
                        subscriber_count=channel_metadata.get("subscriber_count"),
                        description=channel_metadata.get("description"),
                        thumbnail_url=channel_metadata.get("thumbnail_url")
                    )
                    if saved_channel:
                        channel_data["saved_to_db"] = True
                except Exception as e:
                    print(f"Error saving channel to database: {e}")
                    channel_data["save_error"] = str(e)
            
            # Get videos from this channel
            videos = get_recent_videos_from_channel(
                channel_id, 
                cutoff_date, 
                max_videos_per_channel
            )
            
            channel_data["videos"] = videos
            channel_data["video_count"] = len(videos)
            results["total_videos"] += len(videos)
            
            # Update channel analysis stats if saved
            if save_channels and channel_data.get("saved_to_db"):
                try:
                    db_service.update_channel_analysis_stats(
                        channel_url=url,
                        video_count=len(videos),
                        analysis_datetime=datetime.now()
                    )
                except Exception as e:
                    print(f"Error updating channel stats: {e}")
            
        except Exception as e:
            channel_data["error"] = f"Error processing channel {url}: {str(e)}"
        
        results["channels"].append(channel_data)
    
    # Add summary statistics
    results["summary"] = {
        "channels_processed": len(channel_urls),
        "channels_successful": len([c for c in results["channels"] if not c.get("error")]),
        "channels_failed": len([c for c in results["channels"] if c.get("error")]),
        "total_videos_found": results["total_videos"],
        "channels_saved": len([c for c in results["channels"] if c.get("saved_to_db")])
    }
    
    return results

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


def process_video(video, channel_id):
    transcribed_video = transcribe_video(video['video_id'])
    transcribed_video.channel_id = channel_id
    
    return transcribed_video

async def process_video_description(latest_youtube_transcription):
    youtube_description_output = await youtube_agents.youtube_agent_runner(latest_youtube_transcription.segments)
    
    print(youtube_description_output)
    
    database_service.save_youtube_description(
        latest_youtube_transcription.id,
        latest_youtube_transcription.video_id,
        youtube_description_output.description,
        youtube_description_output.chapters
    )
    
    return youtube_description_output

# Main function to process videos
def main():
    user_input = "tylerreedai"
    channel_id = get_channel_id(user_input)

    if not channel_id:
        print("Failed to retrieve channel ID. Please check the input.")
        return

    # Create a directory for the channel if it doesn't exist
    sanitized_channel_name = re.sub(r'[\\/:*?"<>|]', '_', user_input)
    channel_directory = os.path.join(sanitized_channel_name)
    os.makedirs(channel_directory, exist_ok=True)

    # Get latest videos
    videos = get_latest_videos(channel_id)
    video_metadata = []

    # Transcribe and save each video
    for video in videos:
        transcribed_video = process_video(video, channel_id)

        print(f"Processed video: {video['title']}")
        
        video_metadata.append(
            YouTubeTranscriptionCreate(
                video_id=video['video_id'], 
                channel_id=channel_id,
                transcription=transcribed_video.transcription,
                segments=transcribed_video.segments,
                used=False
            )
        )
        
    return video_metadata
    
def get_youtube_oauth_service():
    """Get YouTube service with OAuth authentication for comment operations."""
    creds = None
    
    # Check if token.json exists
    if os.path.exists(CLIENT_TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(CLIENT_TOKEN_FILE, SCOPES)
    
    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Check if credentials file exists
            if not os.path.exists(CLIENT_SECRETS_FILE):
                raise Exception(
                    "YouTube OAuth credentials not found. Please add youtube_credentials.json file.\n"
                    "This should be downloaded from Google Cloud Console > APIs & Services > Credentials"
                )
            
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRETS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open('credentials/token.json', 'w') as token:
            token.write(creds.to_json())
    
    return build('youtube', 'v3', credentials=creds)

def get_video_comments(video_id, max_results=100):
    """Get comments from a YouTube video with replies."""
    try:
        service = get_youtube_oauth_service()
        
        request = service.commentThreads().list(
            part="snippet,replies",
            videoId=video_id,
            maxResults=max_results,
            order="time"
        )
        
        response = request.execute()
        comments = []
        
        for item in response.get("items", []):
            comment = item["snippet"]["topLevelComment"]["snippet"]
            
            # Parse replies if they exist
            replies = []
            if "replies" in item:
                for reply_item in item["replies"]["comments"]:
                    reply_snippet = reply_item["snippet"]
                    replies.append({
                        "reply_id": reply_item["id"],
                        "text": reply_snippet["textDisplay"],
                        "author": reply_snippet["authorDisplayName"],
                        "like_count": reply_snippet["likeCount"],
                        "published_at": reply_snippet["publishedAt"],
                        "parent_id": reply_snippet["parentId"]
                    })
            
            comments.append({
                "comment_id": item["snippet"]["topLevelComment"]["id"],
                "text": comment["textDisplay"],
                "author": comment["authorDisplayName"],
                "like_count": comment["likeCount"],
                "published_at": comment["publishedAt"],
                "can_reply": item["snippet"]["canReply"],
                "replies": replies,
                "reply_count": len(replies)
            })
        
        return comments
        
    except Exception as e:
        print(f"Error getting comments: {e}")
        raise

def create_comment(video_id, comment_text):
    """Create a comment on a YouTube video."""
    try:
        service = get_youtube_oauth_service()
        
        request = service.commentThreads().insert(
            part="snippet",
            body={
                "snippet": {
                    "videoId": video_id,
                    "topLevelComment": {
                        "snippet": {
                            "textOriginal": comment_text
                        }
                    }
                }
            }
        )
        
        response = request.execute()
        
        return {
            "comment_id": response["snippet"]["topLevelComment"]["id"],
            "text": comment_text,
            "video_id": video_id,
            "status": "created"
        }
        
    except Exception as e:
        print(f"Error creating comment: {e}")
        raise

def pin_comment(comment_id):
    """Pin a comment to a YouTube video."""
    try:
        service = get_youtube_oauth_service()
        
        # First, get the comment details to get the video ID
        comment_request = service.comments().list(
            part="snippet",
            id=comment_id
        )
        comment_response = comment_request.execute()
        
        if not comment_response.get("items"):
            raise Exception("Comment not found")
        
        # Pin the comment using the comments.setModerationStatus endpoint
        request = service.comments().setModerationStatus(
            id=comment_id,
            moderationStatus="published",
            banAuthor=False
        )
        
        request.execute()
        
        return {
            "comment_id": comment_id,
            "status": "pinned"
        }
        
    except Exception as e:
        print(f"Error pinning comment: {e}")
        raise

def create_and_pin_comment(video_id, comment_text):
    """Create a comment and immediately pin it to a YouTube video."""
    try:
        # First create the comment
        comment_result = create_comment(video_id, comment_text)
        comment_id = comment_result["comment_id"]
        
        # Then pin it
        pin_result = pin_comment(comment_id)
        
        return {
            "comment_id": comment_id,
            "text": comment_text,
            "video_id": video_id,
            "status": "created_and_pinned"
        }
        
    except Exception as e:
        print(f"Error creating and pinning comment: {e}")
        raise

def get_latest_videos_detailed(channel_id, max_results=10, exclude_shorts=False, include_comments=False, comment_limit=20):
    """Get the latest videos from a channel with detailed information needed for comment creation."""
    try:
        # If excluding shorts, fetch more videos to account for filtering
        fetch_count = max_results * 3 if exclude_shorts else max_results
        
        # Use OAuth service if comments are requested, otherwise use regular service
        service = get_youtube_oauth_service() if include_comments else youtube
        
        # First, get the video IDs from search
        search_request = service.search().list(
            part="snippet",
            channelId=channel_id,
            order="date",
            type="video",
            maxResults=fetch_count
        )
        search_response = search_request.execute()
        
        # Extract video IDs
        video_ids = []
        for item in search_response.get("items", []):
            video_ids.append(item["id"]["videoId"])
        
        if not video_ids:
            return []
        
        # Now get detailed information for each video
        videos_request = service.videos().list(
            part="snippet,statistics,contentDetails",
            id=",".join(video_ids)
        )
        videos_response = videos_request.execute()
        
        videos = []
        for item in videos_response.get("items", []):
            video_data = {
                "video_id": item["id"],
                "title": item["snippet"]["title"],
                "description": item["snippet"]["description"],
                "published_at": item["snippet"]["publishedAt"],
                "thumbnail": item["snippet"]["thumbnails"]["high"]["url"] if "high" in item["snippet"]["thumbnails"] else item["snippet"]["thumbnails"]["default"]["url"],
                "channel_id": item["snippet"]["channelId"],
                "channel_title": item["snippet"]["channelTitle"],
                "duration": item["contentDetails"]["duration"],
                "view_count": int(item["statistics"].get("viewCount", 0)),
                "like_count": int(item["statistics"].get("likeCount", 0)),
                "comment_count": int(item["statistics"].get("commentCount", 0)),
                "tags": item["snippet"].get("tags", []),
                "category_id": item["snippet"]["categoryId"],
                "video_url": f"https://www.youtube.com/watch?v={item['id']}"
            }
            
            # Add comments if requested
            if include_comments:
                try:
                    comments = get_video_comments(item["id"], comment_limit)
                    video_data["comments"] = comments
                    video_data["comments_retrieved"] = len(comments)
                except Exception as e:
                    print(f"Error getting comments for video {item['id']}: {e}")
                    video_data["comments"] = []
                    video_data["comments_retrieved"] = 0
                    video_data["comments_error"] = str(e)
            
            # Filter out shorts if requested
            if exclude_shorts:
                duration_seconds = parse_youtube_duration(video_data["duration"])
                if duration_seconds >= 60:  # Only include videos 60 seconds or longer
                    videos.append(video_data)
                    if len(videos) >= max_results:
                        break
            else:
                videos.append(video_data)
        
        return videos
        
    except Exception as e:
        print(f"Error getting latest videos: {e}")
        raise

def get_my_channel_videos(max_results=10, include_comments=True, comment_limit=20):
    """Get the latest videos from your own channel (authenticated), excluding YouTube Shorts."""
    try:
        # Get authenticated OAuth service (required for mine=True parameter)
        service = get_youtube_oauth_service()
        
        # Get my channel ID
        channel_request = service.channels().list(part="snippet", mine=True)
        channel_response = channel_request.execute()
        
        if not channel_response.get("items"):
            raise Exception("No channel found for authenticated user")
        
        my_channel_id = channel_response["items"][0]["id"]
        
        # Get videos from my channel, excluding shorts
        return get_latest_videos_detailed(
            my_channel_id, 
            max_results, 
            exclude_shorts=True,
            include_comments=include_comments,
            comment_limit=comment_limit
        )
        
    except Exception as e:
        print(f"Error getting my channel videos: {e}")
        raise

def parse_youtube_duration(duration_string):
    """Parse YouTube's ISO 8601 duration format and return total seconds."""
    import re
    
    # YouTube duration format is like: PT4M13S (4 minutes 13 seconds) or PT30S (30 seconds)
    # Remove 'PT' prefix
    duration = duration_string[2:] if duration_string.startswith('PT') else duration_string
    
    # Extract hours, minutes, and seconds using regex
    hours = 0
    minutes = 0
    seconds = 0
    
    # Match hours (e.g., 1H)
    hour_match = re.search(r'(\d+)H', duration)
    if hour_match:
        hours = int(hour_match.group(1))
    
    # Match minutes (e.g., 4M)
    minute_match = re.search(r'(\d+)M', duration)
    if minute_match:
        minutes = int(minute_match.group(1))
    
    # Match seconds (e.g., 13S)
    second_match = re.search(r'(\d+)S', duration)
    if second_match:
        seconds = int(second_match.group(1))
    
    # Convert everything to seconds
    total_seconds = hours * 3600 + minutes * 60 + seconds
    return total_seconds

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