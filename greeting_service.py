# greeting_service.py
import random
from llm_client import LLMClient

FALLBACK = [
"👋 Chào mừng bạn quay lại!",
"✨ Chúc bạn một ngày làm việc hiệu quả!",
"🚀 Sẵn sàng chốt đơn nào!",
]

def generate_greeting():
    try:
        llm = LLMClient()
        txt = llm.generate_text(
        "Bạn viết câu chào UI phần mềm Fsales tiếng Việt, ngắn, tích cực, chuyên nghiệp.",
        "Viết 1 câu chào 8-14 từ, không emoji quá 1 cái."
        )
        if len(txt) < 8 or len(txt) > 80:
            raise ValueError("bad length")
        return txt
    except Exception:
        return random.choice(FALLBACK)