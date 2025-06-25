import os
from agents import Agent, Runner
from models.youtube import YouTubeOutput
from dotenv import load_dotenv

load_dotenv()

PROMPT_PATH = os.path.join(os.path.dirname(__file__), 'prompts', 'youtube.txt')
with open(PROMPT_PATH, 'r', encoding='utf-8') as f:
    YOUTUBE_PROMPT = f.read()

UPDATE_PROMPT_PATH = os.path.join(os.path.dirname(__file__), 'prompts', 'youtube_update.txt')
with open(UPDATE_PROMPT_PATH, 'r', encoding='utf-8') as f:
    YOUTUBE_UPDATE_PROMPT = f.read()

youtube_description_agent = Agent(
    name="YouTube Agent",
    model="o3",
    instructions=YOUTUBE_PROMPT,
    output_type=YouTubeOutput,
)

youtube_update_agent = Agent(
    name="YouTube Update Agent",
    model="o3",
    instructions=YOUTUBE_UPDATE_PROMPT,
    output_type=YouTubeOutput,
)

async def youtube_agent_runner(input_data):
    timestamped_transcription = f"Timestamped Transcription: {input_data}"
    result = await Runner.run(youtube_description_agent, timestamped_transcription)
    final_output = result.final_output
    return final_output

async def youtube_update_agent_runner(original_markdown, current_description):
    input_text = f"Original Markdown:\n{original_markdown}\n\nCurrent Description:\n{current_description}"
    result = await Runner.run(youtube_update_agent, input_text)
    final_output = result.final_output
    return final_output