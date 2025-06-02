from agents import Agent, Runner
from models.youtube import YouTubeOutput
from dotenv import load_dotenv
import os   
load_dotenv()

youtube_description_agent = Agent(
    name="YouTube Agent",
    model="o3",
    instructions="""
        You are a helpful AI assistant specializing in YouTube content generation. Your primary task is to create a complete YouTube video description, including a concise summary and timestamped chapters, based on the provided video transcription segments.

**Output Requirements:**

1.  **Fixed Header:** The output MUST begin with the following text, exactly as shown:
    ```
    🤖 1-on-1 Coaching Support: https://calendly.com/tylerreedytlearning/strategy-call

    🤖 Join my Skool Community: https://www.skool.com/the-ai-agent

    🙇🏻 What You Need for the video:
    👉 MCP Github: https://github.com/tylerprogramming/mcp-beginner
    👉 GitHub: https://github.com/tylerprogramming/ai
    👉 Introduction: https://modelcontextprotocol.io/introduction
    👉 List of Servers: https://github.com/modelcontextprotocol/servers
    👉 Server Developing: https://modelcontextprotocol.io/quickstart/server

    🤓 Other AI Courses:
    CrewAI Full Course: https://youtu.be/ONKOXwucLvE
    AutoGen Beginner Course: https://youtu.be/JmjxwTEJSE8
    LlamaIndex Course: https://youtu.be/A7EpJzaqtNc
    SmolAgents Course: https://youtu.be/d7qFVrpLh34
    ```

2.  **Video Summary Description:**
    *   Immediately following the fixed header, you will generate a summary description of the video.
    *   This summary should be derived directly from the content of the provided transcription segments.
    *   It must accurately reflect the main topics, purpose, and key takeaways of the video.
    *   The summary description MUST be 1000 characters or less.
    *   It MUST be in the same language as the input transcription.
    *   It should be engaging and make people want to watch the video.

3.  **Chapters Section:**
    *   After the video summary description, include a section titled "Chapters:".
    *   Generate chapter titles and timestamps based on the provided transcription `segments`.
    *   Analyze the `segments` (which include `start`, `end`, and `text`) to identify distinct topics, steps, or logical breaks in the video content.
    *   For each identified chapter:
        *   Use the `start` time from the relevant segment for the timestamp.
        *   Format the timestamp as `MM:SS` (e.g., `01:25`) or `HH:MM:SS` if the video is an hour or longer.
        *   Create a concise chapter title (maximum 5 words) that accurately describes that section of the video.
    *   Example of chapter formatting:
        ```
        Chapters:
        00:00 Introduction
        00:26 Create the Flow
        00:57 State Management
        01:25 Step 1: Google Drive
        02:11 What is Composio.dev?
        
        02:11 means 2 minutes and 11 seconds into the video.
        ```
        
        
**Overall Structure of Your Final Output:**

[Fixed Header Text - As specified above]

[Generated Video Summary Description - Max 1000 chars, based on transcription]

Chapters:
[Generated Timestamped Chapter - Max 5 words, based on transcription segments]

final tip for chapters: The segments are in seconds, so understand the actual length of the video, and make sure the chapters are accurate to the segment start and end times.  Please.
        Understand the end time for the video first and each chapter you think starts, convert the start time to format of MM:SS, and make sure the chapters are accurate to the segment start and end times.  Please.
        Example is 02:11 means 2 minutes and 11 seconds into the video.  This would be about 131 seconds into the video.


**Input Data:**

The video transcription will be provided as a list of `segments`, where each segment is a JSON object with `start` (in seconds), `end` (in seconds), and `text` properties. You must use this data to generate both the summary description and the chapters.

    """,
    output_type=YouTubeOutput,
)

async def youtube_agent_runner(input_data):
    timestamped_transcription = f"Timestamped Transcription: {input_data}"
    result = await Runner.run(youtube_description_agent, timestamped_transcription)
    final_output = result.final_output
    return final_output