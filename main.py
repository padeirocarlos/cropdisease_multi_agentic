import asyncio
from dotenv import load_dotenv
from agentics.agentic import DiseaseDiagnosis

load_dotenv(override=True)

async def main(query:str="Russet Burbank Potato"):
    
    print(" ====== Hello from mult-agent! ====== ")
    query = input("What kind of crop disease would like to search and know about ?").strip()
    diseaseDiagnosis = DiseaseDiagnosis(name="Mult-agent")
    
    if not query:
        await diseaseDiagnosis.run(query)
    else:
        await diseaseDiagnosis.run()
        
if __name__ == "__main__":
    asyncio.run(main())
