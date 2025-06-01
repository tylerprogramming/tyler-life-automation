from googleapiclient.discovery import build
import os
import re
from dotenv import load_dotenv
from openai import OpenAI
import yt_dlp
from models.youtube import YouTubeTranscriptionCreate
import json 

load_dotenv()

API_KEY = os.getenv("YOUTUBE_API_KEY")
youtube = build("youtube", "v3", developerKey=API_KEY)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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

    # processed_text = transcription.text

    

    # return processed_text

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


def process_video(video, channel_id):
    transcribed_video = transcribe_video(video['video_id'])
    transcribed_video.channel_id = channel_id

    return transcribed_video

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
    
    