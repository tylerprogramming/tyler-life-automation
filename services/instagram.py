import requests
import os
from agents_all.instagram_agents import instagram_agent_runner
from services import database as database_service
from dotenv import load_dotenv
from models.youtube import YouTubeTranscriptionCreate 

load_dotenv()

INSTAGRAM_ACCOUNT_ID = os.getenv("INSTAGRAM_ACCOUNT_ID")
INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")

def refresh_instagram_access_token():
    url = f"https://graph.instagram.com/refresh_access_token?grant_type=ig_refresh_token&access_token={INSTAGRAM_ACCESS_TOKEN}"
    response = requests.get(url)
    print(response.json())

async def post_to_instagram(youtube_record: YouTubeTranscriptionCreate):
    youtube_video_url = f"https://www.youtube.com/watch?v={youtube_record.video_id}"
    
    input_data = f"Transcription: {youtube_record.transcription} Video URL: {youtube_video_url}"
    
    print("Youtube Record:", youtube_record)
    
    if youtube_record:
        agent_output = await instagram_agent_runner(input_data)
        
        print("Agent Output:", agent_output)
        
        database_service.save_instagram_post(youtube_record.id, agent_output.caption, "test_url")
    else:   
        return "No transcription found"

    # Upload Image to Instagram
    url = f"https://graph.instagram.com/v22.0/{INSTAGRAM_ACCOUNT_ID}/media"
    payload = {
        "image_url": "test_url",
        "caption": "test_caption",
        "access_token": INSTAGRAM_ACCESS_TOKEN
    }
    response = requests.post(url, data=payload)
    media_id = response.json().get("id")

    print("Media ID:", media_id)

    # Publish the uploaded media
    publish_url = f"https://graph.instagram.com/v22.0/{INSTAGRAM_ACCOUNT_ID}/media_publish"
    publish_response = requests.post(publish_url, data={"creation_id": media_id, "access_token": INSTAGRAM_ACCESS_TOKEN})

    print("Publish Response:", publish_response.json())

async def post_instagram_image(image_urls: list[str] = None):
    youtube_record = database_service.check_latest_transcription()
    youtube_video_url = f"https://www.youtube.com/watch?v={youtube_record.video_id}"
    
    input_data = f"Transcription: {youtube_record.transcription} Video URL: {youtube_video_url}"
    
    if youtube_record:
        agent_output = await instagram_agent_runner(input_data)

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
            publish_media_to_instagram(container_id['id'])
        else:
            print("Single Image")
            # upload_single_image_caption_to_instagram(image_urls[0], agent_output.caption)
        
    #     # Upload Image to Instagram
    #     url = f"https://graph.instagram.com/v22.0/{INSTAGRAM_ACCOUNT_ID}/media"
    #     payload = {
    #         "image_url": image_url,
    #         "caption": agent_output.caption,
    #         "access_token": ACCESS_TOKEN
    #     }
    #     response = requests.post(url, data=payload)
    #     media_id = response.json().get("id")

    #     print("Media ID:", media_id)

    #     # Publish the uploaded media
    #     publish_url = f"https://graph.instagram.com/v22.0/{INSTAGRAM_ACCOUNT_ID}/media_publish"
    #     publish_response = requests.post(publish_url, data={"creation_id": media_id, "access_token": ACCESS_TOKEN})

    #     print("Publish Response:", publish_response.json())
        
    #     return agent_output.caption
    else:
        return "No transcription found"

    # # Upload Image to Instagram
    # url = f"https://graph.instagram.com/v22.0/{INSTAGRAM_ACCOUNT_ID}/media"
    # payload = {
    #     "image_url": image_url,
    #     "caption": caption,
    #     "access_token": ACCESS_TOKEN
    # }
    # response = requests.post(url, data=payload)
    # media_id = response.json().get("id")

    # print("Media ID:", media_id)

    # # Publish the uploaded media
    # publish_url = f"https://graph.instagram.com/v22.0/{INSTAGRAM_ACCOUNT_ID}/media_publish"
    # publish_response = requests.post(publish_url, data={"creation_id": media_id, "access_token": ACCESS_TOKEN})

    # print("Publish Response:", publish_response.json())

def upload_image_only_to_instagram(image_url):
    """
    Uploads an image to Instagram using the Graph API with a JSON payload and Bearer token.
    Equivalent to the provided curl command.
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
    print("Upload Response:", response.json())
    return response.json()

def upload_single_image_caption_to_instagram(image_url, caption):
    # Uploads Image to Instagram with caption, doesn't post just yet.  We get a media id.
    url = f"https://graph.instagram.com/v22.0/{INSTAGRAM_ACCOUNT_ID}/media"
    
    payload = {
        "image_url": image_url,
        "caption": caption,
        "access_token": INSTAGRAM_ACCESS_TOKEN
    }
    
    response = requests.post(url, data=payload)
    media_id = response.json().get("id")
    
    print("Response:", response.json())

    print("Media ID:", media_id)

def upload_carousel_to_instagram(caption, children_ids):
    """
    Uploads a carousel (multiple images) to Instagram using the Graph API.
    :param caption: The caption for the carousel post.
    :param children_ids: List of IG container IDs (strings) for the carousel images.
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

def publish_media_to_instagram(media_id):
    # Publish the uploaded media with the media id given from single image upload.  this will take caption and image and post.
    publish_url = f"https://graph.instagram.com/v22.0/{INSTAGRAM_ACCOUNT_ID}/media_publish"
    publish_response = requests.post(
        publish_url, 
        data={
            "creation_id": media_id, 
            "access_token": INSTAGRAM_ACCESS_TOKEN
        }
    )

    print("Publish Response:", publish_response.json())

def get_all_instagram_posts():
    return database_service.get_all_instagram_posts()

def get_instagram_post_by_id(post_id: int):
    return database_service.get_instagram_post_by_id(post_id)

def update_instagram_post(post_id: int, update_data):
    return database_service.update_instagram_post(post_id, update_data)

def delete_instagram_post(post_id: int):
    return database_service.delete_instagram_post(post_id)

if __name__ == "__main__":
    post_instagram_image()

