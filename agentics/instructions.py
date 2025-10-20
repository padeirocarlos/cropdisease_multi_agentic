import os
from dotenv import load_dotenv
from datetime import datetime
load_dotenv(override=True)

def image_generate(pathsogens:str, prompts:list[str], caption:str, path:str, maize:str="Maize")->str:
    
    _prompt = ""
    
    for i, prompt in enumerate(prompts):
        _prompt += f"{i+1}. {prompt} \n"
        
    prompt_ = (f"""
    "You are a visual crop disease assistant. Based on the input trend insights in {pathsogens}, 
    generate two images using the following prompt and caption.
    
    prompt: 
    {_prompt}

    caption: 
    {caption}
    
    Respond in this format:
    {{"imageUrl1": "...", "imageUrl2": "..."}}
    
    You should call the following tool to save the images:
    - 'save_image' to save the images
    - {path} use this path to save the image 
    
    """)
    return prompt_

def crop_disease_image_prediction(crop_disease: str, maize:str="Maize") -> str:
    
    user_prompt = f"""
        You are a visual medical assistant for {maize} plant pathology. Based on agricultural trend insights, 
        create detailed visual prompts for an AI image generation model to generate realistic 
        images of {maize} leaves affected by {crop_disease}.
            
        Trend insights crop diseases related to:
        {crop_disease}

        Please output:
        1. VISUAL PROMPT: A comprehensive, detailed description for AI image generation that includes:
            - Specific visual symptoms and patterns of {crop_disease} on {maize} leaves
            - Color variations, lesions, spots, or discoloration characteristics
            - Leaf texture changes, wilting, or deformation details
            - Growth stage of the {maize} plant
        2. A concise, informative caption describing the {maize} disease manifestation and key identifying features

        Respond in this format:
        {{"prompt1": "...", "caption1": "...", "prompt2": "...", "caption2": "..."}}
        """
    return user_prompt


def crop_disease_image_prediction_(crop_disease: str, caption_style: str = "short punchy", moths_one:int=2, moths_two:int=4,) -> str:
    
    user_prompt = f"""
        You are a visual marketing assistant. Based on the input trend insights, 
        write a creatives and visual prompts for an AI image generation model to generate two images
        image one predicting crop disease in {moths_one} moths and image two predicting crop disease  
        in {moths_two} moths, and also include a short caption for wich image."
            
        Trend insights crop diseases related to:
        {crop_disease}

        Please output:
        1. A vivid, descriptive prompt to guide image generation.
        2. A crop disease diagnosis caption in style: {caption_style}.

        Respond in this format:
        {{"prompt1": "...", "caption1": "...", "prompt2": "...", "caption2": "..."}}
        """
    return user_prompt
     
def crop_disease_research(crop_disease:str, maize:str="Maize", tools: list[dict]=None) -> str:
    
    tools_ = ""

    for i, tool in enumerate(tools):
        name = f"tool name: {tool['function']['name']}; "
        description = f"tool goal: {tool['function']['description']}; "
        tools_ += f"{i+1}. {name} {description} \n"
    
    prompt_ = f"""
        You are a {maize} crop disease diagnosis researcher. You are able to search the web for the latest 
        developments in {maize} {crop_disease} crop diseases. Based on the request, 
        you carry out necessary research and respond with your findings.

        Your goal:
        1. Explore current {maize} crop diseases trends related to {crop_disease} using web search.
        2. Review the geographic regions and climate conditions for {crop_disease} crop diseases pathology treatment.
        3. Recommend one or more {crop_disease} crop diseases treatment methods that best match emerging trends.
        4. If needed, today date is {datetime.now().strftime("%Y-%m-%d")}.

        You can call the following tools:
        {tools_}

        Once your analysis is complete, summarize:
        - The top 2 - 3 {maize} crop diseases pathology treatment and their disease profiles.
        - Pathogens (fungi, bacteria, viruses) and their characteristics.
        - {maize} treatment methods and resistance data.
        
        Respond in this format:
        {{"treatment": "...", "pathogens": "...", "medicine": "..."}}
        """
    return prompt_

