# utils.py
from rag_manager import RAGManager
import aiohttp
from dotenv import load_dotenv
import os
from groq import Groq

LLM_API_KEY = os.getenv('LLM_API_KEY')
url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={LLM_API_KEY}"

# Function to generate content using Gemini LLM API
async def generate_content(prompt) -> str:
    headers = {
        'Content-Type': 'application/json',
    }
    data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }

    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
        try:
            async with session.post(url, headers=headers, json=data) as response:
                result = await response.json()
                return result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', llama_llm_call(prompt))
        except aiohttp.ClientError as e:
            return f"There was an error generating the response: {str(e)}"
        except Exception as e:
            return f"An unexpected error occurred: {str(e)}"
        

def llama_llm_call(prompt):
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')

    client = Groq(
        api_key=GROQ_API_KEY,
    )
    completion = client.chat.completions.create(
        model="llama-3.1-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are porfessional tech interviewer in IT industry."
            },
            {
                "role": "user",
                "content": prompt,
            }
        ],
        temperature=1,
        max_tokens=1024,
        top_p=1,
        stream=False,
        response_format={"type": "json_object"},
    )
    result = completion.choices[0].message.content
    print(result)
    return result