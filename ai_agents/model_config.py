"""Model shared by the OpenAI Agents SDK agents in this package.

o3 shuts down on 2026-12-11. OpenAI lists gpt-5.6-sol as its replacement:
https://developers.openai.com/api/docs/deprecations
"""
from agents import ModelSettings
from openai.types.shared import Reasoning

REASONING_MODEL = "gpt-5.6-sol"

# The Agents SDK defaults gpt-5.6-sol to reasoning effort "none" and verbosity
# "low". o3 always reasoned (medium effort by default) and had no verbosity
# setting, so ask for medium effort and leave verbosity at the API default.
REASONING_SETTINGS = ModelSettings(reasoning=Reasoning(effort="medium"))
