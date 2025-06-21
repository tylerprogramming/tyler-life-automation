from fastapi import APIRouter
from services import linkedin as linkedin_service
from services import instagram as instagram_service
from services import youtube as youtube_service
from services import database as database_service
from services import twitter as twitter_service
from dotenv import load_dotenv
from models.youtube import YouTubeTranscriptionUpdate

load_dotenv()

router = APIRouter()

@router.post("/post_socials")
async def post_socials():
    """
    Endpoint to post content to social media platforms.
    Gets the latest transcription, processes it, and posts to socials.
    """
    latest_youtube_transcription = database_service.check_latest_transcription()
    print(latest_youtube_transcription)
    
    youtube_description = youtube_service.process_video_description(latest_youtube_transcription.segments)
    linkedin_service.post_to_linkedin(latest_youtube_transcription)
    twitter_service.post_to_twitter(latest_youtube_transcription)
    instagram_service.post_instagram_image(latest_youtube_transcription)
    
    youtube_model = YouTubeTranscriptionUpdate(
        used=True
    )
    
    # # instagram_result = instagram_service.post_instagram_image(linkedin_output)
    
    # updated_record = database_service.update_transcription(latest_youtube_transcription.id, youtube_model)
    # print(updated_record)
    return {"message": "Posted to socials."}

