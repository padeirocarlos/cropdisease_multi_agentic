
import os
import re
import gc
import json
from typing import TypedDict
from datetime import datetime

# --- Third-party ---
import requests
from PIL import Image
from io import BytesIO

from dotenv import load_dotenv
from agents import Agent, Tool, Runner
from .agents_tools import ImageGenerator
from .agents_client import model_client_name_dict
from mcp_server.multi_mcp_server import Multi_MCP_Server
from .out_puts import DiseaseSearchDataResult, PromptDataResult, ImageUrlResult
from utils.search_tools import tavily_tool_def, wikipedia_tool_def, arxiv_tool_def
from .instructions import diagnosis_instructions, image_generate, diagnosis_tool, email_instruction, crop_disease_research, crop_disease_image_prediction

load_dotenv(override=True)
    
class DiseaseDiagnosis:
    
    def __init__(self, name: str, model_name: str="llama3.2"):
        self.name = name
        self.model_name = model_name
        self.multi_mcp_server = None
        self.image_generate = ImageGenerator()
        
    async def connect_to_servers(self):
        self.multi_mcp_server = Multi_MCP_Server()
        await self.multi_mcp_server.connect_to_servers()
        return self.multi_mcp_server
        
    async def crop_disease_research_agent(self, crop_disease:str, tools_details: list[dict]=None, model_name: str = None, output_type=None) -> Agent:
        
        if self.multi_mcp_server is None:
            self.multi_mcp_server = await self.connect_to_servers()
        
        prompt_ = crop_disease_research(crop_disease=crop_disease, tools=tools_details)

        return Agent(
            name = self.name,
            tools = self.multi_mcp_server.available_tools,
            instructions = prompt_,
            model = self.get_model(self.model_name) if model_name is None else self.get_model(model_name),
            output_type=output_type,
            )
    
    async def crop_disease_image_prompt_agent(self, crop_disease: str,
                                              maize:str, 
                                              model_name: str = None, 
                                              output_type=None) -> Agent:
        if self.multi_mcp_server is None:
            self.multi_mcp_server = await self.connect_to_servers()
            
        return Agent(
            name = self.name,
            tools = self.multi_mcp_server.available_tools,
            instructions = crop_disease_image_prediction(crop_disease=crop_disease, 
                                                         maize = maize, ),
            model = self.get_model(self.model_name) if model_name is None else self.get_model(model_name),
            output_type=output_type,)
        
    async def crop_disease_image_generate_agent(self, prompt: str, 
                                                model_name: str = None,
                                                # response_format="url", 
                                                output_type=None) -> Agent:
        if self.multi_mcp_server is None:
            self.multi_mcp_server = await self.connect_to_servers()
            
        return Agent(
            name = self.name,
            tools = self.multi_mcp_server.available_tools,
            instructions = f"{prompt}",
            # response_format=response_format,
            model = self.get_model(self.model_name) if model_name is None else self.get_model(model_name),
            output_type=output_type,)
        
    async def create_email_agent(self, report, to_emails:str, email_sender_tool:str="email_sender", model_name:str="llama3.2", output_type=None) -> Agent:

        if self.multi_mcp_server is None:
            self.multi_mcp_server = await self.connect_to_servers()
        
        prompt_ = email_instruction(report=report, 
                                    to_emails=to_emails, 
                                    email_sender_tool = email_sender_tool,)

        # tools = [await self.multi_mcp_server.call_tool(tool_name=email_sender_tool, arguments={"body":None, "subject":None, "to_emails":None})]
        tools = self.multi_mcp_server.available_tools
        
        return Agent(
            name = self.name,
            instructions = prompt_,
            model = self.get_model(model_name),
            tools = tools,
            output_type=output_type,)
    
    async def create_disease_agent(self, query:str, diagnosis_mcp_servers, model_name:str="llama3.2", output_type=None) -> Agent:
        tool = await self.get_diagnosis_tool(query, diagnosis_mcp_servers, model_name)
        return Agent(
            name = self.name,
            instructions = diagnosis_instructions(query),
            model = self.get_model(model_name),
            tools = self.multi_mcp_server.available_tools,
            output_type=output_type,)
    
    async def run(self, query:str="Maize Streak Virus (MSV)", maize:str="Maize"):
        tools_details = [tavily_tool_def, wikipedia_tool_def, arxiv_tool_def]
        try:
            research_agent = await self.crop_disease_research_agent(crop_disease = f"{maize} {query}", 
                                                                    tools_details = tools_details,
                                                                    model_name=self.get_model("qwen3"), # gemma12B_v gemma4B_v qwen3 gemini deepseek qwen3-coder
                                                                    # output_type=None,
                                                                    output_type=DiseaseSearchDataResult,
                                                                    )
            research_agent_result = await Runner.run(research_agent, query)
            pathsogens = research_agent_result.final_output.pathsogens
            medicine = research_agent_result.final_output.medicine
            treatment = research_agent_result.final_output.treatment
            await self.multi_mcp_server.cleanup()
            
            print(f" research_agent_result : === pathsogens : {pathsogens} === \n ")
            
            
            prompt_agent = await self.crop_disease_image_prompt_agent(crop_disease = pathsogens,
                                                                    maize=maize, 
                                                                    model_name=self.get_model("llama3.2"), # llama3 gemma12B_v gemma4B_v qwen3 gemini deepseek qwen3-coder
                                                                    output_type=PromptDataResult,
                                                                    )
            
            messages = [{"role": "user", "content": pathsogens}]
            prompt_agent_result = await Runner.run(prompt_agent, messages)
            prompt = prompt_agent_result.final_output.prompt
            caption = prompt_agent_result.final_output.caption
            await self.multi_mcp_server.cleanup()
            
            print(f" prompt_agent_result : === prompt : {prompt} === \n caption : {caption}  \n")
            
            system_message = (f"""
                "You are an email communication assistant tasked with sending a professional HTML-formatted report to Agriculter farmer.""")
            
            report_ = f"Treatment: {treatment} \n  Medicine: {medicine}\n Pathsogens: {pathsogens} \n "
            
            
            generate_agent = await self.create_email_agent(report=report_,
                                                         to_emails="c.v.padeiro@gmail.com, cpadeiro2012@gmail.com",
                                                         model_name= "llama3.2",
                                                         email_sender_tool="email_sender",
                                                         output_type=ImageUrlResult)  # "llava7B_v", "qwen2_v", "gemma12B_v"
            
            await Runner.run(generate_agent, system_message)
            await self.multi_mcp_server.cleanup()
            
            for i, prompt_ in enumerate(prompt):
                dt = datetime.now()
                name = f"prompt_{i}_{dt.strftime("%Y_%m_%d")}{dt.hour}{dt.minute}{dt.second}"
                out_path_name=os.path.join(os.getcwd(),"generate_image_path",f"{name}.png")
                # out_path_name=os.path.join("generate_image_path",f"{name}.png")
                
                self.image_generate.memory_optimizer(optimizer_type="offload") 
                self.image_generate.memory_optimizer(optimizer_type="vae_slicing") 
                self.image_generate.memory_optimizer(optimizer_type="attention_slicing") 
                
                image = self.image_generate.generate(prompt = prompt_, device="cpu")
                image[0].save(out_path_name)
                if i>=3: # consider only 3 prompts
                    break
            
        except Exception as e:
            print(f"Error running diagnosis {self.name}: {e}")
    
    async def get_diagnosis(self, query, mcp_servers, model_name) -> Agent:
        return Agent(
            name = "Crop disease diagnosis",
            instructions = diagnosis_instructions(query),
            model = self.get_model(model_name),
            mcp_servers = mcp_servers,)
    
    async def get_diagnosis_tool(self, query, mcp_servers, model_name) -> Tool:
        diagnosis = await self.get_diagnosis(query, mcp_servers, model_name)
        return diagnosis.as_tool(tool_name="diagnosis", tool_description=diagnosis_tool())
    
    def get_model(self, model_name: str) -> Agent:
        return model_client_name_dict.get(model_name, model_client_name_dict["ollama"])
