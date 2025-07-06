import os
from agents import Agent, Runner
from models.calendar import CalendarEventOutput
from dotenv import load_dotenv

load_dotenv()

PROMPT_PATH = os.path.join(os.path.dirname(__file__), 'prompts', 'calendar.txt')
with open(PROMPT_PATH, 'r', encoding='utf-8') as f:
    CALENDAR_PROMPT = f.read()

CREATE_FROM_TEXT_PROMPT_PATH = os.path.join(os.path.dirname(__file__), 'prompts', 'calendar_create_from_text.txt')
with open(CREATE_FROM_TEXT_PROMPT_PATH, 'r', encoding='utf-8') as f:
    CALENDAR_PROMPT_CREATE_FROM_TEXT = f.read()

# UPDATE_PROMPT_PATH = os.path.join(os.path.dirname(__file__), 'prompts', 'calendar_update.txt')
# with open(UPDATE_PROMPT_PATH, 'r', encoding='utf-8') as f:
#     CALENDAR_UPDATE_PROMPT = f.read()

calendar_agent = Agent(
    name="Calendar Agent",
    model="o3",
    instructions=CALENDAR_PROMPT,
    output_type=CalendarEventOutput,
)

# calendar_update_agent = Agent(
#     name="Calendar Update Agent",
#     model="o3",
#     instructions=CALENDAR_UPDATE_PROMPT,
#     output_type=InstagramOutput,
# )

create_calendar_events_from_text = Agent(
    name="Calendar Agent Create From Text",
    model="o3",
    instructions=CALENDAR_PROMPT_CREATE_FROM_TEXT,
    output_type=CalendarEventOutput,
)

async def calendar_agent_runner(content_to_schedule, preferences):
    input_text = f"Content to schedule:\n{content_to_schedule}\n\nPreferences:\n{preferences}"
    print(input_text)
    result = await Runner.run(calendar_agent, input_text)
    final_output = result.final_output
    return final_output

# async def calendar_update_agent_runner(content_to_schedule, preferences):
#     input_text = f"Content to schedule:\n{content_to_schedule}\n\nPreferences:\n{preferences}"
#     result = await Runner.run(calendar_update_agent, input_text)
#     final_output = result.final_output
#     return final_output

async def create_calendar_events_from_text_runner(content_to_schedule):
    result = await Runner.run(create_calendar_events_from_text, content_to_schedule)
    final_output = result.final_output
    return final_output