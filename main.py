import asyncio
from dotenv import load_dotenv
from agentics.agentic import DiseaseDiagnosis

load_dotenv(override=True)

async def main(query:str="Maize Streak Virus (MSV)"): # Northern corn Leaf Blight Fall ArmyWorm
     
    print(" ====== Hello from crop disease mult-agentic! ====== ")
    query = input("What kind of maize disease would like to search and know about ?").strip()
    diseaseDiagnosis = DiseaseDiagnosis(name="Cropdisease-Mult-Agentic")
    
    if not query:
        await diseaseDiagnosis.run(query)
    else:
        await diseaseDiagnosis.run()
        
if __name__ == "__main__":
    asyncio.run(main())
