# utils.py
from rag_manager import RAGManager
import aiohttp
from dotenv import load_dotenv
import os

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
                return result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', 'No response generated.')
        except aiohttp.ClientError as e:
            return f"There was an error generating the response: {str(e)}"
        except Exception as e:
            return f"An unexpected error occurred: {str(e)}"