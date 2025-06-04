import tweepy
import os
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

    if youtube_record:
        input_data = f"YouTube Video URL: https://www.youtube.com/watch?v={youtube_record.video_id} and transcription: {youtube_record.transcription}"
        agent_output = await twitter_service(input_data)
        
        response = client.create_tweet(
            text=agent_output.tweet
        )
        
        tweet_text = response.data['text']
        tweet_id = str(response.data['id'])
        
        print(f"Tweet text: {tweet_text}")
        print(f"Tweet ID: {tweet_id}")
        print(f"Youtube transcription ID: {youtube_record.id}")
        
        database_service.save_twitter_post(
            youtube_transcription_id=youtube_record.id,
            tweet=tweet_text,
            tweet_id=tweet_id
        )
        
        return {
            "tweet_id": tweet_id,
            "tweet": tweet_text,
            "tweet_url": f"https://twitter.com/{tweet_obj.user.screen_name}/status/{tweet_id}"
        }
    
    return {
        "error": "No YouTube transcription found"
    }

async def post_tweet_service():
    client = tweepy.Client(
        consumer_key=API_KEY, consumer_secret=API_SECRET,
        access_token=ACCESS_TOKEN, access_token_secret=ACCESS_SECRET
    )
    
    latest_youtube_transcription = get_latest_youtube_transcription()
    
    if latest_youtube_transcription:
        input_data = f"YouTube Video URL: https://www.youtube.com/watch?v={latest_youtube_transcription.video_id} and transcription: {latest_youtube_transcription.transcription}"
        agent_output = await twitter_service(input_data)
        
        # response = client.create_tweet(
        #     text=agent_output.tweet
        # )
        
        tweet_text = agent_output.tweet
        # tweet_id = str(response.data['id'])
        tweet_id = "18989898989898989898"
        
        print(f"Tweet text: {tweet_text}")
        print(f"Tweet ID: {tweet_id}")
        print(f"Youtube transcription ID: {latest_youtube_transcription.id}")
        
        database_service.save_twitter_post(
            youtube_transcription_id=latest_youtube_transcription.id,
            tweet=tweet_text,
            tweet_id=tweet_id
        )
        # return {
        #     "tweet_id": tweet_id,
        #     "tweet": tweet_text,
        #     "tweet_url": f"https://twitter.com/{tweet_obj.user.screen_name}/status/{tweet_id}"
        # }
        return agent_output
    
    return {
        "error": "No YouTube transcription found"
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
