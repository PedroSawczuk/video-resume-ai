from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

apiKeyGemini = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=apiKeyGemini)

response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents=f"Bom dia!"
)

if response.text is not None:
    print(response.text)