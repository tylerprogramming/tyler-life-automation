from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone
import os
from dotenv import load_dotenv
from models.youtube import YouTubeTranscriptionCreate, YouTubeTranscriptionUpdate
import uuid 
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class YouTubeTranscription(Base):
    __tablename__ = "youtube_transcriptions"
    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(String, nullable=False)
    channel_id = Column(String, nullable=False)
    transcription = Column(Text, nullable=False)
    segments = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    used = Column(Boolean, default=False)

class YouTubeDescription(Base):
    __tablename__ = "youtube_descriptions"
    id = Column(Integer, primary_key=True, index=True)
    youtube_transcription_id = Column(Integer, ForeignKey('youtube_transcriptions.id'), nullable=False)
    video_id = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    chapters = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    used = Column(Boolean, default=False)
    
class InstagramPost(Base):
    __tablename__ = "instagram_posts"
    id = Column(Integer, primary_key=True, index=True)
    youtube_transcription_id = Column(Integer, ForeignKey('youtube_transcriptions.id'), nullable=False)
    post_id = Column(String, nullable=True, default=str(uuid.uuid4()))
    caption = Column(Text, nullable=False)
    image_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class TwitterPost(Base):
    __tablename__ = "twitter_posts"
    id = Column(Integer, primary_key=True, index=True)
    youtube_transcription_id = Column(Integer, ForeignKey('youtube_transcriptions.id'), nullable=False)
    tweet_id = Column(String, nullable=True, default=str(uuid.uuid4()))
    tweet = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class LinkedinPost(Base):
    __tablename__ = "linkedin_posts"
    id = Column(Integer, primary_key=True, index=True)
    youtube_transcription_id = Column(Integer, ForeignKey('youtube_transcriptions.id'), nullable=True)
    post_urn = Column(String, nullable=False, unique=True)
    commentary = Column(Text, nullable=False)
    visibility = Column(String, nullable=False, default="PUBLIC")
    author = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

def init_db():
    Base.metadata.create_all(bind=engine)

def check_latest_transcription():
    session = SessionLocal()
    try:
        return session.query(YouTubeTranscription).filter_by(used=False).order_by(YouTubeTranscription.created_at.desc()).first()
    finally:
        session.close()
        
def save_youtube_description(youtube_transcription_id: int, video_id: str, description: str, chapters: list[str]):
    session = SessionLocal()
    
    try:
        youtube_description = YouTubeDescription(
            youtube_transcription_id=youtube_transcription_id,
            video_id=video_id,
            description=description,
            chapters=chapters)
        session.add(youtube_description)
        session.commit()
    finally:
        session.close()

def save_instagram_post(youtube_transcription_id: int, caption: str, image_url: str):
    session = SessionLocal()
    try:
        instagram_post = InstagramPost(
            youtube_transcription_id=youtube_transcription_id, 
            caption=caption, 
            image_url=image_url,
            post_id=str(uuid.uuid4())
        )
        session.add(instagram_post)
        session.commit()
    finally:
        session.close()
        
def insert_transcription(metadata: YouTubeTranscriptionCreate):
    session = SessionLocal()
    
    print(metadata)

    try:
        yt_trans = YouTubeTranscription(**metadata.model_dump())
        session.add(yt_trans)
        session.commit()
    finally:
        session.close()

def get_all_transcriptions():
    session = SessionLocal()
    try:
        return session.query(YouTubeTranscription).all()
    finally:
        session.close()

def delete_transcription(transcription_id: int):
    session = SessionLocal()
    try:
        obj = session.query(YouTubeTranscription).filter_by(id=transcription_id).first()
        if obj:
            session.delete(obj)
            session.commit()
            return True
        return False
    finally:
        session.close()
        
def update_transcription(transcription_id, update_data: YouTubeTranscriptionUpdate):
    """
    Update fields of a YouTubeTranscription by id.
    update_data should be a dict of fields to update.
    """
    session = SessionLocal()
    try:
        obj = session.query(YouTubeTranscription).filter_by(id=transcription_id).first()
        if not obj:
            return None
        for key, value in update_data.model_dump(exclude_unset=True).items():
            if hasattr(obj, key):
                setattr(obj, key, value)
        session.commit()
        session.refresh(obj)
        return obj
    finally:
        session.close()

