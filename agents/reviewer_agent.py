import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

class ReviewerAgent:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    def review(self, rewritten_text: str) -> dict:
        prompt = (
            "Review the following rewritten book chapter for grammar, style, coherence, and flow. "
            "Make any necessary improvements without changing the core message or meaning:\n\n"
            f"{rewritten_text}\n\n"
            "Improved Chapter:"
        )
        response = self.model.generate_content(prompt)
        return {
            "reviewed_text": response.text.strip(),
            "source": "ReviewerAgent"
        }