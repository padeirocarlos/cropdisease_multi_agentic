
import os
import re
import json
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
from .instructions import diagnosis_instructions, image_generate, diagnosis_tool, email_instructions, crop_disease_research, crop_disease_image_prediction

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
                                              caption_style: str = "short punchy", 
                                              moths_one:int=2, moths_two:int=4, 
                                              model_name: str = None, 
                                              output_type=None) -> Agent:
        if self.multi_mcp_server is None:
            self.multi_mcp_server = await self.connect_to_servers()
            
        return Agent(
            name = self.name,
            tools = self.multi_mcp_server.available_tools,
            instructions = crop_disease_image_prediction(crop_disease=crop_disease, 
                                                         caption_style = caption_style, 
                                                         moths_one=moths_one, moths_two=moths_two),
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
        
    async def create_email_agent(self, report, model_name:str="llama3.2", output_type=None) -> Agent:

        return Agent(
            name = self.name,
            instructions = email_instructions(report=report),
            model = self.get_model(model_name),
            tools = self.multi_mcp_server.available_tools,
            output_type=output_type,)
    
    async def create_disease_agent(self, query:str, diagnosis_mcp_servers, model_name:str="llama3.2", output_type=None) -> Agent:
        tool = await self.get_diagnosis_tool(query, diagnosis_mcp_servers, model_name)
        return Agent(
            name = self.name,
            instructions = diagnosis_instructions(query),
            model = self.get_model(model_name),
            tools = self.multi_mcp_server.available_tools,
            output_type=output_type,)
    
    async def run(self, query:str="Russet Burbank Potato"):
        tools_details = [tavily_tool_def, wikipedia_tool_def, arxiv_tool_def]
        try:
            research_agent = await self.crop_disease_research_agent(crop_disease = query, 
                                                                    tools_details = tools_details,
                                                                    model_name=self.get_model("qwen3"), # gemma12B_v gemma4B_v qwen3 gemini deepseek qwen3-coder
                                                                    # output_type=None,
                                                                    output_type=DiseaseSearchDataResult,
                                                                    )
            research_agent_result = await Runner.run(research_agent, query)
            pathsogens = research_agent_result.final_output.pathsogens
            await self.multi_mcp_server.cleanup()
            
            print(f" research_agent_result : === pathsogens : {pathsogens} === \n ")
            
            
            prompt_agent = await self.crop_disease_image_prompt_agent(crop_disease = pathsogens, 
                                                                    moths_one=2, 
                                                                    moths_two=4,
                                                                    model_name=self.get_model("gemma12B_v"), # llama3 gemma12B_v gemma4B_v qwen3 gemini deepseek qwen3-coder
                                                                    output_type=PromptDataResult,
                                                                    )
            
            messages = [{"role": "user", "content": pathsogens}]
            prompt_agent_result = await Runner.run(prompt_agent, messages)
            prompt = prompt_agent_result.final_output.prompt
            caption = prompt_agent_result.final_output.caption
            await self.multi_mcp_server.cleanup()
            
            print(f" prompt_agent_result : === prompt : {prompt} === \n caption : {caption}  \n")
            
            system_message = (f"""
                "You are a visual crop disease assistant. Based on the input trend insights in {pathsogens}, 
                generate two images using a given prompt and caption.""")
            
            prompt_ = image_generate(pathsogens=pathsogens, 
                                     prompts=prompt, 
                                     caption=caption,
                                     path=os.path.join(os.getcwd(), "generate_image_path"))
            
            generate_agent = await self.crop_disease_image_generate_agent(prompt=prompt_,
                                                                          model_name= "gemma12B_v",
                                                                        # response_format="url", 
                                                                          output_type=ImageUrlResult)  # "llava7B_v", "qwen2_v", "gemma12B_v"
            
            generate_agent_result = await Runner.run(generate_agent, system_message)
            image_url1 = generate_agent_result.final_output.imageUrl1
            image_url2 = generate_agent_result.final_output.imageUrl2
            await self.multi_mcp_server.cleanup()
            
            print(f" generate_agent_result : === imageUrl1: {image_url1}  \n imageUrl2: {image_url2} === ")
            
            for i, prompt_ in enumerate(prompt):
                dt = datetime.now()
                name = f"prompt_{i}_{dt.strftime("%Y_%m_%d")}{dt.hour}{dt.minute}{dt.second}"
                out_path_name=os.path.join(os.getcwd(),"out_puts",f"{name}.png")
                # out_path_name=os.path.join("out_puts",f"{name}.png")
                
                if False:
                    self.image_generate.memory_optimizer(optimizer_type="offload") 
                    self.image_generate.memory_optimizer(optimizer_type="vae_slicing") 
                    self.image_generate.memory_optimizer(optimizer_type="attention_slicing") 
                
                image = self.image_generate.generate(prompt = prompt_)
                image.save(out_path_name)
            
            # Save image locally
            # img_bytes = requests.get(image_url1).content
            # img = Image.open(BytesIO(img_bytes))

            # filename = os.path.basename(image_url1.split("?")[0])
            # image_path0 = filename+"0"
            # img.save(os.path.join(os.getcwd(), "generate_image_path/", {image_path0}))
            
            # img_bytes = requests.get(image_url2).content
            # img = Image.open(BytesIO(img_bytes))

            # filename = os.path.basename(image_url2.split("?")[0])
            # image_path1 = filename+"1"
            # img.save(os.path.join(os.getcwd(), "generate_image_path/", {image_path1}))
            
            # return {
            #     "caption": caption,
            #     "image_url1": image_url1,
            #     "image_url2": image_url2,
            #     }
        
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
