import requests
import os
import time
from agents_all.instagram_agents import instagram_agent_runner
from services import database as database_service
from dotenv import load_dotenv
from models.youtube import YouTubeTranscriptionCreate 

load_dotenv()

INSTAGRAM_ACCOUNT_ID = os.getenv("INSTAGRAM_ACCOUNT_ID")
INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")
HOST_URL = os.getenv("HOST_URL")
LATEST_API_VERSION = os.getenv("LATEST_API_VERSION")
INSTAGRAM_CLIENT_ID = os.getenv("INSTAGRAM_CLIENT_ID")
INSTAGRAM_CLIENT_SECRET = os.getenv("INSTAGRAM_CLIENT_SECRET")

def refresh_instagram_access_token():
    """
    Refreshes the long-lived Instagram access token.
    Sends a GET request to the Instagram API to refresh the access token.
    :return: JSON response from the API.
    """
    url = f"https://{HOST_URL}/refresh_access_token?grant_type=ig_refresh_token&access_token={INSTAGRAM_ACCESS_TOKEN}"
    response = requests.get(url)
    return response.json()


async def post_instagram_image(image_urls: list[str] = None):
    """
    Posts one or more images to Instagram, optionally as a carousel.
    Uses an agent to generate a caption, saves the post to the database, uploads images, and creates a container.
    :param image_urls: List of image URLs to post.
    """
    youtube_record = database_service.check_latest_transcription()
    youtube_video_url = f"https://www.youtube.com/watch?v={youtube_record.video_id}"
    
    input_data = f"Transcription: {youtube_record.transcription} Video URL: {youtube_video_url}"
    
    if youtube_record:
        agent_output = await instagram_agent_runner(input_data)

        # need to save more info to the database for the post including children ids and container id
        database_service.save_instagram_post(youtube_record.id, agent_output.caption, ",".join(image_urls))
        
        print("Image URLs:", image_urls)
        if len(image_urls) > 1:
            children_ids = []
            for image_url in image_urls:
                child_id = upload_image_only_to_instagram(image_url)
                print("Child ID:", child_id)
                children_ids.append(child_id['id'])
                
            container_id = upload_carousel_to_instagram(agent_output.caption, children_ids)
            print("Container ID:", container_id)
        else:
            print("Single Image")
            container_id = upload_single_image_caption_to_instagram(image_urls[0], agent_output.caption)
            print("Container ID:", container_id)
    else:
        return "No transcription found"

def upload_image_only_to_instagram(image_url):
    """
    Uploads an image to Instagram using the Graph API with a JSON payload and Bearer token.
    :param image_url: Publicly accessible URL to the image.
    :return: JSON response from the API.
    """
    url = f"https://graph.instagram.com/v22.0/{INSTAGRAM_ACCOUNT_ID}/media"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {INSTAGRAM_ACCESS_TOKEN}"
    }
    payload = {
        "image_url": image_url
    }
    response = requests.post(url, headers=headers, json=payload)
    return response.json()

def upload_single_image_caption_to_instagram(image_url, caption):
    """
    Uploads a single image with a caption to Instagram (does not publish immediately).
    :param image_url: Publicly accessible URL to the image.
    :param caption: Caption for the image.
    """
    url = f"https://graph.instagram.com/v22.0/{INSTAGRAM_ACCOUNT_ID}/media"
    
    payload = {
        "image_url": image_url,
        "caption": caption,
        "access_token": INSTAGRAM_ACCESS_TOKEN
    }
    
    response = requests.post(url, data=payload)
    media_id = response.json().get("id")
    
    return {
        "media_id": media_id,
        "response": response.json()
    }

def upload_carousel_to_instagram(caption, children_ids):
    """
    Uploads a carousel (multiple images) to Instagram using the Graph API.
    :param caption: The caption for the carousel post.
    :param children_ids: List of IG container IDs (strings) for the carousel images.
    :return: JSON response from the API.
    """
    url = f"https://graph.instagram.com/v22.0/{INSTAGRAM_ACCOUNT_ID}/media"
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "caption": caption,
        "media_type": "CAROUSEL",
        "children": ",".join(children_ids),
        "access_token": INSTAGRAM_ACCESS_TOKEN
    }
    response = requests.post(url, headers=headers, json=payload)
    print("Carousel Upload Response:", response.json())
    return response.json()

