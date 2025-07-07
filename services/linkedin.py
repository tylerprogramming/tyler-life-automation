import requests
import os   
from dotenv import load_dotenv
from ai_agents.linkedin import linkedin_agent_runner
from models.youtube import YouTubeTranscriptionCreate

load_dotenv()

LINKEDIN_VERSION = "202504"
ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN")
IMAGE_PATH = "7 steps build AI Agents crewai flows.png"
DOWNLOAD_PATH = "images/linkedin_image.png"

def post_to_linkedin(youtube_record: YouTubeTranscriptionCreate):
    print(youtube_record)
    
    user_info = get_user_info(ACCESS_TOKEN)
    print("User info:", user_info)
    
    person_urn = f"urn:li:person:{user_info['sub']}"
    
    # 2. Register image upload
    upload_url, asset = register_image_upload(ACCESS_TOKEN, person_urn)
    print("Register result:", upload_url, asset)

    # 3. Upload image
    upload_image_to_linkedin(upload_url, IMAGE_PATH)
    print("Image uploaded successfully!")
    
    # 4. Get image metadata (to get downloadUrl)
    image_metadata = get_image_metadata(ACCESS_TOKEN, asset)
    print("Image metadata:", image_metadata)

    # 5. Download image using downloadUrl from metadata
    download_url = image_metadata.get("downloadUrl")
    if download_url:
        download_image(download_url, DOWNLOAD_PATH)
    else:
        print("No downloadUrl found in image metadata.")
  
    input_data = f"YouTube Video URL: https://www.youtube.com/watch?v={youtube_record.video_id} and transcription: {youtube_record.transcription}"
    linkedin_output = linkedin_agent_runner(input_data)
    
    print(linkedin_output)
  
    commentary = linkedin_output.commentary
    
    post_linkedin_image_post(ACCESS_TOKEN, person_urn, commentary, DOWNLOAD_PATH)

def post_linkedin_image_post(access_token, author_urn, commentary, image_urn, alt_text="", visibility="PUBLIC"):
    url = "https://api.linkedin.com/rest/posts"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "LinkedIn-Version": LINKEDIN_VERSION,
        "Content-Type": "application/json"
    }
    data = {
        "author": author_urn,
        "commentary": commentary,
        "visibility": visibility,
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": []
        },
        "content": {
            "media": {
                "altText": alt_text,
                "id": image_urn
            }
        },
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False
    }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status() 
    
def get_user_info(access_token):
    url = "https://api.linkedin.com/v2/userinfo"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def register_image_upload(access_token, person_urn):
    url = "https://api.linkedin.com/rest/images?action=initializeUpload"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "LinkedIn-Version": LINKEDIN_VERSION,
        "X-RestLi-Protocol-Version": "2.0.0",
        "Content-Type": "application/json"
    }
    data = {
        "initializeUploadRequest": {
            "owner": person_urn
        }
    }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    upload_info = response.json()["value"]
    return upload_info["uploadUrl"], upload_info["image"]

def upload_image_to_linkedin(upload_url, image_path):
    with open(image_path, 'rb') as image_file:
        headers = {
            'Content-Type': 'application/octet-stream'
        }
        response = requests.put(upload_url, headers=headers, data=image_file)
        response.raise_for_status()
    return True

def get_image_metadata(access_token, asset):
    url = f"https://api.linkedin.com/rest/images/{asset}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "LinkedIn-Version": LINKEDIN_VERSION,
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def download_image(download_url, save_path):
    response = requests.get(download_url)
    if response.status_code == 200:
        with open(save_path, "wb") as f:
            f.write(response.content)
        print("Image downloaded successfully!")
    else:
        print("Failed to download image. Status code:", response.status_code)

def get_all_linkedin_posts(access_token, author_urn):
    """
    LinkedIn does not provide a direct endpoint to get all posts for a user via the public API.
    This is a placeholder for future implementation or for when API access is available.
    """
    url = f"https://api.linkedin.com/rest/posts?q=author&author={author_urn}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "LinkedIn-Version": LINKEDIN_VERSION,
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def get_linkedin_post(access_token, post_urn):
    url = f"https://api.linkedin.com/rest/posts/{post_urn}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "LinkedIn-Version": LINKEDIN_VERSION,
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def update_linkedin_post(access_token, post_urn, update_data):
    url = f"https://api.linkedin.com/rest/posts/{post_urn}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "LinkedIn-Version": LINKEDIN_VERSION,
        "Content-Type": "application/json"
    }
    response = requests.patch(url, headers=headers, json=update_data)
    response.raise_for_status()
    return response.json()


def delete_linkedin_post(access_token, post_urn):
    url = f"https://api.linkedin.com/rest/posts/{post_urn}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "LinkedIn-Version": LINKEDIN_VERSION,
    }
    response = requests.delete(url, headers=headers)
    response.raise_for_status()
    return {"success": True}