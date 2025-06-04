import requests
import os
from agents_all.instagram_agents import instagram_agent_runner
from services import database as database_service
from dotenv import load_dotenv
from models.youtube import YouTubeTranscriptionCreate 

load_dotenv()

def refresh_instagram_access_token():
    ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")
    print("ACCESS_TOKEN:", ACCESS_TOKEN)
    url = f"https://graph.instagram.com/refresh_access_token?grant_type=ig_refresh_token&access_token={ACCESS_TOKEN}"
    response = requests.get(url)
    print(response.json())

async def post_to_instagram(youtube_record: YouTubeTranscriptionCreate):
    ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")
    INSTAGRAM_ACCOUNT_ID = os.getenv("INSTAGRAM_ACCOUNT_ID")
    
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
        "access_token": ACCESS_TOKEN
    }
    response = requests.post(url, data=payload)
    media_id = response.json().get("id")

    print("Media ID:", media_id)

    # Publish the uploaded media
    publish_url = f"https://graph.instagram.com/v22.0/{INSTAGRAM_ACCOUNT_ID}/media_publish"
    publish_response = requests.post(publish_url, data={"creation_id": media_id, "access_token": ACCESS_TOKEN})

    print("Publish Response:", publish_response.json())

async def post_instagram_image(image_url = None):
    ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")
    INSTAGRAM_ACCOUNT_ID = os.getenv("INSTAGRAM_ACCOUNT_ID")
    
    youtube_record = database_service.check_latest_transcription()
    youtube_video_url = f"https://www.youtube.com/watch?v={youtube_record.video_id}"
    
    input_data = f"Transcription: {youtube_record.transcription} Video URL: {youtube_video_url}"
    
    print("Youtube Record:", youtube_record)
    
    if youtube_record:
        agent_output = await instagram_agent_runner(input_data)
        
        print("Agent Output:", agent_output)
        
        database_service.save_instagram_post(youtube_record.id, agent_output.caption, image_url)
        
        # Upload Image to Instagram
        url = f"https://graph.instagram.com/v22.0/{INSTAGRAM_ACCOUNT_ID}/media"
        payload = {
            "image_url": image_url,
            "caption": agent_output.caption,
            "access_token": ACCESS_TOKEN
        }
        response = requests.post(url, data=payload)
        media_id = response.json().get("id")

        print("Media ID:", media_id)

        # Publish the uploaded media
        publish_url = f"https://graph.instagram.com/v22.0/{INSTAGRAM_ACCOUNT_ID}/media_publish"
        publish_response = requests.post(publish_url, data={"creation_id": media_id, "access_token": ACCESS_TOKEN})

        print("Publish Response:", publish_response.json())
        
        return agent_output.caption
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

