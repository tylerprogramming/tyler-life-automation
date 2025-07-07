from sqlalchemy import create_engine, func, case
from sqlalchemy.orm import sessionmaker, joinedload
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
import os
from dotenv import load_dotenv
from models.youtube import YouTubeTranscriptionCreate, YouTubeTranscriptionUpdate, YouTubeDescriptionCreate, YouTubeDescriptionUpdate
from models.content import ContentCreationResult as ContentCreationResultModel
from models.calendar import CalendarEventCreate, CalendarEventUpdate
import uuid 
from models.db_models import Base, PlatformContent, YouTubeTranscription, YouTubeDescription, ContentResult, InstagramPost, TwitterPost, LinkedinPost, CalendarEvent, InstagramUser, SkoolEvent, CommentSentimentAnalysis, SentimentType, SavedYouTubeChannel

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def check_latest_transcription():
    session = SessionLocal()
    try:
        return session.query(YouTubeTranscription).filter_by(used=False).order_by(YouTubeTranscription.created_at.desc()).first()
    finally:
        session.close()
        
def save_youtube_description(description_data: YouTubeDescriptionCreate):
    session = SessionLocal()
    
    try:
        youtube_description = YouTubeDescription(
            youtube_transcription_id=description_data.youtube_transcription_id,
            video_id=description_data.video_id,
            description=description_data.description,
            chapters=description_data.chapters)
        session.add(youtube_description)
        session.commit()
        session.refresh(youtube_description)
        return youtube_description
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
    except Exception as e:
        print(e)
        session.rollback()
    finally:
        session.close()

def get_all_transcriptions():
    session = SessionLocal()
    try:
        return session.query(YouTubeTranscription).options(joinedload(YouTubeTranscription.description)).all()
    finally:
        session.close()
        
def get_transcription_by_id(transcription_id: int):
    session = SessionLocal()
    try:
        return session.query(YouTubeTranscription).filter_by(id=transcription_id).first()
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

def update_youtube_description(description_id: int, update_data: YouTubeDescriptionUpdate):
    """
    Update fields of a YouTubeDescription by id.
    """
    session = SessionLocal()
    try:
        obj = session.query(YouTubeDescription).filter_by(id=description_id).first()
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

def get_all_content():
    session = SessionLocal()
    try:
        return session.query(ContentResult).all()
    finally:
        session.close()

def get_content_by_id(content_id: int):
    session = SessionLocal()
    try:
        return session.query(ContentResult).filter_by(id=content_id).first()
    finally:
        session.close()

def save_content_result(content_data: ContentCreationResultModel):
    session = SessionLocal()
    try:
        # Convert Pydantic models to dictionaries for JSON storage
        scraped_content_dicts = [item.model_dump() for item in content_data.scraped_content]
        
        content_result = ContentResult(
            query=content_data.query,
            urls=content_data.urls,
            scraped_content=scraped_content_dicts,
            summary=content_data.summary,
            key_highlights=content_data.key_highlights,
            noteworthy_points=content_data.noteworthy_points,
            action_items=content_data.action_items
        )
        
        print("Saving content result")
        print(content_result)
        
        session.add(content_result)
        session.commit()
        session.refresh(content_result)
        return content_result
    finally:
        session.close()

def update_content_creation_result(content_result_id: int, update_data: ContentCreationResultModel):
    session = SessionLocal()
    try:
        content_result = session.query(ContentResult).filter_by(id=content_result_id).first()
        if not content_result:
            return None
        for key, value in update_data.model_dump(exclude_unset=True).items():
            if hasattr(content_result, key):
                setattr(content_result, key, value)
        session.commit()
        session.refresh(content_result)
        return content_result
    finally:
        session.close()
        
def save_or_update_platform_content(research_id: int, platform: str, content):
    session = SessionLocal()
    try:
        platform_content = session.query(PlatformContent).filter_by(
            research_id=research_id, platform=platform
        ).first()
        print("platform content")
        print(platform_content)
        # Convert Pydantic model to dict if needed
        if hasattr(content, "model_dump"):
            content_data = content.model_dump(mode="json")
        elif hasattr(content, "dict"):
            content_data = content.dict()
        else:
            content_data = content  # string or already a dict

        if platform_content:
            print("updating platform content")
            print(content_data)
            
            platform_content.content_data = content_data
            platform_content.updated_at = datetime.now(timezone.utc)
            session.commit()
            session.refresh(platform_content)
            
            print("platform content updated")
            return platform_content
        else:
            new_content = PlatformContent(
                research_id=research_id,
                platform=platform,
                content_data=content_data,
            )
            session.add(new_content)
            session.commit()
            session.refresh(new_content)
            return new_content
    except Exception as e:
        print(e)
        session.rollback()
    finally:
        session.close()

