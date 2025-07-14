from googleapiclient.discovery import build
import os
import re
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

load_dotenv()

API_KEY = os.getenv("YOUTUBE_API_KEY")
youtube = build("youtube", "v3", developerKey=API_KEY)

# YouTube OAuth Configuration
SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]
CLIENT_SECRETS_FILE = "credentials/client_secrets.json"
CLIENT_TOKEN_FILE = "credentials/token.json"

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