"""
Advanced AI-powered comment sentiment analysis service for YouTube videos.
This service provides comprehensive sentiment analysis including:
- Overall sentiment classification (positive, negative, neutral)
- Detailed sentiment scoring and confidence metrics
- Key action items and suggestions based on comments
- Main themes and patterns in viewer feedback
- Sample comments for each sentiment category
"""

import os
import json
import time
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone

from models.youtube_analytics import (
    CommentSentimentAnalysisResult,
    CommentSample,
    SentimentType
)
from models.db_models import SentimentType as DBSentimentType
from services import database as db_service

# Import OpenAI as backup
try:
    from openai import OpenAI
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Import Gemini AI
try:
    import google.generativeai as genai
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

class CommentSentimentAnalyzer:
    """
    Advanced AI-powered comment sentiment analyzer with comprehensive insights.
    """
    
    def __init__(self, use_gemini: bool = True):
        self.use_gemini = use_gemini and GEMINI_AVAILABLE
        self.gemini_model = None
        self.openai_client = None
        
        if self.use_gemini and GEMINI_AVAILABLE:
            self.gemini_model = genai.GenerativeModel('gemini-pro')
        elif OPENAI_AVAILABLE:
            self.openai_client = openai_client
            self.use_gemini = False
        
        self.model_name = "gemini-pro" if self.use_gemini else "gpt-4"
    
    def _ensure_ai_available(self):
        """Ensure AI service is available."""
        if not self.use_gemini and not OPENAI_AVAILABLE:
            raise Exception("No AI service available. Please install google-generativeai or openai package and set appropriate API keys.")
    
    def _generate_ai_response(self, prompt: str) -> str:
        """Generate AI response using available service."""
        self._ensure_ai_available()
        
        try:
            if self.use_gemini and self.gemini_model:
                response = self.gemini_model.generate_content(prompt)
                return response.text
            elif self.openai_client:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=3000,
                    temperature=0.3
                )
                return response.choices[0].message.content
            else:
                raise Exception("No AI service available")
        except Exception as e:
            return f"Error generating AI response: {str(e)}"
    
    def _prepare_comments_for_analysis(self, comments: List[Dict]) -> str:
        """Prepare comments data for AI analysis."""
        comment_data = []
        for comment in comments:
            comment_data.append({
                "id": comment.get("comment_id", ""),
                "author": comment.get("author", ""),
                "text": comment.get("text", ""),
                "likes": comment.get("like_count", 0),
                "published": comment.get("published_at", ""),
                "replies": len(comment.get("replies", []))
            })
        return json.dumps(comment_data, indent=2)
    
    def _parse_ai_sentiment_response(self, ai_response: str) -> Dict[str, Any]:
        """Parse AI response to extract structured sentiment data."""
        try:
            # Try to find JSON in the response
            start = ai_response.find('{')
            end = ai_response.rfind('}')
            if start != -1 and end != -1:
                json_str = ai_response[start:end+1]
                return json.loads(json_str)
        except:
            pass
        
        # Fallback to manual parsing
        result = {
            "sentiment_score": 0.0,
            "confidence_score": 0.5,
            "positive_count": 0,
            "negative_count": 0,
            "neutral_count": 0,
            "key_action_items": [],
            "suggestions": [],
            "main_themes": [],
            "ai_analysis": ai_response
        }
        
        lines = ai_response.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Look for numeric values
            if 'sentiment score' in line.lower():
                try:
                    score = float(line.split(':')[-1].strip())
                    result["sentiment_score"] = max(-1, min(1, score))
                except:
                    pass
            elif 'confidence' in line.lower():
                try:
                    confidence = float(line.split(':')[-1].strip())
                    result["confidence_score"] = max(0, min(1, confidence))
                except:
                    pass
            elif 'positive:' in line.lower():
                try:
                    count = int(line.split(':')[-1].strip())
                    result["positive_count"] = max(0, count)
                except:
                    pass
            elif 'negative:' in line.lower():
                try:
                    count = int(line.split(':')[-1].strip())
                    result["negative_count"] = max(0, count)
                except:
                    pass
            elif 'neutral:' in line.lower():
                try:
                    count = int(line.split(':')[-1].strip())
                    result["neutral_count"] = max(0, count)
                except:
                    pass
            
            # Look for sections
            if 'action items' in line.lower():
                current_section = 'action_items'
            elif 'suggestions' in line.lower():
                current_section = 'suggestions'
            elif 'main themes' in line.lower() or 'themes' in line.lower():
                current_section = 'themes'
            elif line.startswith('- ') or line.startswith('• '):
                item = line[2:].strip()
                if current_section == 'action_items':
                    result["key_action_items"].append(item)
                elif current_section == 'suggestions':
                    result["suggestions"].append(item)
                elif current_section == 'themes':
                    result["main_themes"].append(item)
        
        return result
    
    def _categorize_comments_by_sentiment(self, comments: List[Dict], ai_response: str) -> Tuple[List[CommentSample], List[CommentSample], List[CommentSample]]:
        """Categorize comments by sentiment based on AI analysis."""
        positive_comments = []
        negative_comments = []
        most_liked_comments = []
        
        # Sort comments by likes
        sorted_comments = sorted(comments, key=lambda x: x.get("like_count", 0), reverse=True)
        
        # Get top liked comments
        for comment in sorted_comments[:5]:
            most_liked_comments.append(CommentSample(
                comment_id=comment.get("comment_id", ""),
                author=comment.get("author", ""),
                text=comment.get("text", "")[:200] + "..." if len(comment.get("text", "")) > 200 else comment.get("text", ""),
                like_count=comment.get("like_count", 0),
                published_at=comment.get("published_at", ""),
                sentiment_score=None
            ))
        
        # Simple sentiment categorization based on keywords and patterns
        positive_keywords = ["great", "amazing", "awesome", "fantastic", "excellent", "perfect", "love", "wonderful", "brilliant", "helpful", "thanks", "thank you", "good job", "well done", "inspiring", "motivating"]
        negative_keywords = ["bad", "terrible", "awful", "hate", "stupid", "boring", "worst", "horrible", "disappointing", "waste", "useless", "confusing", "wrong", "misleading", "annoying"]
        
        for comment in comments:
            text = comment.get("text", "").lower()
            
            # Count positive/negative indicators
            positive_score = sum(1 for keyword in positive_keywords if keyword in text)
            negative_score = sum(1 for keyword in negative_keywords if keyword in text)
            
            comment_sample = CommentSample(
                comment_id=comment.get("comment_id", ""),
                author=comment.get("author", ""),
                text=comment.get("text", "")[:200] + "..." if len(comment.get("text", "")) > 200 else comment.get("text", ""),
                like_count=comment.get("like_count", 0),
                published_at=comment.get("published_at", ""),
                sentiment_score=round((positive_score - negative_score) / max(len(text.split()), 1), 2)
            )
            
            if positive_score > negative_score:
                positive_comments.append(comment_sample)
            elif negative_score > positive_score:
                negative_comments.append(comment_sample)
        
        # Sort and limit results
        positive_comments.sort(key=lambda x: x.like_count, reverse=True)
        negative_comments.sort(key=lambda x: x.like_count, reverse=True)
        
        return positive_comments[:5], negative_comments[:5], most_liked_comments
    
    def analyze_video_comments(
        self, 
        video_id: str, 
        video_title: str, 
        comments: List[Dict],
        include_replies: bool = True,
        max_comments: int = 200
    ) -> CommentSentimentAnalysisResult:
        """
        Perform comprehensive sentiment analysis on video comments.
        
        Args:
            video_id: YouTube video ID
            video_title: Title of the video
            comments: List of comment dictionaries
            include_replies: Whether to include replies in analysis
            max_comments: Maximum number of comments to analyze
            
        Returns:
            CommentSentimentAnalysisResult with comprehensive analysis
        """
        start_time = time.time()
        
        if not comments:
            return CommentSentimentAnalysisResult(
                video_id=video_id,
                video_title=video_title,
                overall_sentiment=SentimentType.NEUTRAL,
                sentiment_score=0.0,
                confidence_score=0.0,
                positive_count=0,
                negative_count=0,
                neutral_count=0,
                total_comments_analyzed=0,
                key_action_items=["No comments available for analysis"],
                suggestions=["Encourage viewers to leave comments to get feedback"],
                main_themes=["No comments to analyze"],
                ai_analysis="No comments available for analysis",
                analysis_model=self.model_name,
                processing_time_seconds=time.time() - start_time
            )
        
        # Limit comments for analysis
        comments_to_analyze = comments[:max_comments]
        total_comments = len(comments_to_analyze)
        
        # Prepare comprehensive AI prompt
        comments_data = self._prepare_comments_for_analysis(comments_to_analyze)
        
        ai_prompt = f"""
        Analyze the sentiment of these YouTube video comments for the video "{video_title}".
        
        Please provide a comprehensive analysis including:
        
        1. SENTIMENT METRICS:
           - Overall sentiment score (-1 to 1, where -1 is most negative, 1 is most positive)
           - Confidence score (0-1, how confident you are in the analysis)
           - Count of positive, negative, and neutral comments
        
        2. KEY ACTION ITEMS:
           - Specific, actionable steps the creator can take based on viewer feedback
           - Address common concerns or questions raised in comments
           - Suggestions for content improvements
        
        3. SUGGESTIONS:
           - Recommendations for engaging with the audience
           - Ideas for future content based on viewer interests
           - Ways to improve viewer satisfaction
        
        4. MAIN THEMES:
           - Common topics or themes discussed in comments
           - Recurring feedback patterns
           - Viewer interests and preferences
        
        5. DETAILED ANALYSIS:
           - Summary of overall viewer reception
           - Notable patterns in engagement
           - Specific insights about audience behavior
        
        Comments Data ({total_comments} comments):
        {comments_data}
        
        Please structure your response with clear sections for each component above.
        Focus on providing actionable insights that can help the creator improve their content and engagement.
        """
        
        # Generate AI analysis
        ai_response = self._generate_ai_response(ai_prompt)
        
        # Parse AI response
        parsed_data = self._parse_ai_sentiment_response(ai_response)
        
        # Categorize comments
        positive_samples, negative_samples, most_liked_samples = self._categorize_comments_by_sentiment(
            comments_to_analyze, ai_response
        )
        
        # Determine overall sentiment
        sentiment_score = parsed_data.get("sentiment_score", 0.0)
        if sentiment_score > 0.2:
            overall_sentiment = SentimentType.POSITIVE
        elif sentiment_score < -0.2:
            overall_sentiment = SentimentType.NEGATIVE
        else:
            overall_sentiment = SentimentType.NEUTRAL
        
        # Ensure counts make sense
        positive_count = parsed_data.get("positive_count", len(positive_samples))
        negative_count = parsed_data.get("negative_count", len(negative_samples))
        neutral_count = max(0, total_comments - positive_count - negative_count)
        
        processing_time = time.time() - start_time
        
        return CommentSentimentAnalysisResult(
            video_id=video_id,
            video_title=video_title,
            overall_sentiment=overall_sentiment,
            sentiment_score=sentiment_score,
            confidence_score=parsed_data.get("confidence_score", 0.5),
            positive_count=positive_count,
            negative_count=negative_count,
            neutral_count=neutral_count,
            total_comments_analyzed=total_comments,
            key_action_items=parsed_data.get("key_action_items", []),
            suggestions=parsed_data.get("suggestions", []),
            main_themes=parsed_data.get("main_themes", []),
            ai_analysis=ai_response,
            top_positive_comments=positive_samples,
            top_negative_comments=negative_samples,
            most_liked_comments=most_liked_samples,
            analysis_model=self.model_name,
            processing_time_seconds=round(processing_time, 2),
            created_at=datetime.now(timezone.utc).isoformat(),
            updated_at=datetime.now(timezone.utc).isoformat()
        )
    
    def save_analysis_to_database(self, analysis: CommentSentimentAnalysisResult) -> bool:
        """Save sentiment analysis results to database."""
        try:
            # Convert SentimentType to DBSentimentType
            db_sentiment = DBSentimentType.POSITIVE if analysis.overall_sentiment == SentimentType.POSITIVE else \
                          DBSentimentType.NEGATIVE if analysis.overall_sentiment == SentimentType.NEGATIVE else \
                          DBSentimentType.NEUTRAL
            
            # Convert comment samples to dictionaries
            top_positive = [sample.model_dump() for sample in analysis.top_positive_comments]
            top_negative = [sample.model_dump() for sample in analysis.top_negative_comments]
            most_liked = [sample.model_dump() for sample in analysis.most_liked_comments]
            
            result = db_service.save_comment_sentiment_analysis(
                video_id=analysis.video_id,
                video_title=analysis.video_title,
                overall_sentiment=db_sentiment,
                sentiment_score=analysis.sentiment_score,
                positive_count=analysis.positive_count,
                negative_count=analysis.negative_count,
                neutral_count=analysis.neutral_count,
                total_comments_analyzed=analysis.total_comments_analyzed,
                key_action_items=analysis.key_action_items,
                suggestions=analysis.suggestions,
                main_themes=analysis.main_themes,
                ai_analysis=analysis.ai_analysis,
                top_positive_comments=top_positive,
                top_negative_comments=top_negative,
                most_liked_comments=most_liked,
                analysis_model=analysis.analysis_model,
                processing_time_seconds=analysis.processing_time_seconds,
                confidence_score=analysis.confidence_score
            )
            
            return result is not None
        except Exception as e:
            print(f"Error saving analysis to database: {str(e)}")
            return False

