import os
import datetime
from celery import Celery
from celery.schedules import crontab
from dotenv import load_dotenv
# from services import database as database_service
# from services import youtube as youtube_service
from services import telegram as telegram_service
from services import calendar as calendar_service

load_dotenv()

celery_app = Celery(
    "worker",
    broker=os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0"),
)

# Beat schedule to check the DB every minute
celery_app.conf.beat_schedule = {
    'send-telegram-message': {
        'task': 'send_telegram_message',
        'schedule': crontab(hour=6, minute=0),
    },
}

@celery_app.task(name='send_telegram_message')
def send_telegram_message():
    try:
        events = calendar_service.get_events_by_date_range(start_date=datetime.datetime.now(), end_date=datetime.datetime.now() + datetime.timedelta(days=1))
        
        message = ""
        for event in events:
            message += f"{event.title} - {event.scheduled_date} - {event.scheduled_time}\n"
        
        telegram_service.send_telegram_message(message)
    except Exception as e:
        print(f"❌ Failed to send Telegram message: {e}")
        return f"Failed to send Telegram message: {e}"

# @celery_app.task(name='check_latest_youtube_video')
# def check_latest_youtube_video():
#     try:
#         channel_id = youtube_service.get_channel_id("tylerreedai")
#         latest_youtube_video = youtube_service.get_latest_videos("UCrnqntHQ4oNe7HJtfiAMQ2g", 1)
#         check_exists = database_service.video_exists(latest_youtube_video[0]['video_id'])
        
#         print(f"Check video exists in database already: {check_exists}")
        
#         if not check_exists:
#             youtube_transcription_create = youtube_service.process_video(latest_youtube_video[0], channel_id)
#             database_service.insert_transcription(youtube_transcription_create)
#             print(f"Inserted transcription for {latest_youtube_video[0]['title']} into database")
            
#         return f"DB checked successfully at {datetime.datetime.now()}"
#     except Exception as e:
#         print(f"❌ DB check failed: {e}")
#         return f"DB check failed: {e}"
