from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from services import database as database_service

from routes.social_routes import router as social_router
from routes.social_instagram import router as social_instagram_router
from routes.social_twitter import router as social_twitter_router
from routes.social_linkedin import router as social_linkedin_router
from routes.social_youtube import router as social_youtube_router
from routes.content import router as content_router
from routes.dashboard import router as dashboard_router
from routes.calendar import router as calendar_router
from routes.google_calendar import router as google_calendar_router

from psycopg2 import OperationalError

import time

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the social routes
app.include_router(content_router, prefix="/content", tags=["Content"])
app.include_router(social_router, tags=["Socials"])
app.include_router(social_instagram_router, prefix="/instagram", tags=["Instagram"])
app.include_router(social_twitter_router, prefix="/twitter", tags=["Twitter"])
app.include_router(social_linkedin_router, prefix="/linkedin", tags=["LinkedIn"])
app.include_router(social_youtube_router, prefix="/youtube", tags=["YouTube"])
app.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard"])
app.include_router(calendar_router, prefix="/calendar", tags=["Calendar"])
app.include_router(google_calendar_router, prefix="/google-calendar", tags=["Google Calendar"])

MAX_RETRIES = 10
for i in range(MAX_RETRIES):
    try:
        database_service.init_db()
        print("Database initialized successfully.")
        break
    except OperationalError as e:
        print(f"Database not ready (attempt {i+1}/{MAX_RETRIES}): {e}")
        time.sleep(3)
else:
    raise Exception("Database not available after multiple attempts.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000) 