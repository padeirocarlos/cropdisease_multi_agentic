# For Gmail | !pip install smtplib or uv add smtplib

import os
import sys
import requests
import asyncio
import smtplib
from typing import Dict
from dotenv import load_dotenv
from pydantic import BaseModel
from email.mime.text import MIMEText
sys.path.append(os.path.abspath(os.path.join('..', 'commons')))
from api_base_url import ApiBaseUrl
from agents import Agent, Runner, trace, function_tool, OpenAIChatCompletionsModel, input_guardrail, GuardrailFunctionOutput, output_guardrail

class CommonTools:
    
    def __init__(self):
        load_dotenv(override=True)

    @function_tool
    def email_sender(body: str, subject: str, to_emails:list):
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
        
        print(f" subject : {subject} ,  from_email: {from_email}  , to_email: {to_email} ,  gmail_app_password: {gmail_app_password}")
        try:
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                if to_email:
                    server.starttls()  # Secure the connection
                    server.login(from_email, gmail_app_password)
                    server.send_message(msg)
                
            return {"status": "success"}
        except Exception as e:
            return {"status": "failure", "message": str(e)}