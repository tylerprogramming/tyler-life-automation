import os
import yt_dlp
from dotenv import load_dotenv
from openai import OpenAI
from moviepy import VideoFileClip
from models.youtube import YouTubeTranscriptionCreate
from services import database as database_service
from ai_agents.youtube import youtube_agent_runner

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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

def transcribe_video(video_id):
    """Transcribe a YouTube video and return transcription data."""
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
        
    segment_data = [
        {"start": s.start, "end": s.end, "text": s.text}
        for s in transcription.segments
    ]
    
    # Clean up temporary files
    os.remove("temp_audio.mp3")

    return YouTubeTranscriptionCreate(
        video_id=video_id,
        channel_id='',
        transcription=transcription.text,
        segments=segment_data,
        used=False
    )

def transcribe_local_video(video_filename):
    """Transcribe a local video file and return transcription data."""
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
    
    segment_data = [
        {"start": s.start, "end": s.end, "text": s.text}
        for s in transcription.segments
    ]
    
    # Clean up temporary files
    os.remove("temp_audio.mp3")

    return YouTubeTranscriptionCreate(
        video_id=video_filename,
        channel_id='',
        transcription=transcription.text,
        segments=segment_data,
        used=False
    )

def process_video(video, channel_id):
    """Process a video for transcription with channel ID."""
    transcribed_video = transcribe_video(video['video_id'])
    transcribed_video.channel_id = channel_id
    
    return transcribed_video

async def process_video_description(latest_youtube_transcription):
    """Process video description using AI agents."""
    youtube_description_output = await youtube_agent_runner(latest_youtube_transcription.segments)
    
    print(youtube_description_output)
    
    database_service.save_youtube_description(
        latest_youtube_transcription.id,
        latest_youtube_transcription.video_id,
        youtube_description_output.description,
        youtube_description_output.chapters
    )
    
    return youtube_description_output 