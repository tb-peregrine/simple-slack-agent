import os
import logging
import asyncio
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv
from agents import Agent, Runner
from agents.mcp import MCPServerStreamableHttp

# Set up logging - only show warnings and errors
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Verify environment variables
bot_token = os.environ.get("SLACK_BOT_TOKEN")
app_token = os.environ.get("SLACK_APP_TOKEN")
openai_api_key = os.environ.get("OPENAI_API_KEY")
tinybird_token = os.environ.get("TINYBIRD_TOKEN")

if not all([bot_token, app_token, openai_api_key, tinybird_token]):
    logger.error("Missing required environment variables!")
    raise ValueError("Missing required environment variables")

# Initialize the Slack app
app = App(token=bot_token)

async def get_agent_response(text: str) -> str:
    """Get response from OpenAI agent with Tinybird MCP"""
    server = MCPServerStreamableHttp(
        name="tinybird",
        params={
            "url": f"https://cloud.tinybird.co/mcp?token={tinybird_token}",
        },
    )

    async with server:
        agent = Agent(
            name="tb_agent",
            model="gpt-4-turbo-preview",
            mcp_servers=[server]
        )
        result = await Runner.run(
            agent,
            input=text,
        )
        return result.final_output

@app.event("app_mention")
def handle_mention(event, say):
    """
    Handle when the bot is mentioned in a channel
    """
    # Get the user who mentioned the bot and their message
    user = event["user"]
    text = event["text"].replace(f"<@{event['user']}>", "").strip()
    
    # Get the thread_ts if it exists, otherwise use the event ts
    thread_ts = event.get("thread_ts") or event["ts"]
    
    try:
        # Send immediate response in the thread
        say(
            text="I'm working on your request... 🤔",
            thread_ts=thread_ts
        )
        
        # Get response from agent
        response = asyncio.run(get_agent_response(text))
        
        # Send the final response in the same thread
        say(
            text=f"<@{user}> {response}",
            thread_ts=thread_ts
        )
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        say(
            text=f"<@{user}> I apologize, but I encountered an error while processing your request. Please try again later.",
            thread_ts=thread_ts
        )

if __name__ == "__main__":
    # Start the app in Socket Mode
    handler = SocketModeHandler(app, app_token)
    handler.start() 