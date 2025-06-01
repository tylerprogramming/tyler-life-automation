from fastapi import APIRouter, HTTPException
from services.database import (
    save_linkedin_post,
    get_all_linkedin_posts,
    get_linkedin_post_by_id,
    update_linkedin_post,
    delete_linkedin_post
)
from services import linkedin as linkedin_service
from models.linkedin import LinkedinPostCreate, LinkedinPostUpdate, LinkedinPostResponse
from dotenv import load_dotenv
import os

load_dotenv()

ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN")

router = APIRouter()

@router.get("/linkedin_posts", response_model=list[LinkedinPostResponse])
def get_all_linkedin_posts_route():
    try:
        posts = get_all_linkedin_posts()
        return [
            LinkedinPostResponse(
                post_urn=post.post_urn,
                commentary=post.commentary,
                visibility=post.visibility,
                author=post.author,
                created_at=post.created_at.isoformat() if post.created_at else None
            ) for post in posts
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/linkedin_posts/{post_id}", response_model=LinkedinPostResponse)
def get_linkedin_post_route(post_id: int):
    post = get_linkedin_post_by_id(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="LinkedIn post not found")
    return LinkedinPostResponse(
        post_urn=post.post_urn,
        commentary=post.commentary,
        visibility=post.visibility,
        author=post.author,
        created_at=post.created_at.isoformat() if post.created_at else None
    )
    
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

@router.post("/linkedin_posts", response_model=LinkedinPostResponse)
def create_linkedin_post_route(post: LinkedinPostCreate):
    # For now, youtube_transcription_id and author are not required in the model, but you can extend as needed
    # post_urn should be generated or provided (for demo, use a UUID)
    import uuid
    post_urn = str(uuid.uuid4())
    author = "demo-author"  # Replace with actual author logic if needed
    db_post = save_linkedin_post(
        youtube_transcription_id=None,
        post_urn=post_urn,
        commentary=post.commentary,
        visibility=post.visibility,
        author=author
    )
    return LinkedinPostResponse(
        post_urn=db_post.post_urn,
        commentary=db_post.commentary,
        visibility=db_post.visibility,
        author=db_post.author,
        created_at=db_post.created_at.isoformat() if db_post.created_at else None
    )

@router.patch("/linkedin_posts/{post_id}", response_model=LinkedinPostResponse)
def update_linkedin_post_route(post_id: int, update_data: LinkedinPostUpdate):
    updated = update_linkedin_post(post_id, update_data)
    if not updated:
        raise HTTPException(status_code=404, detail="LinkedIn post not found")
    return LinkedinPostResponse(
        post_urn=updated.post_urn,
        commentary=updated.commentary,
        visibility=updated.visibility,
        author=updated.author,
        created_at=updated.created_at.isoformat() if updated.created_at else None
    )

@router.delete("/linkedin_posts/{post_id}")
def delete_linkedin_post_route(post_id: int):
    deleted = delete_linkedin_post(post_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="LinkedIn post not found")
    return {"success": True}