def video_exists(video_id: str) -> bool:
    """
    Check if a video with the given video_id exists in the database.
    Returns True if it exists, False otherwise.
    """
    session = SessionLocal()
    try:
        return session.query(YouTubeTranscription).filter_by(video_id=video_id).first() is not None
    finally:
        session.close()

def get_all_instagram_posts():
    session = SessionLocal()
    try:
        return session.query(InstagramPost).all()
    finally:
        session.close()

def get_instagram_post_by_id(post_id: int):
    session = SessionLocal()
    try:
        return session.query(InstagramPost).filter_by(id=post_id).first()
    finally:
        session.close()

def update_instagram_post(post_id: int, update_data):
    session = SessionLocal()
    try:
        post = session.query(InstagramPost).filter_by(id=post_id).first()
        if not post:
            return None
        for key, value in update_data.model_dump(exclude_unset=True).items():
            if hasattr(post, key):
                setattr(post, key, value)
        session.commit()
        session.refresh(post)
        return post
    finally:
        session.close()

def delete_instagram_post(post_id: int):
    session = SessionLocal()
    try:
        post = session.query(InstagramPost).filter_by(id=post_id).first()
        if post:
            session.delete(post)
            session.commit()
            return True
        return False
    finally:
        session.close()

def save_twitter_post(youtube_transcription_id: int, tweet: str, tweet_id: str = None):
    session = SessionLocal()
    try:
        twitter_post = TwitterPost(
            youtube_transcription_id=youtube_transcription_id,
            tweet=tweet,
            tweet_id=tweet_id or str(uuid.uuid4())
        )
        session.add(twitter_post)
        session.commit()
    finally:
        session.close()

def get_all_twitter_posts():
    session = SessionLocal()
    try:
        return session.query(TwitterPost).all()
    finally:
        session.close()

def get_twitter_post_by_id(post_id: int):
    session = SessionLocal()
    try:
        return session.query(TwitterPost).filter_by(id=post_id).first()
    finally:
        session.close()

def update_twitter_post(post_id: int, update_data):
    session = SessionLocal()
    try:
        post = session.query(TwitterPost).filter_by(id=post_id).first()
        if not post:
            return None
        for key, value in update_data.model_dump(exclude_unset=True).items():
            if hasattr(post, key):
                setattr(post, key, value)
        session.commit()
        session.refresh(post)
        return post
    finally:
        session.close()

def delete_twitter_post(post_id: int):
    session = SessionLocal()
    try:
        post = session.query(TwitterPost).filter_by(id=post_id).first()
        if post:
            session.delete(post)
            session.commit()
            return True
        return False
    finally:
        session.close()

def save_linkedin_post(youtube_transcription_id: int, post_urn: str, commentary: str, visibility: str, author: str):
    session = SessionLocal()
    try:
        linkedin_post = LinkedinPost(
            youtube_transcription_id=youtube_transcription_id,
            post_urn=post_urn,
            commentary=commentary,
            visibility=visibility,
            author=author
        )
        session.add(linkedin_post)
        session.commit()
        session.refresh(linkedin_post)
        return linkedin_post
    finally:
        session.close()

def get_all_linkedin_posts():
    session = SessionLocal()
    try:
        return session.query(LinkedinPost).all()
    finally:
        session.close()

def get_linkedin_post_by_id(post_id: int):
    session = SessionLocal()
    try:
        return session.query(LinkedinPost).filter_by(id=post_id).first()
    finally:
        session.close()

def update_linkedin_post(post_id: int, update_data):
    session = SessionLocal()
    try:
        post = session.query(LinkedinPost).filter_by(id=post_id).first()
        if not post:
            return None
        for key, value in update_data.model_dump(exclude_unset=True).items():
            if hasattr(post, key):
                setattr(post, key, value)
        session.commit()
        session.refresh(post)
        return post
    finally:
        session.close()

def delete_linkedin_post(post_id: int):
    session = SessionLocal()
    try:
        post = session.query(LinkedinPost).filter_by(id=post_id).first()
        if post:
            session.delete(post)
            session.commit()
            return True
        return False
    finally:
        session.close()
