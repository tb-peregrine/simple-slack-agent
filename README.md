# Simple Slack Agent with Tinybird MCP

A Slack bot that uses OpenAI's agents SDK to answer questions about your Tinybird data.

## Features

- Responds to mentions in Slack channels
- Uses OpenAI's agents SDK to process questions
- Connects to Tinybird MCP to access your data
- Uses Socket Mode for real-time communication
- Supports terminal mode with streaming responses

## Setup Instructions

1. Create a new Slack App at <https://api.slack.com/apps>
2. Enable Socket Mode in your app settings
3. Add the following bot token scopes:
   - `app_mentions:read`
   - `chat:write`
4. Install the app to your workspace
5. Create a `.env` file with your tokens:

    ```
    SLACK_BOT_TOKEN=xoxb-your-bot-token
    SLACK_APP_TOKEN=xapp-your-app-token
    OPENAI_API_KEY=your-openai-api-key
    TINYBIRD_TOKEN=your-tinybird-token
    ```

## Running the Bot

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Run the bot:

For Slack mode (default):

```bash
python app.py
```

For terminal mode with streaming responses:

```bash
python app.py -t
```

3. In Slack mode, mention the bot in any channel it's invited to using `@YourBotName`

## How it Works

1. When the bot is mentioned in a channel, it captures the message
2. The message is passed to an OpenAI agent that has access to your Tinybird MCP server
3. The agent can:
   - Execute SQL queries against your Tinybird workspace
   - Access your data sources and endpoints
   - Formulate responses based on the data
4. The agent's response is sent back to the Slack channel

## Requirements

- Python 3.8+
- Slack workspace with admin permissions
- OpenAI API key
- Tinybird workspace with MCP enabled
