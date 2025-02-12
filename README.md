# Slack Meeting Notes & File Management Integration

An AI-powered integration solution for managing files, folders, and meeting notes in Slack. This project combines LangChain and OpenAI to provide intelligent document management capabilities.

## `run_demo_bot1.py`

This script serves as the entry point for running the Document Management Bot in Slack mode.

### Key Features:
- **Logging**: Configures logging to capture debug information and errors, which helps in monitoring the bot's activity.
- **Slack Integration**: Utilizes the Slack Bolt framework to handle messages and events from Slack. It sends notifications to a specified Slack channel.
- **Command Processing**: Processes user commands and responds accordingly, providing feedback on actions taken.
- **Environment Variables**: Loads necessary environment variables (e.g., Slack tokens) from a `.env` file to ensure secure access to Slack APIs.

### Usage:
To run the bot, execute the script in a terminal. Ensure that the required environment variables are set, including `SLACK_BOT_TOKEN`, `SLACK_APP_TOKEN`, and `SLACK_CHANNEL_ID`. The bot will start, allowing for direct interaction while also listening for messages in Slack.
