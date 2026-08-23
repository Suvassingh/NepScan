import openai
from django.conf import settings

def generate_summary(text: str) -> str:
    if not text:
        return ""
    openai.api_key = settings.OPENAI_API_KEY
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Summarize the following document text concisely."},
            {"role": "user", "content": text}
        ],
        max_tokens=200
    )
    return response.choices[0].message.content