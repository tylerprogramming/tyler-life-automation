import os
from agents import Agent, Runner
from models.linkedin import LinkedinOutput

PROMPT_PATH = os.path.join(os.path.dirname(__file__), 'prompts', 'linkedin.txt')
with open(PROMPT_PATH, 'r', encoding='utf-8') as f:
    LINKEDIN_PROMPT = f.read()

UPDATE_PROMPT_PATH = os.path.join(os.path.dirname(__file__), 'prompts', 'linkedin_update.txt')
with open(UPDATE_PROMPT_PATH, 'r', encoding='utf-8') as f:
    LINKEDIN_UPDATE_PROMPT = f.read()

linkedin_agent = Agent(
    name="Linkedin Agent",
    instructions=LINKEDIN_PROMPT,
    output_type=LinkedinOutput,
)

linkedin_update_agent = Agent(
    name="Linkedin Update Agent",
    instructions=LINKEDIN_UPDATE_PROMPT,
    output_type=LinkedinOutput,
)

async def linkedin_agent_runner(input_data):
    result = await Runner.run(linkedin_agent, input_data)
    final_output = result.final_output_as(LinkedinOutput)
    return final_output

async def linkedin_update_agent_runner(original_markdown, current_commentary):
    input_text = f"Original Markdown:\n{original_markdown}\n\nCurrent Commentary:\n{current_commentary}"
    result = await Runner.run(linkedin_update_agent, input_text)
    final_output = result.final_output_as(LinkedinOutput)
    return final_output