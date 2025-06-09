import tweepy
import os
import requests
from io import BytesIO
from PIL import Image
from services import database as database_service
from dotenv import load_dotenv
from models.twitter import TwitterPostCreate, TwitterPostUpdate
from agents_all.twitter import twitter_agent_runner
from models.youtube import YouTubeTranscriptionCreate

load_dotenv()

API_KEY = os.getenv("TWITTER_API_KEY")
API_SECRET = os.getenv("TWITTER_API_SECRET")
ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")

async def twitter_service(input_data: str):
    agent_output = await twitter_agent_runner(input_data)
    return agent_output

async def post_to_twitter(youtube_record: YouTubeTranscriptionCreate):
    client = tweepy.Client(
        consumer_key=API_KEY, consumer_secret=API_SECRET,
        access_token=ACCESS_TOKEN, access_token_secret=ACCESS_SECRET
    )

    if youtube_record is not None:
        input_data = f"YouTube Video URL: https://www.youtube.com/watch?v={youtube_record.video_id} and transcription: {youtube_record.transcription}"
        agent_output = await twitter_service(input_data)
        
        return agent_output
        
        # response = client.create_tweet(
        #     text=agent_output.tweet
        # )
        
        # tweet_text = response.data['text']
        # tweet_id = str(response.data['id'])
        
        # print(f"Tweet text: {tweet_text}")
        # print(f"Tweet ID: {tweet_id}")
        # print(f"Youtube transcription ID: {youtube_record.id}")
        
        # database_service.save_twitter_post(
        #     youtube_transcription_id=youtube_record.id,
        #     tweet=tweet_text,
        #     tweet_id=tweet_id
        # )
        
        # return {
        #     "tweet_id": tweet_id,
        #     "tweet": tweet_text,
        #     "tweet_url": f"https://twitter.com/{tweet_obj.user.screen_name}/status/{tweet_id}"
        # }
    else:
        pass
        return {
            "error": "No YouTube transcription found"
        }

async def post_tweet_service():
    client = tweepy.Client(
        consumer_key=os.getenv("TWITTER_API_KEY"), 
        consumer_secret=os.getenv("TWITTER_API_SECRET"), 
        access_token=os.getenv("TWITTER_ACCESS_TOKEN"), 
        access_token_secret=os.getenv("TWITTER_ACCESS_SECRET")
        # bearer_token=os.getenv("TWITTER_BEARER_TOKEN")
    )

    latest_youtube_transcription = get_latest_youtube_transcription()
    
    if latest_youtube_transcription:
        input_data = f"""
            YouTube Video URL: https://www.youtube.com/watch?v={latest_youtube_transcription.video_id} 
            and transcription: {latest_youtube_transcription.transcription}
        """
        agent_output = await twitter_service(input_data)
        
        print(f"Agent output: {agent_output}")
        
        response = client.create_tweet(
            text=agent_output.tweet
        )
        
        main_tweet_id = response.data['id']
        
        # if agent_output.reply_tweets is not None:
        #     for reply in agent_output.reply_tweets:
        #         post_tweet_as_reply(reply.reply_tweet, main_tweet_id)
        
        # response = client.create_tweet(
        #     text=agent_output.tweet
        # )
        
        # tweet_text = agent_output.tweet
        # tweet_id = str(response.data['id'])
        
        # print(f"Tweet text: {tweet_text}")
        # print(f"Tweet ID: {tweet_id}")
        # print(f"Youtube transcription ID: {latest_youtube_transcription.id}")
        
        # database_service.save_twitter_post(
        #     youtube_transcription_id=latest_youtube_transcription.id,
        #     tweet=tweet_text,
        #     tweet_id=tweet_id
        # )

        # return {
        #     "tweet_id": tweet_id,
        #     "tweet": tweet_text,
        #     "tweet_url": f"https://twitter.com/{response.data['username']}/status/{tweet_id}"
        # }
        return agent_output
    
    return {
        "error": "No YouTube transcription found"
    }
    
def upload_image_to_twitter(image_path: str, image_name: str):
    client = tweepy.OAuth1UserHandler(
        consumer_key=os.getenv("TWITTER_API_KEY"), 
        consumer_secret=os.getenv("TWITTER_API_SECRET"), 
        access_token=os.getenv("TWITTER_ACCESS_TOKEN"), 
        access_token_secret=os.getenv("TWITTER_ACCESS_SECRET")
    )

    api = tweepy.API(client)

    download_image(image_path, f"{image_name}.png")

    img = Image.open(f"{image_name}.png")

    # Save image in-memory
    bytes_io = BytesIO()
    img.save(bytes_io, "PNG")
    bytes_io.seek(0)

    # Upload the image
    upload = api.media_upload(
        filename=image_name,
        file=bytes_io
    )

    print(f"Uploaded image: {upload}")
    print(f"Uploaded image ID: {upload.media_id}")
    
    return upload.media_id

def download_image(url, save_path):
    response = requests.get(url)
    if response.status_code == 200:
        with open(save_path, 'wb') as f:
            f.write(response.content)
        print(f"Image downloaded and saved to {save_path}")
    else:
        print(f"Failed to download image. Status code: {response.status_code}")


def post_tweet_as_reply(tweet: str, main_tweet_id: str, media_ids: list[str] = None):
    """
    Post a tweet to Twitter as a reply to the main tweet.
    
    Args:
        tweet: The tweet to post
        main_tweet_id: The ID of the main tweet to reply to
    """
    
    client = tweepy.Client(
        consumer_key=os.getenv("TWITTER_API_KEY"), 
        consumer_secret=os.getenv("TWITTER_API_SECRET"), 
        access_token=os.getenv("TWITTER_ACCESS_TOKEN"), 
        access_token_secret=os.getenv("TWITTER_ACCESS_SECRET")
    )
    
    response = client.create_tweet(
        text=tweet,
        in_reply_to_tweet_id=main_tweet_id,
        media_ids=media_ids
    )
    
    tweet_text = response.data['text']
    username = response.data['username']
    reply_tweet_id = str(response.data['id'])
    
    return {
        "tweet_id": reply_tweet_id,
        "tweet": tweet_text,
        "tweet_url": f"https://twitter.com/{username}/status/{reply_tweet_id}"
    }

def get_latest_youtube_transcription():
    youtube_record = database_service.check_latest_transcription()
    
    if youtube_record:
        return youtube_record
    else:
        return None

def get_all_twitter_posts():
    return database_service.get_all_twitter_posts()

def get_twitter_post_by_id(post_id: int):
    return database_service.get_twitter_post_by_id(post_id)

def update_twitter_post(post_id: int, update_data: TwitterPostUpdate):
    return database_service.update_twitter_post(post_id, update_data)

def delete_twitter_post(post_id: int):
    return database_service.delete_twitter_post(post_id)
