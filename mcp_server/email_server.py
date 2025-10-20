import uuid
import os

import smtplib
from dotenv import load_dotenv
from email.mime.text import MIMEText
from datetime import datetime, timezone

from mcp.server.fastmcp import FastMCP
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

load_dotenv(override=True)

# Create FastMCP server
mcp = FastMCP(name="Email-Management-Server")

@mcp.resource("config://app-version")
def get_app_version() -> dict:
    """Static resource providing application version information"""
    return {
        "name": "Email-Management-Server",
        "version": "1.0.0",
        "release_date": "2025-10-15",
        "environment": "production"
    }


email_tool_def = {
    "type": "function",
    "function": {
        "name": "email_sender",
        "description": "Searches for research papers on arXiv by query string.",
        "parameters": {
            "type": "object",
            "properties": {
                "body": {
                    "type": "string",
                    "description": "body content of the email."
                },
                "subject": {
                    "type": "string",
                    "description": "subject of the email.",
                },
                
                "to_emails": {
                    "type": "string",
                    "description": "the list of destined email.",
                }
            },
            "required": ["subject"]
        }
    }
}
@mcp.tool()
def email_sender(body: str=None, subject: str=None, to_emails:list=None):
    """ Send out an email with the given body to all sales prospects via Gmail SMTP """
    
    # Set up email sender, recipient, and content
    from_email = os.getenv("GMAIL_USER")  # Replace with your Gmail address or set as env var
    to_email = os.getenv("GMAIL_TO")     # Replace with recipient or set as env var
    gmail_app_password = os.getenv("GMAIL_APP_PASSWORD")  # Use your Gmail app password or set as env var
    # subject = "Sales email list test 1"
    
    # Create the email
    msg = MIMEText(body, 'html')
    msg['Subject'] = subject
    msg['From'] = from_email
    to_email = None
    
    if to_emails is None:
        to_emails = ["c.v.padeiro@gmail.com", "cpadeiro2012@gmail.com"]
    
    if subject is None:
        msg['Subject'] = "Sales email list test 1"
    
    for index, email in enumerate(to_emails):
        if index !=0:
            to_email += "," + email
        else:
            to_email = email
            
    if to_email is not None:
        msg['To'] = to_email
    
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            if to_email:
                server.starttls()  # Secure the connection
                server.login(from_email, gmail_app_password)
                server.send_message(msg)
            
        return {"status": "success"}
    except Exception as e:
        return {"status": "failure", "message": str(e)}

@mcp.prompt()
def generate_email_prompt(disease_report: str, num_teatment: int = 5) -> str:
    """Generate a prompt for Claude to find and discuss academic papers on a specific disease report."""
    return f"""Search for {num_teatment} academic papers about '{disease_report}' using the search_papers tool. 

        Follow these instructions:
        1. First, search for papers using search_papers(disease='{disease_report}', max_results={num_teatment})
        2. For each paper found, extract and organize the following information:
        - Paper title
        - Authors
        - Publication date
        - Brief summary of the key findings
        - Main contributions or innovations
        - Methodologies used
        - Relevance to the report disease '{disease_report}'

        3. Provide a comprehensive summary that includes:
        - Overview of the current state of research in '{disease_report}'
        - Common themes and trends across the papers
        - Key research gaps or areas for future investigation
        - Most impactful or influential papers in this area

        4. Organize your findings in a clear, structured format with headings and bullet points for easy readability.

        Please present both detailed information about each paper and a high-level synthesis of the research landscape in {disease}."""

if __name__ == "__main__":
    mcp.run(transport='stdio')