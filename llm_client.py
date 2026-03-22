# llm_client.py
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


class LLMClient:
    def __init__(self):
        self.api_key = os.getenv("LLM_API_KEY")
        self.model = os.getenv("LLM_MODEL", "gpt-4o-mini")
        self.timeout = float(os.getenv("LLM_TIMEOUT", "3"))
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None

    def generate_text(self, system_prompt: str, user_prompt: str) -> str:
        if not self.client:
            raise RuntimeError("Missing LLM_API_KEY")

        resp = self.client.chat.completions.create(
        model=self.model,
        messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
        ],
        temperature=0.9,
        timeout=self.timeout,
        )
        return resp.choices[0].message.content.strip()
