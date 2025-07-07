from firecrawl import FirecrawlApp
from dotenv import load_dotenv
import os
from crewai import Agent, Task, Crew, LLM
from models.content import ScrapeURLs, ScrapedData, ContentCreationResult, ContentGenerationRequest, PlatformContentResponse
from services import database as database_service
from pydantic import BaseModel, Field
from typing import List, Optional
from ai_agents.x import twitter_agent_runner, twitter_update_agent_runner
from ai_agents.youtube import youtube_agent_runner, youtube_update_agent_runner
from ai_agents.instagram import instagram_agent_runner, instagram_update_agent_runner
from ai_agents.linkedin import linkedin_agent_runner, linkedin_update_agent_runner

from models.ai_improve import (
    YouTubeImproved, TwitterImproved, TwitterReplyImproved, InstagramImproved, LinkedinImproved
)

load_dotenv()

o3_llm = LLM(
    model="o3",
    api_key=os.getenv("OPENAI_API_KEY")
)

class SummaryResult(BaseModel):
    summary: str = Field(
        ..., 
        description="A well-written paragraph summarizing the overall content of the scraped websites"
    )
    key_highlights: List[str] = Field(
        default_factory=list,
        description="A list of the most important facts, statistics, or ideas extracted from the content"
    )
    noteworthy_points: List[str] = Field(
        default_factory=list,
        description="Interesting, surprising, or recurring themes found across the websites"
    )
    action_items: Optional[List[str]] = Field(
        default=None,
        description="Suggested actions or follow-up steps derived from the content, if applicable"
    )

app = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))

def scrape_website(url: str):
    scrape_result = app.scrape_url(url, formats=['markdown', 'html'])
    print(scrape_result)
    return scrape_result

def search_website(query: str):
    search_result = app.search(query, limit=5)
    return search_result

def summarize_content(result: List[ScrapedData]):
    summary_agent = Agent(
        role="Insightful Web Summary Agent",
        goal=(
            f"Carefully analyze the scraped web content: {result} from the provided websites. "
            "Extract and highlight the most important information, including key takeaways, "
            "notable data points, emerging themes, and anything actionable or unique. "
            "Then write a concise and well-structured summary that takes everything into account.  It should be "
            "as detailed as possible.  I want it structured well, and easy to read."
        ),
        backstory=(
            "You are a highly skilled web content summarization agent trained to read, analyze, "
            "and synthesize large volumes of scraped website data. You excel at identifying what truly matters—"
            "from factual insights and trends to tone, calls to action, and stand-out elements. "
            "You present your findings in a way that is both informative and digestible for decision-makers, researchers, or general readers."
        ),
        verbose=True
    )

    summary_task = Task(
        description=(
            "Read and analyze the content scraped from the following websites:"
            f"{result}"
            "Your goal is to generate a structured summary that includes:\n"
            "- A short paragraph summary of the overall content\n"
            "- Key highlights and facts\n"
            "- Noteworthy elements (e.g., trends, unusual info, or repeated themes)\n"
            "- Any actionable insights or suggestions (if relevant)\n"
            "- Keep the language accessible, accurate, and compelling"
        ),
        expected_output=(
            "A structured summary including: overall summary, key highlights, noteworthy points, "
            "and optional actionable suggestions"
        ),
        agent=summary_agent,
        output_pydantic=SummaryResult
    )

    
    crew = Crew(agents=[summary_agent], tasks=[summary_task])
    crew_result = crew.kickoff()
    
    return crew_result.pydantic