# Global analyzer instance
comment_analyzer = CommentSentimentAnalyzer()

# Service functions for easy access
def analyze_video_comments(
    video_id: str, 
    video_title: str, 
    comments: List[Dict],
    include_replies: bool = True,
    max_comments: int = 200,
    save_to_db: bool = True
) -> CommentSentimentAnalysisResult:
    """
    Analyze video comments and optionally save to database.
    
    Args:
        video_id: YouTube video ID
        video_title: Title of the video
        comments: List of comment dictionaries
        include_replies: Whether to include replies in analysis
        max_comments: Maximum number of comments to analyze
        save_to_db: Whether to save results to database
        
    Returns:
        CommentSentimentAnalysisResult with comprehensive analysis
    """
    analysis = comment_analyzer.analyze_video_comments(
        video_id=video_id,
        video_title=video_title,
        comments=comments,
        include_replies=include_replies,
        max_comments=max_comments
    )
    
    if save_to_db:
        comment_analyzer.save_analysis_to_database(analysis)
    
    return analysis

def get_sentiment_analysis_from_db(video_id: str) -> Optional[CommentSentimentAnalysisResult]:
    """Get existing sentiment analysis from database."""
    try:
        db_analysis = db_service.get_comment_sentiment_analysis(video_id)
        if not db_analysis:
            return None
        
        # Convert database model to API model
        sentiment_type = SentimentType.POSITIVE if db_analysis.overall_sentiment == DBSentimentType.POSITIVE else \
                       SentimentType.NEGATIVE if db_analysis.overall_sentiment == DBSentimentType.NEGATIVE else \
                       SentimentType.NEUTRAL
        
        # Convert comment samples
        top_positive = [CommentSample(**sample) for sample in db_analysis.top_positive_comments or []]
        top_negative = [CommentSample(**sample) for sample in db_analysis.top_negative_comments or []]
        most_liked = [CommentSample(**sample) for sample in db_analysis.most_liked_comments or []]
        
        return CommentSentimentAnalysisResult(
            video_id=db_analysis.video_id,
            video_title=db_analysis.video_title,
            overall_sentiment=sentiment_type,
            sentiment_score=db_analysis.sentiment_score,
            confidence_score=db_analysis.confidence_score,
            positive_count=db_analysis.positive_count,
            negative_count=db_analysis.negative_count,
            neutral_count=db_analysis.neutral_count,
            total_comments_analyzed=db_analysis.total_comments_analyzed,
            key_action_items=db_analysis.key_action_items or [],
            suggestions=db_analysis.suggestions or [],
            main_themes=db_analysis.main_themes or [],
            ai_analysis=db_analysis.ai_analysis,
            top_positive_comments=top_positive,
            top_negative_comments=top_negative,
            most_liked_comments=most_liked,
            analysis_model=db_analysis.analysis_model,
            processing_time_seconds=db_analysis.processing_time_seconds,
            created_at=db_analysis.created_at.isoformat() if db_analysis.created_at else None,
            updated_at=db_analysis.updated_at.isoformat() if db_analysis.updated_at else None
        )
    except Exception as e:
        print(f"Error getting sentiment analysis from database: {str(e)}")
        return None

def delete_sentiment_analysis(video_id: str) -> bool:
    """Delete sentiment analysis from database."""
    return db_service.delete_comment_sentiment_analysis(video_id) 