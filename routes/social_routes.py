from fastapi import APIRouter, Body
from services import linkedin as linkedin_service
from services import youtube as youtube_service
from services import database as database_service
import os
from dotenv import load_dotenv
from models.youtube import YouTubeTranscriptionUpdate

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
    youtube_metadata = youtube_service.main()
    
    print(youtube_metadata)
    
    database_service.insert_transcription(youtube_metadata)
    
    return {"message": "Transcriptions inserted successfully"}

@router.post("/post_socials")
async def post_socials(payload: dict = Body(...)):
    """
    Endpoint to post content to social media platforms.
    Fill in the logic to post to your desired platforms.
    """
    # TODO: Implement posting logic
    return {"message": "Post to socials received", "payload": payload}

@router.get("/latest_youtube_videos")
async def latest_youtube_videos():
    """
    Endpoint to retrieve the latest YouTube videos.
    Fill in the logic to fetch and return videos.
    """
    # TODO: Implement YouTube fetching logic
    return {"videos": []} 

@router.get("/linkedin-user-info")
async def linkedin_user_info():
    """
    Endpoint to retrieve the LinkedIn user info.
    """
    return {"user_info": linkedin_service.get_user_info(ACCESS_TOKEN)}

@router.get("/linkedin-post-with-image")
async def linkedin_post_with_image():
    """
    Endpoint to post a LinkedIn image post.
    """
    IMAGE_PATH = "7 steps build AI Agents crewai flows.png"
    DOWNLOAD_PATH = "images/linkedin_image.png"
    
    user_info = linkedin_service.get_user_info(ACCESS_TOKEN)
    print("User info:", user_info)
    
    person_urn = f"urn:li:person:{user_info['sub']}"
    
    # 2. Register image upload
    upload_url, asset = linkedin_service.register_image_upload(ACCESS_TOKEN, person_urn)
    print("Register result:", upload_url, asset)

    # 3. Upload image
    linkedin_service.upload_image_to_linkedin(upload_url, IMAGE_PATH)
    print("Image uploaded successfully!")
    
    # 4. Get image metadata (to get downloadUrl)
    image_metadata = linkedin_service.get_image_metadata(ACCESS_TOKEN, asset)
    print("Image metadata:", image_metadata)

    # 5. Download image using downloadUrl from metadata
    download_url = image_metadata.get("downloadUrl")
    if download_url:
        linkedin_service.download_image(download_url, DOWNLOAD_PATH)
    else:
        print("No downloadUrl found in image metadata.")
  
    commentary = """
        I'll walk you through how to build a fully automated AI Workout Planner using CrewAI Flows and Composio.dev.

        Here's what we'll build together:
        🛠️ Step 1: Set up your CrewAI environment with flows
        🔗 Step 2: Connect Google Drive and Slack using composio.dev
        💡 Step 3: Define your state management for multi-step tasks
        📄 Step 4: Automatically generate workout Docs and Sheets
        🚀 Step 5: Save everything in organized Drive folders
        📬 Step 6: Send a Slack message with your new workout
        🧠 Step 7: Make it repeatable and scalable for any routine

        Link to full video: https://youtu.be/NWOoGPKfisg
    """
    
    linkedin_service.post_linkedin_image_post(ACCESS_TOKEN, person_urn, commentary, DOWNLOAD_PATH)
    
    return {"message": "LinkedIn post with image received"}