def get_platform_posts():
    session = SessionLocal()
    try:
        # Join PlatformContent with ContentResult to get the research query
        results = (
            session.query(PlatformContent, ContentResult.query)
            .join(ContentResult, PlatformContent.research_id == ContentResult.id)
            .all()
        )
        print(results)
        return results
    finally:
        session.close()

def get_content_result_with_usage(research_id: int):
    session = SessionLocal()
    try:
        return session.query(ContentResult).filter(ContentResult.id == research_id).first()
    finally:
        session.close()

def check_platform_already_used(research_id: int, platform: str) -> bool:
    content_result = get_content_result_with_usage(research_id)
    if not content_result:
        return False
    if platform == "youtube":
        return content_result.used_for_youtube
    elif platform == "x":
        return content_result.used_for_x
    elif platform == "instagram":
        return content_result.used_for_instagram
    elif platform == "linkedin":
        return content_result.used_for_linkedin
    return False

def delete_platform_post(content_id: int) -> bool:
    session = SessionLocal()
    try:
        post = session.query(PlatformContent).filter_by(id=content_id).first()
        if post:
            session.delete(post)
            session.commit()
            return True
        return False
    finally:
        session.close()
        
def get_platform_posts_only():
    session = SessionLocal()
    try:
        return session.query(PlatformContent).all()
    finally:
        session.close()

def get_platform_content_by_id(content_id: int):
    session = SessionLocal()
    try:
        return session.query(PlatformContent).filter_by(id=content_id).first()
    finally:
        session.close()

def get_platform_content_by_ids(content_ids: list):
    """Get platform content records for the specified content IDs with research data"""
    session = SessionLocal()
    try:
        # Join PlatformContent with ContentResult to get research data
        results = (
            session.query(PlatformContent, ContentResult)
            .join(ContentResult, PlatformContent.research_id == ContentResult.id)
            .filter(PlatformContent.id.in_(content_ids))
            .all()
        )
        
        return results
    finally:
        session.close()

def update_platform_content(content_id: int, improved_content: dict):
    session = SessionLocal() 
    try:
        post = session.query(PlatformContent).filter_by(id=content_id).first()
        if not post:
            return None
        post.content_data = improved_content
        post.updated_at = datetime.now(timezone.utc)
        session.commit()
        session.refresh(post)
        return post
    finally:
        session.close()

def get_original_markdown_by_platform_content_id(content_id: int):
    session = SessionLocal()
    try:
        platform_content = session.query(PlatformContent).filter_by(id=content_id).first()
        if not platform_content:
            return None
        content_result = session.query(ContentResult).filter_by(id=platform_content.research_id).first()
        if not content_result or not content_result.scraped_content:
            return None
        # scraped_content is a list of dicts with 'markdown' keys
        markdowns = [item.get('markdown', '') for item in content_result.scraped_content]
        return "\n\n".join(markdowns)
    finally:
        session.close()

def get_dashboard_stats():
    session = SessionLocal()
    try:
        platforms = ['youtube', 'x', 'instagram', 'linkedin']
        stats = {}
        for platform in platforms:
            total = session.query(PlatformContent).filter(PlatformContent.platform == platform).count()
            ready = session.query(PlatformContent).filter(PlatformContent.platform == platform, PlatformContent.used == False).count()
            published = session.query(PlatformContent).filter(PlatformContent.platform == platform, PlatformContent.used == True).count()
            stats[platform] = {
                "total": total,
                "ready": ready,
                "published": published
            }
        # YouTubeDescription
        youtube_desc_total = session.query(YouTubeDescription).count()
        youtube_desc_ready = session.query(YouTubeDescription).filter(YouTubeDescription.used == False).count()
        youtube_desc_published = session.query(YouTubeDescription).filter(YouTubeDescription.used == True).count()
        stats["youtube"]["total"] += youtube_desc_total
        stats["youtube"]["ready"] += youtube_desc_ready
        stats["youtube"]["published"] += youtube_desc_published
        return stats
    finally:
        session.close()

