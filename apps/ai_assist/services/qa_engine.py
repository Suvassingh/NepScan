import openai
from django.conf import settings

def answer_question(document_text: str, question: str) -> str:
    openai.api_key = settings.OPENAI_API_KEY
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a document assistant. Answer the question based on the given text."},
            {"role": "user", "content": f"Document: {document_text}\n\nQuestion: {question}"}
        ],
        max_tokens=150
    )
    return response.choices[0].message.content