async def publish_media_to_instagram(container_id):
    """
    Publishes a media container to Instagram after polling until it is ready.
    :param container_id: The ID of the media container to publish.
    :return: JSON response from the API if published, or None if not ready.
    """
    if not poll_until_ready(container_id):
        print("Media was not ready in time.")
        return
    
    print("Media is ready to publish.")
    
    # Publish the uploaded media with the media id given from single image upload.  this will take caption and image and post.
    publish_url = f"https://graph.instagram.com/v22.0/{INSTAGRAM_ACCOUNT_ID}/media_publish"
    publish_response = requests.post(
        publish_url, 
        data={
            "creation_id": container_id, 
            "access_token": INSTAGRAM_ACCESS_TOKEN
        }
    )
    
    return publish_response.json()

def poll_until_ready(container_id, max_attempts=2, wait_seconds=5):
    """
    Polls the Instagram API until the media container is ready to be published or until max_attempts is reached.
    :param container_id: The ID of the media container to check.
    :param max_attempts: Maximum number of polling attempts.
    :param wait_seconds: Seconds to wait between attempts.
    :return: True if ready, False otherwise.
    """
    url = f'https://{HOST_URL}/{LATEST_API_VERSION}/{container_id}'
    params = {
        'fields': 'status_code,status',
        'access_token': INSTAGRAM_ACCESS_TOKEN
    }

    for attempt in range(max_attempts):
        response = requests.get(url, params=params)
        data = response.json()
        print("Data:", data)

        if 'status_code' in data and data['status_code'] == 'FINISHED':
            print(f"[✓] Media is ready to publish after {attempt+1} tries.")
            return True

        print(f"[{attempt+1}] Status: {data.get('status_code', 'UNKNOWN')} - waiting...")
        time.sleep(wait_seconds)

    print("[X] Media was not ready in time.")
    return False


async def create_reels_container(video_url, caption=None, is_carousel_item=False, upload_type=None):
    """
    Creates a Reels container on Instagram.
    :param video_url: Publicly accessible URL to the video file.
    :param caption: Optional caption for the Reels.
    :param is_carousel_item: Set True if this is part of a carousel.
    :param upload_type: Set to 'resumable' for large files (optional).
    :return: API response as dict.
    """
    url = f"https://{HOST_URL}/{LATEST_API_VERSION}/{INSTAGRAM_ACCOUNT_ID}/media"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {INSTAGRAM_ACCESS_TOKEN}"
    }
    
    payload = {
        "media_type": "REELS",
        "video_url": video_url
    }
    
    if caption:
        payload["caption"] = caption
    if is_carousel_item:
        payload["is_carousel_item"] = True
    if upload_type:
        payload["upload_type"] = upload_type

    response = requests.post(url, headers=headers, json=payload)
    return response.json()

def get_instagram_user_info():
    """
    Retrieves Instagram user information using the client credentials.
    :return: JSON response from the API.
    """
    url = f"https://graph.facebook.com/oauth/access_token"
    
    params = {
        "client_id": INSTAGRAM_CLIENT_ID,
        "client_secret": INSTAGRAM_CLIENT_SECRET,
        "grant_type": "client_credentials"
    }

    response = requests.get(url, params=params)

    return response.json()

def get_all_instagram_posts():
    """
    Retrieves all Instagram posts from the database service.
    :return: List of all Instagram posts.
    """
    return database_service.get_all_instagram_posts()

def get_instagram_post_by_id(post_id: int):
    """
    Retrieves a specific Instagram post by its ID from the database service.
    :param post_id: The ID of the Instagram post.
    :return: The Instagram post data.
    """
    return database_service.get_instagram_post_by_id(post_id)

def update_instagram_post(post_id: int, update_data):
    return database_service.update_instagram_post(post_id, update_data)

def delete_instagram_post(post_id: int):
    return database_service.delete_instagram_post(post_id)

if __name__ == "__main__":
    post_instagram_image()

