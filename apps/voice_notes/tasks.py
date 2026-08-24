import openai
from django.conf import settings

def transcribe_audio(audio_bytes: bytes) -> str:
    openai.api_key = settings.OPENAI_API_KEY
    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name
    try:
        with open(tmp_path, 'rb') as f:
            response = openai.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                language="ne"  # or "en"
            )
            return response.text
    finally:
        import os
        os.unlink(tmp_path)