from fastapi import APIRouter, HTTPException
from services import twitter as twitter_service
from models.twitter import TwitterPostCreate, TwitterPostUpdate

router = APIRouter()

@router.post("/post_tweet")
async def post_tweet_route():
    return await twitter_service.post_tweet_service()

@router.get("/twitter_posts")
def get_all_twitter_posts():
    posts = twitter_service.get_all_twitter_posts()
    return posts

@router.get("/twitter_posts/{post_id}")
def get_twitter_post(post_id: int):
    post = twitter_service.get_twitter_post_by_id(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Twitter post not found")
    return post

@router.put("/twitter_posts/{post_id}")
def update_twitter_post(post_id: int, update_data: TwitterPostUpdate):
    updated = twitter_service.update_twitter_post(post_id, update_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Twitter post not found")
    return updated

@router.delete("/twitter_posts/{post_id}")
def delete_twitter_post(post_id: int):
    deleted = twitter_service.delete_twitter_post(post_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Twitter post not found")
    return {"success": True}
