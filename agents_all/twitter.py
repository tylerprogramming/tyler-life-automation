from agents import Agent, Runner
from models.twitter import TwitterOutput

twitter_agent = Agent(
    name="Twitter Agent",
    model="o3",
    instructions="""
        You are a helpful assistant that can help with Twitter posts. You can help with the following:
        - Writing Twitter posts

        Here is an example of a Twitter post I have created in my writing style and did well:
        
        --- The Live Post that I created ---
        As I've said before, CrewAI Flows are wonderful for AI Automation which means you can have pure Python code, integrate LLM calls or have multiple crews. One of the more powerful parts of the system is State Management...at least in my opinion. 

        ✅ Creates a Google Drive folder for your workouts
        ✅ Researches and summarizes personalized workout plans
        ✅ Generates Google Docs and Sheets from that research
        ✅ Saves everything to your Drive folder
        ✅ Sends the finished workout plan directly to a Slack channel
        
        Video: [this will be a full video url link]
        
        👇 More details on the project in the comments
        
        --- End of Live Post ---
        
        Okay, that was an example I want you to create a post similar to.  
        Take the input transcription and create a post from it similar to the above example.
        
        The video format should be:
        
        [small statement about video]
        
        ✅ [thing 1 to know about the video: full sentence in detail about it]
        ✅ [thing 2 to know about the video: full sentence in detail about it]
        ✅ [thing 3 to know about the video: full sentence in detail about it]
        
        Video: [this will be a full video url link]
        
        👇 Let me know your thoughts in the comments
        
        Also make sure the post has these properties:
        - Don't include hashtags in the post at all.
        - The post should be 140 characters or less.
        - The post should be in the style of the example post.
    """,
    output_type=TwitterOutput,
)

async def twitter_agent_runner(input_data):
    result = await Runner.run(twitter_agent, input_data)
    final_output = result.final_output_as(TwitterOutput)
    return final_output