def content_search(query: str) -> ContentCreationResult:
    search_results_data = search_website(query)
    
    search_context = "\n\n".join(
        [
            f"Title: {result['title']}\nURL: {result['url']}\nDescription: {result['description']}"
            for result in search_results_data.data
        ]
    )
        
    relevant_urls_agent = Agent(
        role="Relevant URLs Agent",
        goal=f"Find the most relevant URLs from the search results: {search_context}, and only return the top 3 urls to scrape that aren't based on youtube.",
        backstory="You are a world-class researcher, skilled at identifying the most relevant and promising URLs from a list of search results based on their title and description.",
        verbose=True,
        reasoning=True
    )
    
    relevant_urls_task = Task(
        description=f"From the following search results: {search_context}, find the most relevant URLs. You must return only the top 3 urls to scrape.",
        expected_output="A list of the top 3 most relevant URLs to scrape, formatted as a JSON object with a single key 'urls'.",
        agent=relevant_urls_agent,
        output_pydantic=ScrapeURLs
    )
    
    crew = Crew(agents=[relevant_urls_agent], tasks=[relevant_urls_task])
    crew_result = crew.kickoff()
    
    # Retrieve the validated Pydantic output from the task
    selected_urls = crew_result.pydantic.urls
    
    print("Selected URLs:")
    print(selected_urls)

    scraped_content_list = []
    for url in selected_urls:
        scrape_result = scrape_website(url)
        # Check if scraping was successful and the markdown content exists
        if scrape_result and scrape_result.markdown:
            print("scraped url: " + url)
            scraped_content_list.append(
                ScrapedData(url=url, markdown=scrape_result.markdown)
            )
            print("scraped markdown: " + scrape_result.markdown)
            
    print("Scraped content list:")
    print(scraped_content_list)
    
    scraped_markdown = "\n\n".join([item.markdown for item in scraped_content_list])
    
    print("Scraped markdown:")
    print(scraped_markdown)
        
    summary_result = summarize_content(scraped_markdown)
    
    final_result = ContentCreationResult(
        query=query,
        urls=selected_urls,
        scraped_content=scraped_content_list,
        summary=summary_result.summary,
        key_highlights=summary_result.key_highlights,
        noteworthy_points=summary_result.noteworthy_points,
        action_items=summary_result.action_items
    )
    
    return final_result

def get_platform_posts():
    posts = database_service.get_platform_posts()
    result = []
    for post, research_query in posts:
        result.append({
            "id": post.id,
            "research_id": post.research_id,
            "platform": post.platform,
            "content_data": post.content_data,
            "created_at": post.created_at.isoformat() if post.created_at else None,
            "updated_at": post.updated_at.isoformat() if post.updated_at else None,
            "used": post.used,
            "research_query": research_query
        })
    return result

def save_content_result(content_result: ContentCreationResult):
    return database_service.save_content_result(content_result)

def save_or_update_platform_content(research_id: int, platform: str, content):
    try:    
        return database_service.save_or_update_platform_content(research_id, platform, content)
    except Exception as e:
        print("error saving or updating platform content")
        print(e)
        raise e

async def create_platform_content(request: ContentGenerationRequest) -> PlatformContentResponse:
    # Map platforms to boolean fields
    used_for_youtube = "youtube" in request.platforms
    used_for_x = "x" in request.platforms
    used_for_instagram = "instagram" in request.platforms
    used_for_linkedin = "linkedin" in request.platforms
    
    print(request)
    print(used_for_youtube)
    print(used_for_x)
    print(used_for_instagram)
    print(used_for_linkedin)
    
    existing = database_service.get_content_by_id(request.research_id)
    if existing:
        print("Existing content found")
        if existing.id:
            print(existing.id)
        else:
            print("No id found")
            print(existing)
    else:
        print("No existing content found")
        print(request)
        

    youtube_content = None
    x_content = None
    instagram_content = None
    linkedin_content = None

    full_markdown = "\n\n".join([item['markdown'] for item in existing.scraped_content])

    if used_for_youtube:
        youtube_content = await youtube_agent_runner(full_markdown)
    if used_for_x:
        x_content = await twitter_agent_runner(full_markdown)
    if used_for_instagram:
        instagram_content = await instagram_agent_runner(full_markdown)
    if used_for_linkedin:
        linkedin_content = await linkedin_agent_runner(full_markdown)
        
    # Create a dict with all fields, updating only the platform booleans
    update_data = {
        "query": existing.query,
        "urls": existing.urls,
        "scraped_content": existing.scraped_content,
        "summary": existing.summary,
        "key_highlights": existing.key_highlights,
        "noteworthy_points": existing.noteworthy_points,
        "action_items": existing.action_items,
        "used_for_youtube": used_for_youtube,
        "used_for_x": used_for_x,
        "used_for_instagram": used_for_instagram,
        "used_for_linkedin": used_for_linkedin,
    }
    
    content_result = ContentCreationResult(**update_data)
    updated_content_result = database_service.update_content_creation_result(request.research_id, content_result)
    # Save to database
    # save_content_result(content_result)
        
    response = PlatformContentResponse(
        x_content=x_content,
        instagram_content=instagram_content,
        linkedin_content=linkedin_content
    )
        
    return response
    