def get_weekly_dashboard():
    session = SessionLocal()
    try:
        weekly_data = session.query(
            func.date_trunc('week', PlatformContent.created_at).label('week_start'),
            PlatformContent.platform,
            func.count(PlatformContent.id).label('total_posts'),
            func.sum(case((PlatformContent.used == False, 1), else_=0)).label('ready_posts'),
            func.sum(case((PlatformContent.used == True, 1), else_=0)).label('published_posts')
        ).group_by(
            func.date_trunc('week', PlatformContent.created_at),
            PlatformContent.platform
        ).order_by(
            func.date_trunc('week', PlatformContent.created_at).desc()
        ).limit(32).all()  # 8 weeks * 4 platforms
        result = [
            {
                "platform": row.platform.title(),
                "week_start": row.week_start.isoformat() if row.week_start else None,
                "total_posts": row.total_posts,
                "ready_posts": row.ready_posts,
                "published_posts": row.published_posts
            }
            for row in weekly_data
        ]
        return result
    finally:
        session.close()

def get_recent_content_results(limit: int = 5):
    session = SessionLocal()
    try:
        return session.query(ContentResult).order_by(ContentResult.created_at.desc()).limit(limit).all()
    finally:
        session.close()

# Calendar Event Functions
def get_calendar_events(start_date=None, end_date=None, platform=None, status=None):
    session = SessionLocal()
    try:
        query = session.query(CalendarEvent)
        
        if start_date:
            query = query.filter(CalendarEvent.scheduled_date >= start_date)
        if end_date:
            query = query.filter(CalendarEvent.scheduled_date <= end_date)
        if platform:
            query = query.filter(CalendarEvent.platform == platform)
        if status:
            query = query.filter(CalendarEvent.status == status)
            
        return query.order_by(CalendarEvent.scheduled_date.asc(), CalendarEvent.scheduled_time.asc()).all()
    finally:
        session.close()

def create_calendar_event(event_data: CalendarEventCreate):
    session = SessionLocal()
    try:
        event = CalendarEvent(
            id=str(uuid.uuid4()),
            content_id=event_data.content_id,
            research_id=event_data.research_id,
            platform=event_data.platform.value,
            title=event_data.title,
            scheduled_date=event_data.scheduled_date,
            scheduled_time=event_data.scheduled_time,
            status=event_data.status.value,
            notes=event_data.notes
        )
        session.add(event)
        session.commit()
        session.refresh(event)
        return event
    finally:
        session.close()

def get_calendar_event_by_id(event_id: str):
    session = SessionLocal()
    try:
        return session.query(CalendarEvent).filter_by(id=event_id).first()
    finally:
        session.close()

def update_calendar_event(event_id: str, update_data: CalendarEventUpdate):
    session = SessionLocal()
    try:
        event = session.query(CalendarEvent).filter_by(id=event_id).first()
        if not event:
            return None
        
        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            if hasattr(event, key):
                if key in ['status', 'platform'] and hasattr(value, 'value'):
                    setattr(event, key, value.value)
                else:
                    setattr(event, key, value)
        
        event.updated_at = datetime.now(timezone.utc)
        session.commit()
        session.refresh(event)
        return event
    finally:
        session.close()

def delete_calendar_event(event_id: str) -> bool:
    session = SessionLocal()
    try:
        event = session.query(CalendarEvent).filter_by(id=event_id).first()
        if event:
            session.delete(event)
            session.commit()
            return True
        return False
    finally:
        session.close()

def get_events_by_date_range(start_date, end_date, platform=None):
    session = SessionLocal()
    try:
        query = session.query(CalendarEvent).filter(
            CalendarEvent.scheduled_date >= start_date,
            CalendarEvent.scheduled_date <= end_date
        )
        
        if platform:
            query = query.filter(CalendarEvent.platform == platform)
            
        return query.order_by(CalendarEvent.scheduled_date.asc(), CalendarEvent.scheduled_time.asc()).all()
    finally:
        session.close()

