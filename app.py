import os
import logging
import asyncio
import argparse
import sys
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

if not all([openai_api_key, tinybird_token]):
    logger.error("Missing required environment variables!")
    raise ValueError("Missing required environment variables")

async def thinking_animation(stop_event):
    """Display a thinking animation"""
    spinner = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
    i = 0
    while not stop_event.is_set():
        sys.stdout.write(f"\rAgent: {spinner[i]} Thinking...")
        sys.stdout.flush()
        i = (i + 1) % len(spinner)
        await asyncio.sleep(0.1)

async def get_agent_response(text: str) -> str:
    """Get response from OpenAI agent with Tinybird MCP (non-streaming)"""
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

async def stream_agent_response(text: str):
    """Stream response from OpenAI agent with Tinybird MCP"""
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
        # Stream the response word by word
        words = result.final_output.split()
        for word in words:
            yield word + " "
            await asyncio.sleep(0.05)  # Small delay between words

async def terminal_chat():
    """Run the agent in terminal mode"""
    print("🤖 Terminal mode activated. Type 'exit' to quit.")
    print("Ask me anything about your Tinybird data!")
    
    while True:
        try:
            # Get user input
            user_input = input("\nYou: ").strip()
            
            # Check for exit command
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("\nGoodbye! 👋")
                break
            
            # Create stop event for the animation
            stop_event = asyncio.Event()
            
            # Start thinking animation
            animation_task = asyncio.create_task(thinking_animation(stop_event))
            
            try:
                # Get the response first
                response = await get_agent_response(user_input)
                
                # Stop the animation and clear the line
                stop_event.set()
                await animation_task
                sys.stdout.write("\r" + " " * 50 + "\r")
                sys.stdout.write("Agent: ")
                sys.stdout.flush()
                
                # Stream the response word by word
                words = response.split()
                for word in words:
                    sys.stdout.write(word + " ")
                    sys.stdout.flush()
                    await asyncio.sleep(0.05)  # Small delay between words
                print()  # New line after response
                
            except Exception as e:
                # Stop the animation if there's an error
                stop_event.set()
                await animation_task
                print(f"\nError: {str(e)}")
                raise e
            
        except KeyboardInterrupt:
            print("\n\nGoodbye! 👋")
            break
        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            print("\nAgent: I apologize, but I encountered an error. Please try again.")

def run_slack_bot():
    """Run the bot in Slack mode"""
    if not all([bot_token, app_token]):
        logger.error("Missing Slack tokens!")
        raise ValueError("Missing Slack tokens")

    # Initialize the Slack app
    app = App(token=bot_token)

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

    # Start the app in Socket Mode
    handler = SocketModeHandler(app, app_token)
    handler.start()

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run the bot in Slack or terminal mode')
    parser.add_argument('-t', '--terminal', action='store_true', help='Run in terminal mode')
    args = parser.parse_args()

    if args.terminal:
        # Run in terminal mode
        asyncio.run(terminal_chat())
    else:
        # Run in Slack mode
        run_slack_bot() 