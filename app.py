import asyncio
import gradio as gr
from pathlib import Path
from dotenv import load_dotenv
from agentics.agentic import DiseaseDiagnosis

load_dotenv(override=True)

async def run(query:str="Russet Burbank Potato"):
    diseaseDiagnosis = DiseaseDiagnosis(name="crop disease detection mult-agent")
    resutl = await diseaseDiagnosis.run(query)
    # Tell me about this crop disease Russet Burbank Potato
    yield resutl

def create_ui():
    with gr.Blocks(theme = gr.themes.Default(primary_hue="sky")) as ui:
        
        gr.Markdown(" ====== Hello from mult-agent! ======")
        
        query_textbox = gr.Textbox(label = " What kind of crop disease would like to search and know about ?")
        run_button = gr.Button("Run", variant="primary")
        
        # report = gr.Markdown(label="Report")
        # run_button.click(fn=run, inputs=query_textbox, outputs = report)
        run_button.click(fn=run, inputs=query_textbox)
        
    return ui

if __name__ == "__main__":
    ui = create_ui()
    ui.launch(share=True)