# Skool Event Functions
def create_skool_event(
    title: str,
    start_time: datetime,
    end_time: datetime,
    description: str = "",
    location: Optional[Dict[str, Any]] = None,
    privacy: Optional[Dict[str, Any]] = None,
    timezone_str: str = "America/New_York",
    reminder_disabled: bool = False,
    cover_image: str = "",
    group_id: str = "",
    notes: str = "",
    tags: Optional[List[str]] = None
) -> Optional[SkoolEvent]:
    """Create a new Skool event in the database"""
    session = SessionLocal()
    try:
        skool_event = SkoolEvent(
            group_id=group_id,
            start_time=start_time,
            end_time=end_time,
            title=title,
            description=description,
            timezone=timezone_str,
            reminder_disabled=reminder_disabled,
            cover_image=cover_image,
            location=location,
            privacy=privacy,
            status='draft',
            notes=notes,
            tags=tags or []
        )
        
        session.add(skool_event)
        session.commit()
        session.refresh(skool_event)
        return skool_event
    except Exception as e:
        print(f"Error creating Skool event: {str(e)}")
        session.rollback()
        return None
    finally:
        session.close()

def get_skool_events(
    status: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 100
) -> List[SkoolEvent]:
    """Get Skool events with optional filtering"""
    session = SessionLocal()
    try:
        query = session.query(SkoolEvent)
        
        if status:
            query = query.filter(SkoolEvent.status == status)
        
        if start_date:
            query = query.filter(SkoolEvent.start_time >= start_date)
        
        if end_date:
            query = query.filter(SkoolEvent.start_time <= end_date)
        
        events = query.order_by(SkoolEvent.start_time.desc()).limit(limit).all()
        return events
    except Exception as e:
        print(f"Error getting Skool events: {str(e)}")
        return []
    finally:
        session.close()

def get_skool_event_by_id(event_id: int) -> Optional[SkoolEvent]:
    """Get a Skool event by its database ID"""
    session = SessionLocal()
    try:
        event = session.query(SkoolEvent).filter(SkoolEvent.id == event_id).first()
        return event
    except Exception as e:
        print(f"Error getting Skool event by ID: {str(e)}")
        return None
    finally:
        session.close()

def update_skool_event(event_id: int, **kwargs) -> Optional[SkoolEvent]:
    """Update a Skool event"""
    session = SessionLocal()
    try:
        event = session.query(SkoolEvent).filter(SkoolEvent.id == event_id).first()
        if not event:
            return None
        
        # Update allowed fields
        allowed_fields = [
            'title', 'description', 'start_time', 'end_time', 'timezone',
            'reminder_disabled', 'cover_image', 'location', 'privacy',
            'status', 'notes', 'tags', 'error_message', 'api_response',
            'skool_event_id', 'posted_at'
        ]
        
        for field, value in kwargs.items():
            if field in allowed_fields:
                setattr(event, field, value)
        
        event.updated_at = datetime.now(timezone.utc)
        
        session.commit()
        session.refresh(event)
        return event
    except Exception as e:
        print(f"Error updating Skool event: {str(e)}")
        session.rollback()
        return None
    finally:
        session.close()

def delete_skool_event(event_id: int) -> bool:
    """Delete a Skool event from the database"""
    session = SessionLocal()
    try:
        event = session.query(SkoolEvent).filter(SkoolEvent.id == event_id).first()
        if not event:
            return False
        
        session.delete(event)
        session.commit()
        return True
    except Exception as e:
        print(f"Error deleting Skool event: {str(e)}")
        session.rollback()
        return False
    finally:
        session.close()

