import os
import gc
import torch

# --- Third-party ---
from dotenv import load_dotenv
from huggingface_hub import login
from utils.api_base_url import ApiConfig
from diffusers import StableDiffusionPipeline, AutoPipelineForText2Image, DiffusionPipeline
# from transformers import AutoTokenizer, AutoModelForCausalLM, TextStreamer, BitsAndBytesConfig

load_dotenv(override=True)
hf_token = os.getenv(ApiConfig.HUGGING_FACE_API_TOKEN)

## Decision Tree: Which Pipeline to Use?
# ```
# Do you know the exact model family?
# ├─ YES, it's Stable Diffusion v1.x/v2.x
# │  └─> Use StableDiffusionPipeline (most explicit control)
# │
# ├─ YES, it's FLUX
# │  └─> Use FluxPipeline (FLUX-specific optimizations)
# │
# ├─ NO, could be anything
# │  └─> Use DiffusionPipeline (maximum flexibility)
# │
# └─ Want task-specific features for text-to-image?
#    └─> Use AutoPipelineForText2Image (clear intent + optimizations)

class ImageGenerator:
    
    def __init__(self, model_id:str = "stabilityai/stable-diffusion-xl-base-1.0",dtype=torch.float16):
        login(hf_token, add_to_git_credential=True)
        self.dtype = dtype
        
        self.pipeline = AutoPipelineForText2Image.from_pretrained(
                    model_id,
                    dtype = self.dtype,
                    safety_checker = True, 
                    use_safetensors = True,
                    # variant="fp16"
                    )
    
    def memory_optimizer(self, optimizer_type:str="offload"):
        if optimizer_type == "offload":
            self.pipeline.enable_model_cpu_offload()  # Aggressive memory saving
            
        elif optimizer_type == "vae_slicing":
            self.pipeline.enable_vae_slicing()         # Reduce memory for VAE
            
        else:
            self.pipeline.enable_attention_slicing()   # Reduce memory for attention
    
    def generate(self, prompt: str="", negative_prompt: str = "", size:dict = (512, 512),  pipeline_type:str ="text2Image", model_id:str = None, device:str="cuda"):
        
        if pipeline_type == "text2Image":
            
            if model_id is None:
                model_id = "stabilityai/stable-diffusion-xl-base-1.0"
            
            self.pipeline = AutoPipelineForText2Image.from_pretrained(
                    model_id,
                    dtype = self.dtype,
                    safety_checker = True, 
                    use_safetensors = True,
                    # variant="fp16"
                    ).to(device)
                
            image =  self.pipeline(
                prompt = prompt,
                negative_prompt = negative_prompt,
                num_inference_steps = 40,
                guidance_scale = 7.5,
                height = size[0],
                width = size[1],)
            return image[0]
            
        if pipeline_type == "diffusion":
            
            if model_id is None:
                model_id = "runwayml/stable-diffusion-v1-5"
            # Explicitly for Stable Diffusion v1.x/v2.x
            self.pipeline = DiffusionPipeline.from_pretrained(
                    model_id,
                    dtype = self.dtype,
                    safety_checker = True, 
                    use_safetensors = True,
                    # variant="fp16"
                    ).to(device)
            
            image = self.pipeline(
                prompt=prompt,
                negative_prompt = negative_prompt,
                num_inference_steps = 50,
                guidance_scale = 7.5,
                height = size[0],
                width = size[1],)
            
            return image[0]
    
        if pipeline_type == "stableDiffusion":
            
            if model_id is None:
                model_id = "runwayml/stable-diffusion-v1-5"
                
            # Explicitly for Stable Diffusion v1.x/v2.x
            self.pipeline = StableDiffusionPipeline.from_pretrained(
                    model_id,
                    # dtype = self.dtype, # Not used in Stable Diffusion pipeline
                    # safety_checker = True, # Not used in Stable Diffusion pipeline
                    use_safetensors = True,
                    variant="fp16").to("cuda")
            
            # Classic SD interface
            image = self.pipeline(
                prompt=prompt,
                negative_prompt = negative_prompt,
                num_inference_steps = 50,
                guidance_scale = 7.5,
                height = size[0],
                width = size[1])
            return image[0]

  
