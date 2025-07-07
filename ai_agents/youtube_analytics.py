import os
from agents import Agent, Runner
from models.youtube import YouTubeOutput
from dotenv import load_dotenv

load_dotenv()

PROMPT_PATH = os.path.join(os.path.dirname(__file__), 'prompts', 'youtube_analytics_channel.txt')
with open(PROMPT_PATH, 'r', encoding='utf-8') as f:
    YOUTUBE_PROMPT = f.read()

youtube_analytics_channel_agent = Agent(
    name="YouTube Analytics Channel Agent",
    model="o3",
    instructions=YOUTUBE_PROMPT,
    output_type=YouTubeOutput,
)

async def youtube_analytics_channel_agent_runner(input_data):
    result = await Runner.run(youtube_analytics_channel_agent, input_data)
    final_output = result.final_output
    return final_output