def get_all_content():
    return database_service.get_all_content()

def get_content_by_id(research_id: int):
    return database_service.get_content_by_id(research_id)

def delete_platform_post(content_id: int) -> bool:
    return database_service.delete_platform_post(content_id)

async def ai_improve_content(content_id: int):
    # 1. Fetch current content
    current_content = database_service.get_platform_content_by_id(content_id)
    if not current_content:
        return None

    # 1b. Fetch original markdown for this content
    original_markdown = database_service.get_original_markdown_by_platform_content_id(content_id)

    platform = current_content.platform
    content_data = current_content.content_data

    # 2. AI improvement (stub)
    improved_content_model = await ai_improve_content_stub(platform, content_data, original_markdown)

    # 3. Update in DB
    database_service.update_platform_content(content_id, improved_content_model.model_dump())

    # 4. Return result
    return {
        "message": "Content improved successfully",
        "improved_content": improved_content_model.model_dump(),
        "content_id": content_id
    }

async def ai_improve_content_stub(platform, content_data, original_markdown):
    # Improved logic for all platforms
    if platform == "youtube":
        description = content_data if isinstance(content_data, str) else content_data.get('description', '')
        output = await youtube_update_agent_runner(original_markdown, description)
        return YouTubeImproved(description=output.description if hasattr(output, 'description') else output)
    elif platform == "x":
        tweet = content_data.get('tweet', '')
        reply_tweets = [r.get('reply_tweet', '') for r in content_data.get("reply_tweets", [])]
        full_content = original_markdown + "\n\n" + tweet + "\n\n" + "\n\n".join(reply_tweets)
        output = await twitter_update_agent_runner(full_content)
        return TwitterImproved(
            tweet=output.tweet,
            reply_tweets=[
                TwitterReplyImproved(**(r.dict() if hasattr(r, 'dict') else r)) if not isinstance(r, TwitterReplyImproved) else r
                for r in output.reply_tweets
            ]
        )
    elif platform == "instagram":
        caption = content_data.get('caption', '')
        output = await instagram_update_agent_runner(original_markdown, caption)
        return InstagramImproved(caption=output.caption if hasattr(output, 'caption') else output)
    elif platform == "linkedin":
        commentary = content_data.get('commentary', '')
        output = await linkedin_update_agent_runner(original_markdown, commentary)
        return LinkedinImproved(commentary=output.commentary if hasattr(output, 'commentary') else output)
    else:   
        return YouTubeImproved(description="IMPROVED: Unknown platform content")

def get_platform_posts_only():
    return database_service.get_platform_posts_only()

def check_platform_already_used(research_id: int, platform: str) -> bool:
    return database_service.check_platform_already_used(research_id, platform)

def get_recent_research(limit: int = 5):
    return database_service.get_recent_content_results(limit)

# if __name__ == "__main__":
#     result = content_search("crewai flows")
    
#     class SummaryResult(BaseModel):
#         summary: str = Field(..., description="The summary of the content of the scraped websites")
    
#     summary_agent = Agent(
#         role="Summary Agent",
#         goal="Summarize the content of the scraped websites: {result.scraped_content}",
#         backstory="You are a summary agent that summarizes the content of the scraped websites",
#         verbose=True
#     )
    
#     summary_task = Task(
#         description=f"Summarize the content of the scraped websites: {result.scraped_content}",
#         expected_output="A summary of the content of the scraped websites",
#         agent=summary_agent,
#         output_pydantic=SummaryResult
#     )
    
#     crew = Crew(agents=[summary_agent], tasks=[summary_task])
#     crew_result = crew.kickoff()
    
#     print(crew_result)
    
#     print(result)