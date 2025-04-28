import os
import base64
import time
import json
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from together import Together

# Configuration
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
TOGETHER_API_KEY = "Your-api-key"  # Replace with your Together.ai API key
TOGETHER_MODEL = "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"  # The model you mentioned
CHECK_FREQUENCY = 60  # Check for new emails every 60 seconds
MAX_EMAILS_PER_CYCLE = 1  # Process at most 5 emails per check
EMAIL_LABEL = "INBOX"  # Which email label to check

# Set API key for Together client
os.environ["TOGETHER_API_KEY"] = TOGETHER_API_KEY

# Gmail API Authentication
def get_gmail_service():
    """Authenticate and return Gmail API service."""
    creds = None
    
    # Check if token.json exists with stored credentials
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_info(
            json.loads(open('token.json').read()), SCOPES)
    
    # If credentials don't exist or are invalid, get new ones
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save credentials for next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    # Build and return the Gmail service
    return build('gmail', 'v1', credentials=creds)

# Email Operations
def get_unread_emails(service, max_results=MAX_EMAILS_PER_CYCLE):
    """Get unread emails from Gmail."""
    results = service.users().messages().list(
        userId='me', 
        labelIds=[EMAIL_LABEL], 
        q='is:unread'
    ).execute()
    
    messages = results.get('messages', [])
    
    if not messages:
        return []
    
    # Limit number of emails processed
    messages = messages[:max_results]
    
    # Get full message details
    emails = []
    for message in messages:
        msg = service.users().messages().get(
            userId='me', id=message['id'], format='full'
        ).execute()
        emails.append(msg)
    
    return emails

def extract_email_content(message):
    """Extract email details from Gmail API message."""
    headers = message['payload']['headers']
    
    # Get email subject
    subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
    
    # Get sender
    from_email = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
    
    # Get message ID for threading
    message_id = next((h['value'] for h in headers if h['name'] == 'Message-ID'), None)
    
    # Extract body content
    if 'parts' in message['payload']:
        # Multipart message
        parts = message['payload']['parts']
        body = ""
        for part in parts:
            if part['mimeType'] == 'text/plain':
                body_data = part['body'].get('data', '')
                if body_data:
                    body += base64.urlsafe_b64decode(body_data).decode('utf-8')
    else:
        # Single part message
        body_data = message['payload']['body'].get('data', '')
        body = base64.urlsafe_b64decode(body_data).decode('utf-8') if body_data else ""
    
    return {
        'id': message['id'],
        'threadId': message['threadId'],
        'subject': subject,
        'from': from_email,
        'body': body,
        'message_id': message_id
    }

def generate_reply(email_data):
    """Generate a reply using the Together.ai client library."""
    try:
        # Initialize Together client
        client = Together()
        
        # Create system and user messages
        messages = [
            {
                "role": "system", 
                "content": "You are an email assistant. Generate helpful, professional replies to emails. Be concise but thorough."
            },
            {
                "role": "user", 
                "content": f"""
                Generate a reply to this email:
                
                FROM: {email_data['from']}
                SUBJECT: {email_data['subject']}
                
                EMAIL CONTENT:
                {email_data['body']}
                
                Your reply should:
                - Be professional and helpful
                - Directly address the content of the email
                - Keep a similar tone to the original email
                - Be concise but thorough
                - Do not include any salutation or signature - just the reply body
                """
            }
        ]
        
        # Call the Together API through the client
        response = client.chat.completions.create(
            model=TOGETHER_MODEL,
            messages=messages,
            max_tokens=500,
            temperature=0.7
        )
        
        # Extract the reply text
        if response and hasattr(response, 'choices') and len(response.choices) > 0:
            reply_text = response.choices[0].message.content
            return reply_text
        else:
            print("Unexpected API response format")
            return None
            
    except Exception as e:
        print(f"Error calling Together API: {e}")
        return None

def send_reply(service, email_data, reply_text):
    """Send reply email using Gmail API."""
    # Format sender name from original email
    sender_name = email_data['from'].split('<')[0].strip()
    if '<' in email_data['from']:
        sender_email = email_data['from'].split('<')[1].split('>')[0]
    else:
        sender_email = email_data['from']
    
    # Create message
    message = MIMEText(reply_text)
    message['to'] = email_data['from']
    message['subject'] = f"Re: {email_data['subject']}"
    
    # Add threading headers if available
    if email_data['message_id']:
        message['In-Reply-To'] = email_data['message_id']
        message['References'] = email_data['message_id']
    
    # Convert to Gmail API format
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
    
    # Send the message
    try:
        sent_message = service.users().messages().send(
            userId='me',
            body={'raw': raw_message, 'threadId': email_data['threadId']}
        ).execute()
        
        # Mark the original as read
        service.users().messages().modify(
            userId='me', 
            id=email_data['id'],
            body={'removeLabelIds': ['UNREAD']}
        ).execute()
        
        return sent_message
    except Exception as e:
        print(f"Error sending reply: {e}")
        return None

def process_emails():
    """Main function to process emails."""
    service = get_gmail_service()
    
    print("Checking for new emails...")
    emails = get_unread_emails(service)
    
    if not emails:
        print("No new emails to process.")
        return
    
    print(f"Found {len(emails)} unread emails.")
    
    for email in emails:
        try:
            # Extract email content
            email_data = extract_email_content(email)
            print(f"Processing email: {email_data['subject']}")
            
            # Generate reply using LLM
            reply_text = generate_reply(email_data)
            
            if reply_text:
                # Send the reply
                result = send_reply(service, email_data, reply_text)
                if result:
                    print(f"Reply sent successfully to: {email_data['from']}")
                else:
                    print(f"Failed to send reply to: {email_data['from']}")
            else:
                print("Failed to generate reply.")
        except Exception as e:
            print(f"Error processing email: {e}")
            continue

def main():
    """Run the email replier in a loop."""
    print("Starting Email Auto-Reply Agent with Together.ai...")
    while True:
        try:
            process_emails()
        except Exception as e:
            print(f"Error in main loop: {e}")
        
        print(f"Waiting {CHECK_FREQUENCY} seconds before next check...")
        time.sleep(CHECK_FREQUENCY)

if __name__ == "__main__":
    main()