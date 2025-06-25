import os
from agents import Agent, Runner
from models.instagram import InstagramOutput
from dotenv import load_dotenv

load_dotenv()

PROMPT_PATH = os.path.join(os.path.dirname(__file__), 'prompts', 'instagram.txt')
with open(PROMPT_PATH, 'r', encoding='utf-8') as f:
    INSTAGRAM_PROMPT = f.read()

UPDATE_PROMPT_PATH = os.path.join(os.path.dirname(__file__), 'prompts', 'instagram_update.txt')
with open(UPDATE_PROMPT_PATH, 'r', encoding='utf-8') as f:
    INSTAGRAM_UPDATE_PROMPT = f.read()

instagram_agent = Agent(
    name="Instagram Agent",
    model="o3-mini",
    instructions=INSTAGRAM_PROMPT,
    output_type=InstagramOutput,
)

instagram_update_agent = Agent(
    name="Instagram Update Agent",
    model="o3-mini",
    instructions=INSTAGRAM_UPDATE_PROMPT,
    output_type=InstagramOutput,
)

async def instagram_agent_runner(input_data):
    transcription = f"Transcription: {input_data}"
    result = await Runner.run(instagram_agent, transcription)
    final_output = result.final_output
    return final_output

async def instagram_update_agent_runner(original_markdown, current_caption):
    input_text = f"Original Markdown:\n{original_markdown}\n\nCurrent Caption:\n{current_caption}"
    result = await Runner.run(instagram_update_agent, input_text)
    final_output = result.final_output
    return final_output