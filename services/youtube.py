# Legacy YouTube service file - Functions have been separated into specialized services:
# - youtube_transcription.py: Video download, transcription, and processing
# - youtube_analytics.py: Channel analysis, video data, and outlier analysis
# - youtube_comments.py: OAuth, comments, and authenticated operations

import re
import os
from dotenv import load_dotenv
from models.youtube import YouTubeTranscriptionCreate
from services import database as database_service
from services.youtube_transcription import process_video, get_latest_videos
from services.youtube_analytics import get_channel_id

load_dotenv()

# Main function to process videos (legacy)
def main():
    """Legacy main function for processing videos."""
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