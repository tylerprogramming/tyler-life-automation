from fastapi import APIRouter, HTTPException
from services import instagram as instagram_service
from models.instagram import InstagramPostCreate, InstagramPostUpdate
import requests

router = APIRouter()

@router.post("/post_instagram_image")
async def post_instagram_image_route(image_urls: list[str]):
    return await instagram_service.post_instagram_image(image_urls)

@router.post("/post_instagram_reels")
async def post_instagram_reels_route(video_url: str):
    return await instagram_service.create_reels_container(video_url)

@router.post("/publish_instagram_container")
async def publish_instagram_container_route(container_id: str):
    return await instagram_service.publish_media_to_instagram(container_id)

@router.post("/poll_container_status")
async def poll_container_status_route(container_id: str):
    return await instagram_service.poll_until_ready(container_id)

@router.get("/refresh_instagram_access_token")
async def refresh_instagram_access_token_route():
    return instagram_service.refresh_instagram_access_token()

@router.get("/instagram_posts")
def get_all_instagram_posts():
    posts = instagram_service.get_all_instagram_posts()
    return posts

@router.get("/instagram_posts/{post_id}")
def get_instagram_post(post_id: int):
    post = instagram_service.get_instagram_post_by_id(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Instagram post not found")
    return post

@router.put("/instagram_posts/{post_id}")
def update_instagram_post(post_id: int, update_data: InstagramPostUpdate):
    updated = instagram_service.update_instagram_post(post_id, update_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Instagram post not found")
    return updated

@router.delete("/instagram_posts/{post_id}")
def delete_instagram_post(post_id: int):
    deleted = instagram_service.delete_instagram_post(post_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Instagram post not found")
    return {"success": True}