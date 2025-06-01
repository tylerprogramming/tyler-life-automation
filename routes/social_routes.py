from fastapi import APIRouter, Body
from services import linkedin as linkedin_service
from services import instagram as instagram_service
from services import youtube as youtube_service
from services import database as database_service
from services import twitter as twitter_service
import os
from dotenv import load_dotenv
from models.youtube import YouTubeTranscriptionUpdate
from agents_all.linkedin_agents import linkedin_agent_runner
from agents_all.youtube_agents import youtube_agent_runner

load_dotenv()
ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN")

router = APIRouter()

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
    channel_id = youtube_service.get_channel_id(user_input)
    latest_video = youtube_service.get_latest_videos(channel_id)
    transcribed_video = youtube_service.process_video(latest_video[0], channel_id)
    
    print(transcribed_video)
    
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

@router.post("/post_socials")
async def post_socials():
    """
    Endpoint to post content to social media platforms.
    Fill in the logic to post to your desired platforms.
    """
    latest_youtube_transcription = database_service.check_latest_transcription()
    print(latest_youtube_transcription)
    
    linkedin_service.post_to_linkedin(latest_youtube_transcription)
    twitter_service.post_to_twitter(latest_youtube_transcription)
    instagram_service.post_instagram_image(latest_youtube_transcription)
    
    youtube_model = YouTubeTranscriptionUpdate(
        used=True
    )
    
    # instagram_result = instagram_service.post_instagram_image(linkedin_output)
    
    updated_record = database_service.update_transcription(latest_youtube_transcription.id, youtube_model)
    print(updated_record)
    return {"message": "Post to socials received", "payload": linkedin_output}

@router.get("/latest_youtube_videos")
async def latest_youtube_videos():
    """
    Endpoint to retrieve the latest YouTube videos.
    Fill in the logic to fetch and return videos.
    """
    # TODO: Implement YouTube fetching logic
    return {"videos": []} 

