import os
from agents import Agent, Runner
from models.twitter import TwitterOutput
from models.ai_improve import TwitterImproved

PROMPT_PATH = os.path.join(os.path.dirname(__file__), 'prompts', 'x.txt')
with open(PROMPT_PATH, 'r', encoding='utf-8') as f:
    X_PROMPT = f.read()

UPDATE_PROMPT_PATH = os.path.join(os.path.dirname(__file__), 'prompts', 'x_update.txt')
with open(UPDATE_PROMPT_PATH, 'r', encoding='utf-8') as f:
    X_UPDATE_PROMPT = f.read()

twitter_agent = Agent(
    name="Twitter Agent",
    model="o3",
    instructions=X_PROMPT,
    output_type=TwitterOutput,
)

twitter_update_agent = Agent(
    name="Twitter Update Agent",
    model="o3",
    instructions=X_UPDATE_PROMPT,
    output_type=TwitterOutput,
)

async def twitter_agent_runner(input_data):
    result = await Runner.run(twitter_agent, input_data)
    final_output = result.final_output_as(TwitterOutput)
    return final_output

async def twitter_update_agent_runner(input_data):
    result = await Runner.run(twitter_update_agent, input_data)
    final_output = result.final_output_as(TwitterImproved)
    return final_output