# Comment Sentiment Analysis Functions
def save_comment_sentiment_analysis(
    video_id: str,
    video_title: str,
    overall_sentiment: SentimentType,
    sentiment_score: float,
    positive_count: int,
    negative_count: int,
    neutral_count: int,
    total_comments_analyzed: int,
    key_action_items: List[str] = None,
    suggestions: List[str] = None,
    main_themes: List[str] = None,
    ai_analysis: str = None,
    top_positive_comments: List[Dict] = None,
    top_negative_comments: List[Dict] = None,
    most_liked_comments: List[Dict] = None,
    analysis_model: str = None,
    processing_time_seconds: float = None,
    confidence_score: float = None
) -> Optional[CommentSentimentAnalysis]:
    """Save or update comment sentiment analysis for a video"""
    session = SessionLocal()
    try:
        # Check if analysis already exists
        existing_analysis = session.query(CommentSentimentAnalysis).filter_by(video_id=video_id).first()
        
        if existing_analysis:
            # Update existing analysis
            existing_analysis.video_title = video_title
            existing_analysis.overall_sentiment = overall_sentiment
            existing_analysis.sentiment_score = sentiment_score
            existing_analysis.confidence_score = confidence_score
            existing_analysis.positive_count = positive_count
            existing_analysis.negative_count = negative_count
            existing_analysis.neutral_count = neutral_count
            existing_analysis.total_comments_analyzed = total_comments_analyzed
            existing_analysis.key_action_items = key_action_items or []
            existing_analysis.suggestions = suggestions or []
            existing_analysis.main_themes = main_themes or []
            existing_analysis.ai_analysis = ai_analysis
            existing_analysis.top_positive_comments = top_positive_comments or []
            existing_analysis.top_negative_comments = top_negative_comments or []
            existing_analysis.most_liked_comments = most_liked_comments or []
            existing_analysis.analysis_model = analysis_model
            existing_analysis.processing_time_seconds = processing_time_seconds
            existing_analysis.updated_at = datetime.now(timezone.utc)
            
            session.commit()
            session.refresh(existing_analysis)
            return existing_analysis
        else:
            # Create new analysis
            new_analysis = CommentSentimentAnalysis(
                video_id=video_id,
                video_title=video_title,
                overall_sentiment=overall_sentiment,
                sentiment_score=sentiment_score,
                confidence_score=confidence_score,
                positive_count=positive_count,
                negative_count=negative_count,
                neutral_count=neutral_count,
                total_comments_analyzed=total_comments_analyzed,
                key_action_items=key_action_items or [],
                suggestions=suggestions or [],
                main_themes=main_themes or [],
                ai_analysis=ai_analysis,
                top_positive_comments=top_positive_comments or [],
                top_negative_comments=top_negative_comments or [],
                most_liked_comments=most_liked_comments or [],
                analysis_model=analysis_model,
                processing_time_seconds=processing_time_seconds
            )
            
            session.add(new_analysis)
            session.commit()
            session.refresh(new_analysis)
            return new_analysis
    except Exception as e:
        print(f"Error saving comment sentiment analysis: {str(e)}")
        session.rollback()
        return None
    finally:
        session.close()

def get_comment_sentiment_analysis(video_id: str) -> Optional[CommentSentimentAnalysis]:
    """Get comment sentiment analysis for a video"""
    session = SessionLocal()
    try:
        return session.query(CommentSentimentAnalysis).filter_by(video_id=video_id).first()
    except Exception as e:
        print(f"Error getting comment sentiment analysis: {str(e)}")
        return None
    finally:
        session.close()

def get_all_comment_sentiment_analyses(limit: int = 100) -> List[CommentSentimentAnalysis]:
    """Get all comment sentiment analyses, ordered by creation date"""
    session = SessionLocal()
    try:
        return session.query(CommentSentimentAnalysis).order_by(
            CommentSentimentAnalysis.created_at.desc()
        ).limit(limit).all()
    except Exception as e:
        print(f"Error getting all comment sentiment analyses: {str(e)}")
        return []
    finally:
        session.close()

def delete_comment_sentiment_analysis(video_id: str) -> bool:
    """Delete comment sentiment analysis for a video"""
    session = SessionLocal()
    try:
        analysis = session.query(CommentSentimentAnalysis).filter_by(video_id=video_id).first()
        if analysis:
            session.delete(analysis)
            session.commit()
            return True
        return False
    except Exception as e:
        print(f"Error deleting comment sentiment analysis: {str(e)}")
        session.rollback()
        return False
    finally:
        session.close()

def get_sentiment_summary(video_id: str) -> Optional[Dict]:
    """Get a summary of sentiment analysis for a video"""
    session = SessionLocal()
    try:
        analysis = session.query(CommentSentimentAnalysis).filter_by(video_id=video_id).first()
        if analysis:
            return {
                "video_id": analysis.video_id,
                "overall_sentiment": analysis.overall_sentiment.value,
                "sentiment_score": analysis.sentiment_score,
                "total_comments": analysis.total_comments_analyzed,
                "last_analyzed": analysis.updated_at.isoformat() if analysis.updated_at else analysis.created_at.isoformat(),
                "has_action_items": len(analysis.key_action_items or []) > 0
            }
        return None
    except Exception as e:
        print(f"Error getting sentiment summary: {str(e)}")
        return None
    finally:
        session.close()

