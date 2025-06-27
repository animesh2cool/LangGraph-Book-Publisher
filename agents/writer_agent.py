import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

class WriterAgent:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    def rewrite(self, input_text: str) -> dict:
        prompt = (
            "Rewrite the following book chapter in a creative, engaging tone without changing its meaning.\n\n"
            f"{input_text}\n\n"
            "Rewritten Chapter:"
        )
        response = self.model.generate_content(prompt)
        return {
            "rewritten_text": response.text.strip(),
            "source": "WriterAgent"
        }