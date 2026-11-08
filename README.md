# tyler-life-automation

A FastAPI backend for running a creator's social media from one place:
- Writes posts with AI and stores them.
- Publishes to X, LinkedIn and Instagram.
- Transcribes your exported YouTube videos and drafts their descriptions.
- Reads and pins YouTube comments, and analyzes channels.
- Keeps a content calendar, with a daily Telegram summary.

It runs as five Docker Compose services: the API, a Celery worker, Celery beat, Redis and Postgres. A sixth service, ngrok, exposes the API for OAuth callbacks.

There is no frontend in this repo. The API is meant to be called by a separate dashboard.

## What is in here

- `social_server.py`: the FastAPI app (port 9000). It mounts these routers:
  - `/content`: generate, save and improve posts
  - `/post_socials`
  - `/instagram`, `/twitter`, `/linkedin`
  - `/youtube`: transcriptions, descriptions, comments, multi-channel analysis
  - `/dashboard`
  - `/calendar` and `/google-calendar`
- `routes/`: one router per area. `routes/_with_facebooklogin_instagram.py` is an older Facebook-login variant and is not mounted.
- `services/`: API clients, the database layer (`services/database.py`) and Celery tasks (`services/tasks.py`).
- `ai_agents/`: OpenAI Agents SDK agents for each platform, with prompts in `ai_agents/prompts/`. The shared model is set in `ai_agents/model_config.py`.
- `models/`: Pydantic request models and the SQLAlchemy tables (`models/db_models.py`).
- `setup_youtube_oauth.py`, `simple_auth.py`: one-time Google OAuth helpers for YouTube and Google Calendar.
- `_guides/`: deeper setup notes:
  - [YouTube OAuth](_guides/OAUTH_SETUP_GUIDE.md)
  - [multi-channel analysis](_guides/MULTI_CHANNEL_GUIDE.md)
  - [Instagram OAuth](_guides/INSTAGRAM_OAUTH_SETUP.md)
  - [Instagram frontend flow](_guides/INSTAGRAM_FRONTEND_INTEGRATION.md)

## Run it

Requirements: Docker with Compose. The image installs Python 3.11 and ffmpeg itself.

1. Create `.env` in the repo root. Compose reads it for the `${...}` values below. `.env` is gitignored.

   ```bash
   # used by docker-compose.yml
   DATABASE_URL=postgresql://postgres_tyler:postgres_123!@db:5432/socialmedia_db
   CELERY_BROKER_URL=redis://redis:6379/0
   OPENAI_API_KEY=
   NGROK_AUTHTOKEN=

   # read by the app code (only the ones for the features you use)
   FIRECRAWL_API_KEY=
   YOUTUBE_API_KEY=
   TWITTER_API_KEY=
   TWITTER_API_SECRET=
   TWITTER_ACCESS_TOKEN=
   TWITTER_ACCESS_SECRET=
   TWITTER_BEARER_TOKEN=
   LINKEDIN_ACCESS_TOKEN=
   INSTAGRAM_CLIENT_ID=
   INSTAGRAM_CLIENT_SECRET=
   INSTAGRAM_ACCESS_TOKEN=
   INSTAGRAM_ACCOUNT_ID=
   INSTAGRAM_ENCRYPTION_KEY=
   HOST_URL=
   LATEST_API_VERSION=
   FRONTEND_URL=
   TELEGRAM_BOT_TOKEN=
   TELEGRAM_CHAT_ID=
   ```

   The `DATABASE_URL` shown matches the `db` service credentials in `docker-compose.yml`. Change both together if you change one.

2. Edit `docker-compose.yml` for your machine. It is written for the author's setup:
   - `fastapi.volumes` mounts `/Volumes/TylerYouTube/exported_final_videos` at `/app/videos`. `/youtube/transcribe_local_video` reads videos from there. Point it at your own export folder.
   - `fastapi.volumes` also mounts `./google-credentials.json`. Create that file, or remove the line. If the file is missing, Docker creates an empty directory in its place.
   - `ngrok.command` uses a reserved domain, `choice-entirely-coyote.ngrok-free.app`, and `routes/social_instagram.py` hardcodes the same `BASE_URL`. Replace both with your own ngrok domain, or remove the ngrok service if you do not need Instagram OAuth.

3. Start everything:

   ```bash
   docker compose up --build
   ```

   The API waits for Postgres (up to 10 tries, 3 s apart), creates the tables, and serves on `http://localhost:9000`. Interactive docs are at `http://localhost:9000/docs`.

## Google credentials

OAuth files are gitignored (`credentials.json`, `credentials/`, `youtube_credentials/`). The code reads them from these paths:

- YouTube comments (`services/youtube_comments.py`): `credentials/client_secrets.json`, with the token written to `credentials/token.json`.
- `setup_youtube_oauth.py` uses `youtube_credentials/client_secrets.json` and `youtube_credentials/token.json`. Its paths differ from `services/youtube_comments.py`, so copy the token across after running it.
- Google Calendar (`services/google_calendar.py`): `credentials/credentials.json` (or `credentials.json` in the root). It reads the token from `credentials/token.json` but writes a refreshed one to `token.json` in the root, so move it into `credentials/` after the first login.

Run the OAuth helpers on your host. They open a browser.

## Scheduled job

`celery_beat` runs `send_telegram_message` every day at 06:00 (`services/tasks.py`). It sends that day's calendar events to `TELEGRAM_CHAT_ID`.

## Notes

- The image build copies the whole repo (`COPY . .`), and `.dockerignore` does not exclude `.env` or `credentials/`. So the API container reads its keys from the copied `.env`, but the keys also end up inside the image. Do not push the image to a public registry.
- `requirements.txt` is unpinned, so each build installs the latest releases.
- `services/youtube_transcription.py` uses `whisper-1` with segment timestamps. OpenAI shuts `whisper-1` down on 2027-02-26, and its replacement does not return timestamps.