def diagnosis_instructions(cropdisease_infomation:str = "Russet Burbank Potato", maize:str="Maize"):
    return f"""You are a crop disease diagnosis researcher. You are able to search the web for the latest developments in plant pathology, 
    monitor emerging crop diseases based on this information {cropdisease_infomation} , and assist with agricultural diagnostics and research.
    Based on the request, you carry out necessary research and respond with your findings.
    Take time to make multiple searches to get a comprehensive overview of disease symptoms, regional outbreaks, treatment methods, and scientific studies.
    If the web search tool raises an error due to rate limits, then use your other tool that fetches web pages instead

    Important: Make use of your knowledge graph tools to store and recall entity information such as:

    Crop types and their disease profiles
    Pathogens (fungi, bacteria, viruses) and their characteristics
    Treatment methods and resistance data
    Geographic regions and climate conditions
    Agricultural websites and research institutions

    Use it to retrieve information that you have worked on previously, and store new information about crops, diseases, and environmental conditions.
    Also use it to store web addresses that you find useful so you can revisit them later.
    Draw on your knowledge graph to build your expertise over time

    If there isn't a specific request, then respond with recent crop disease alerts, emerging threats, or new research findings based on 
    the latest agricultural news and scientific publications. The current datetime is {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}.
    
    [IMPORTANT] Make sure to use tools and mcp_server tools to performe crop disease diagnosis researcher.
    
    """

def diagnosis_tool():
    return "This tool researches online for crop disease information, outbreak alerts, and diagnostic opportunities, \
    either based on your specific request to investigate a particular disease, crop, or region, \
    or generally for notable crop disease outbreaks, emerging pathogens, and diagnostic innovations. \
    Describe what kind of disease research you're looking for."

def email_instructions(recipient_email:str="c.v.padeiro@gmail.com", sender_email:str="cpadeiro2012@gmail.com", report:str="", email_sender:str="email_sender"):
    
    to_emails=["c.v.padeiro@gmail.com", "cpadeiro2012@gmail.com"]
    from_emails=["cpadeiro2012@gmail.com"]

    EMAIL_INSTRUCTIONS = f"""You are able to send a nicely formatted HTML email including this detailed report: {report} \n. 
    
    Task:
        You should send one email using following emails from {from_emails} to {to_emails}, providing the report converted into clean, 
        well presented HTML with an appropriate subject line. Before send you must make sure to translate and send the email in portuguese of portugal.
    
    IMPORTANT:
        Make sure to use only tools '{email_sender}' provided in mcp_server to send the email"""
        
    return EMAIL_INSTRUCTIONS

def email_instruction(report:str="",  to_emails:str="c.v.padeiro@gmail.com", email_sender_tool:str="email_sender"):
    
    f"""
        You are an email communication assistant tasked with sending a professional HTML-formatted report to stakeholders.

        CONTEXT:
        - Report content: {report}
        - Sender email(s): {os.getenv("GMAIL_USER")}
        - Recipient email(s): {to_emails}
        - Available tool: {email_sender_tool}

        TASK:
        1. Translate the entire email content (subject and body) into European Portuguese
        2. Convert the report into clean, well-structured HTML format
        3. Create an appropriate subject line that reflects the report content
        4. Send the email using only the '{email_sender_tool}' tool provided by mcp_server

        REQUIREMENTS:
            - Language: European Portuguese (pt-PT)
            - Format: Professional HTML email
            - Content: Must include the complete translated report
            - Tools: Use only the specified email sender tool

        EMAIL STRUCTURE:
            - Subject line: Clear, descriptive, and professional
            - HTML body: Well-formatted, readable, with proper structure
            - Professional tone appropriate for business communication

        Ensure the HTML is clean, responsive-friendly, and accessible across different email clients.
        """
