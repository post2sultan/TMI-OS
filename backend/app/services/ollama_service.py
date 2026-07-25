import requests

from app.core.settings import settings


class OllamaService:

    def generate(self, prompt: str):

        response = requests.post(
            f"{settings.OLLAMA_URL}/api/generate",
            json={
                "model": settings.OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False
            },
            timeout=300
        )

        response.raise_for_status()

        return response.json()["response"]


ollama_service = OllamaService()