def get_videos_with_sentiment_summaries(video_ids: List[str]) -> Dict[str, Dict]:
    """Get sentiment summaries for multiple videos"""
    session = SessionLocal()
    try:
        analyses = session.query(CommentSentimentAnalysis).filter(
            CommentSentimentAnalysis.video_id.in_(video_ids)
        ).all()
        
        result = {}
        for analysis in analyses:
            result[analysis.video_id] = {
                "video_id": analysis.video_id,
                "overall_sentiment": analysis.overall_sentiment.value,
                "sentiment_score": analysis.sentiment_score,
                "total_comments": analysis.total_comments_analyzed,
                "last_analyzed": analysis.updated_at.isoformat() if analysis.updated_at else analysis.created_at.isoformat(),
                "has_action_items": len(analysis.key_action_items or []) > 0
            }
        return result
    except Exception as e:
        print(f"Error getting videos with sentiment summaries: {str(e)}")
        return {}
    finally:
        session.close()

# ================================
# Saved YouTube Channel Management Functions
# ================================

def save_youtube_channel(
    channel_url: str,
    channel_id: str,
    channel_name: str = None,
    subscriber_count: int = None,
    description: str = None,
    thumbnail_url: str = None,
    tags: List[str] = None,
    notes: str = None,
    priority: int = 1,
    max_videos_override: int = None,
    days_back_override: int = None
) -> Optional[SavedYouTubeChannel]:
    """
    Save a YouTube channel to the database for persistent monitoring.
    If channel already exists, update its metadata.
    """
    session = SessionLocal()
    try:
        # Check if channel already exists
        existing_channel = session.query(SavedYouTubeChannel).filter_by(channel_url=channel_url).first()
        
        if existing_channel:
            # Update existing channel
            existing_channel.channel_id = channel_id
            existing_channel.channel_name = channel_name or existing_channel.channel_name
            existing_channel.subscriber_count = subscriber_count or existing_channel.subscriber_count
            existing_channel.description = description or existing_channel.description
            existing_channel.thumbnail_url = thumbnail_url or existing_channel.thumbnail_url
            existing_channel.tags = tags or existing_channel.tags
            existing_channel.notes = notes or existing_channel.notes
            existing_channel.priority = priority
            existing_channel.max_videos_override = max_videos_override
            existing_channel.days_back_override = days_back_override
            existing_channel.updated_at = datetime.now(timezone.utc)
            existing_channel.last_fetched_at = datetime.now(timezone.utc)
            
            session.commit()
            session.refresh(existing_channel)
            return existing_channel
        else:
            # Create new channel
            new_channel = SavedYouTubeChannel(
                channel_url=channel_url,
                channel_id=channel_id,
                channel_name=channel_name,
                subscriber_count=subscriber_count,
                description=description,
                thumbnail_url=thumbnail_url,
                tags=tags,
                notes=notes,
                priority=priority,
                max_videos_override=max_videos_override,
                days_back_override=days_back_override,
                last_fetched_at=datetime.now(timezone.utc)
            )
            
            session.add(new_channel)
            session.commit()
            session.refresh(new_channel)
            return new_channel
            
    except Exception as e:
        print(f"Error saving YouTube channel: {e}")
        session.rollback()
        return None
    finally:
        session.close()

def get_saved_youtube_channels(active_only: bool = True) -> List[SavedYouTubeChannel]:
    """
    Get all saved YouTube channels, optionally filtering by active status.
    """
    session = SessionLocal()
    try:
        query = session.query(SavedYouTubeChannel)
        
        if active_only:
            query = query.filter(SavedYouTubeChannel.is_active == True)
        
        return query.order_by(SavedYouTubeChannel.priority.asc(), SavedYouTubeChannel.created_at.desc()).all()
        
    except Exception as e:
        print(f"Error getting saved YouTube channels: {e}")
        return []
    finally:
        session.close()

def get_saved_youtube_channel(channel_url: str = None, channel_id: str = None) -> Optional[SavedYouTubeChannel]:
    """
    Get a specific saved YouTube channel by URL or channel ID.
    """
    session = SessionLocal()
    try:
        if channel_url:
            return session.query(SavedYouTubeChannel).filter_by(channel_url=channel_url).first()
        elif channel_id:
            return session.query(SavedYouTubeChannel).filter_by(channel_id=channel_id).first()
        else:
            return None
            
    except Exception as e:
        print(f"Error getting saved YouTube channel: {e}")
        return None
    finally:
        session.close()

