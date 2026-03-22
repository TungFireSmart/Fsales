from openai import OpenAI
from AI.ai_config import OPENAI_API_KEY, MODEL_NAME

_client = OpenAI(api_key=OPENAI_API_KEY)


def ask_chatgpt(prompt: str) -> str:
    try:
        resp = _client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Bạn là Anna, trợ lý AI cho quản lý CRM FSales. "
                        "Trả lời ngắn gọn, rõ ràng, bằng tiếng Việt, giọng chuyên nghiệp và thân thiện."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=300,
            timeout=15
        )
        return resp.choices[0].message.content.strip()

    except Exception as e:
        return f"Lỗi ChatGPT: {e}"
