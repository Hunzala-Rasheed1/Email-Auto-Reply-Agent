# Email Auto-Reply Agent

An automated system that reads incoming emails and generates intelligent replies using a free LLM (Large Language Model).

## Overview

This tool connects to your Gmail account, monitors for new emails, and automatically generates and sends contextual replies using the Together.ai API with state-of-the-art language models. Perfect for managing high email volume, vacation responses, or simple inquiries.

## Features

- **Gmail Integration**: Securely connects to your Gmail account via OAuth
- **Intelligent Replies**: Uses Llama-4-Maverick or other powerful LLMs to generate contextual responses
- **Customizable**: Easy to modify prompt instructions, email filters, and check frequency
- **Threading Support**: Maintains proper email conversation threading
- **Error Handling**: Robust handling for API and network issues

## Requirements

- Python 3.7+
- Gmail account
- Together.ai API key (free tier available)
- Google Cloud project with Gmail API enabled

## Installation

1. Clone this repository or download the script files
```bash
git clone https://github.com/yourusername/email-auto-reply-agent.git
cd email-auto-reply-agent
```

2. Install required dependencies
```bash
pip install together google-auth google-auth-oauthlib google-api-python-client
```

3. Set up your Google Cloud Project and OAuth credentials:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project
   - Enable the Gmail API
   - Create OAuth credentials (Desktop app)
   - Download credentials as `credentials.json` and place in the project directory
   - Add your email as a test user in the OAuth consent screen

4. Get a Together.ai API key:
   - Sign up at [Together.ai](https://www.together.ai/)
   - Get your API key from the dashboard
   - Add it to the script or set as an environment variable:
   ```bash
   export TOGETHER_API_KEY="your_api_key_here"
   ```

## Configuration

Edit the script to customize your email auto-reply agent:

```python
# Key configuration options
TOGETHER_MODEL = "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"  # Which LLM to use
CHECK_FREQUENCY = 60  # How often to check for new emails (in seconds)
MAX_EMAILS_PER_CYCLE = 5  # Maximum emails to process per check
EMAIL_LABEL = "INBOX"  # Which email label to check

# Email filtering
# Modify the query in get_unread_emails() to filter specific emails:
# Example: q='is:unread from:example@gmail.com' or q='is:unread subject:"Important"'
```

## Usage

1. Run the script:
```bash
python email_agent.py
```

2. First-time setup:
   - A browser window will open
   - Log in with your Google account
   - Grant the requested permissions
   - The script will create and save a token for future use

3. The agent will now:
   - Check for new emails every minute (or as configured)
   - Process up to 5 emails per check (configurable)
   - Generate and send replies
   - Mark original emails as read

4. To stop the agent, press Ctrl+C in the terminal

## Customizing Responses

To adjust how the agent responds to emails, modify the system and user prompts in the `generate_reply()` function:

```python
messages = [
    {
        "role": "system", 
        "content": "You are an email assistant. Generate helpful, professional replies to emails. Be concise but thorough."
    },
    {
        "role": "user", 
        "content": f"""
        Generate a reply to this email:
        ...
        """
    }
]
```

## Alternative LLM Options

The script is configured to use Together.ai, but can be adapted for other LLM providers:

1. **Ollama (Local)**: For running models locally without API costs
2. **OpenAI**: For commercial use with their models
3. **Anthropic**: For Claude models
4. **Hugging Face**: For their Inference API

## Security Considerations

- API keys and OAuth tokens provide access to your accounts - keep them secure
- The script will have read/send access to your emails
- Consider running in a dedicated environment for better security
- Review the privacy policies of Together.ai before processing sensitive emails

## Troubleshooting

- **Authentication Issues**: Delete `token.json` and try again to reset OAuth flow
- **Rate Limits**: Increase `CHECK_FREQUENCY` if hitting API rate limits
- **Email Format Problems**: Some complex emails may not parse correctly


## Contributing

Pull requests welcome! Please ensure your changes maintain backward compatibility.