def update_saved_youtube_channel(
    channel_url: str,
    **kwargs
) -> Optional[SavedYouTubeChannel]:
    """
    Update a saved YouTube channel with new data.
    """
    session = SessionLocal()
    try:
        channel = session.query(SavedYouTubeChannel).filter_by(channel_url=channel_url).first()
        
        if not channel:
            return None
        
        # Update allowed fields
        allowed_fields = [
            'channel_name', 'subscriber_count', 'description', 'thumbnail_url',
            'is_active', 'priority', 'tags', 'notes', 'max_videos_override',
            'days_back_override', 'last_analyzed_at', 'total_videos_found',
            'last_video_count', 'avg_videos_per_analysis'
        ]
        
        for key, value in kwargs.items():
            if key in allowed_fields and hasattr(channel, key):
                setattr(channel, key, value)
        
        channel.updated_at = datetime.now(timezone.utc)
        
        session.commit()
        session.refresh(channel)
        return channel
        
    except Exception as e:
        print(f"Error updating saved YouTube channel: {e}")
        session.rollback()
        return None
    finally:
        session.close()

def delete_saved_youtube_channel(channel_url: str) -> bool:
    """
    Delete a saved YouTube channel from the database.
    """
    session = SessionLocal()
    try:
        channel = session.query(SavedYouTubeChannel).filter_by(channel_url=channel_url).first()
        
        if channel:
            session.delete(channel)
            session.commit()
            return True
        
        return False
        
    except Exception as e:
        print(f"Error deleting saved YouTube channel: {e}")
        session.rollback()
        return False
    finally:
        session.close()

def toggle_saved_youtube_channel_status(channel_url: str) -> Optional[SavedYouTubeChannel]:
    """
    Toggle the active status of a saved YouTube channel.
    """
    session = SessionLocal()
    try:
        channel = session.query(SavedYouTubeChannel).filter_by(channel_url=channel_url).first()
        
        if channel:
            channel.is_active = not channel.is_active
            channel.updated_at = datetime.now(timezone.utc)
            
            session.commit()
            session.refresh(channel)
            return channel
        
        return None
        
    except Exception as e:
        print(f"Error toggling saved YouTube channel status: {e}")
        session.rollback()
        return None
    finally:
        session.close()

def update_channel_analysis_stats(
    channel_url: str,
    video_count: int,
    analysis_datetime: datetime = None
) -> Optional[SavedYouTubeChannel]:
    """
    Update statistics for a channel after analysis.
    """
    session = SessionLocal()
    try:
        channel = session.query(SavedYouTubeChannel).filter_by(channel_url=channel_url).first()
        
        if not channel:
            return None
        
        # Update stats
        channel.last_video_count = video_count
        channel.total_videos_found += video_count
        channel.last_analyzed_at = analysis_datetime or datetime.now(timezone.utc)
        
        # Calculate average videos per analysis
        total_analyses = session.query(SavedYouTubeChannel).filter(
            SavedYouTubeChannel.channel_url == channel_url,
            SavedYouTubeChannel.last_analyzed_at.isnot(None)
        ).count()
        
        if total_analyses > 0:
            channel.avg_videos_per_analysis = channel.total_videos_found / total_analyses
        
        session.commit()
        session.refresh(channel)
        return channel
        
    except Exception as e:
        print(f"Error updating channel analysis stats: {e}")
        session.rollback()
        return None
    finally:
        session.close()

def get_channel_urls_for_analysis(active_only: bool = True) -> List[str]:
    """
    Get a list of channel URLs that should be included in analysis.
    Returns them ordered by priority (1=highest priority).
    """
    session = SessionLocal()
    try:
        query = session.query(SavedYouTubeChannel.channel_url)
        
        if active_only:
            query = query.filter(SavedYouTubeChannel.is_active == True)
        
        channels = query.order_by(SavedYouTubeChannel.priority.asc()).all()
        return [channel[0] for channel in channels]
        
    except Exception as e:
        print(f"Error getting channel URLs for analysis: {e}")
        return []
    finally:
        session.close()