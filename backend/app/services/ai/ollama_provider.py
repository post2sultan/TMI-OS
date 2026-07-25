import json
from typing import Any

import httpx

from app.core.settings import settings
from app.services.ai.base import AIProvider


class OllamaProvider(AIProvider):

    def __init__(self) -> None:
        self.base_url = settings.OLLAMA_URL.rstrip(
            "/"
        )

        self.timeout = httpx.Timeout(
            connect=settings.OLLAMA_CONNECT_TIMEOUT,
            read=settings.OLLAMA_READ_TIMEOUT,
            write=30.0,
            pool=10.0,
        )

    @property
    def name(self) -> str:
        return "ollama"

    def generate(
        self,
        prompt: str,
        model: str,
        temperature: float,
        max_output_tokens: int,
    ) -> str:

        payload: dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "keep_alive": settings.OLLAMA_KEEP_ALIVE,
            "options": {
                "temperature": temperature,
                "num_predict": max_output_tokens,
                "num_ctx": settings.AI_CONTEXT_WINDOW,
            },
        }

        try:
            with httpx.Client(
                timeout=self.timeout
            ) as client:

                response = client.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                )

                response.raise_for_status()

        except httpx.ConnectError as error:
            raise RuntimeError(
                "Unable to connect to Ollama at "
                f"{self.base_url}."
            ) from error

        except httpx.TimeoutException as error:
            raise RuntimeError(
                "Ollama generation timed out."
            ) from error

        except httpx.HTTPStatusError as error:
            raise RuntimeError(
                "Ollama HTTP error: "
                f"{error.response.status_code} "
                f"{error.response.text}"
            ) from error

        try:
            response_data = response.json()

        except json.JSONDecodeError as error:
            raise RuntimeError(
                "Ollama returned an invalid API response."
            ) from error

        generated_text = response_data.get(
            "response"
        )

        if not isinstance(
            generated_text,
            str,
        ):
            raise RuntimeError(
                "Ollama response did not contain "
                "generated text."
            )

        generated_text = generated_text.strip()

        if not generated_text:
            raise RuntimeError(
                "Ollama returned an empty response."
            )

        done = response_data.get(
            "done"
        )

        done_reason = response_data.get(
            "done_reason"
        )

        if done is not True:
            raise RuntimeError(
                "Ollama generation did not complete."
            )

        if done_reason == "length":
            raise RuntimeError(
                "Ollama output was truncated because "
                f"the {max_output_tokens}-token output "
                "limit was reached."
            )

        try:
            parsed_response = json.loads(
                generated_text
            )

        except json.JSONDecodeError as error:
            raise RuntimeError(
                "Ollama generated incomplete or "
                "invalid JSON."
            ) from error

        if not isinstance(
            parsed_response,
            dict,
        ):
            raise RuntimeError(
                "Ollama generated JSON that was not "
                "an object."
            )

        return generated_text

    def embed(
        self,
        text: str,
        model: str,
    ) -> list[float]:

        payload: dict[str, Any] = {
            "model": model,
            "input": text,
            "keep_alive": settings.OLLAMA_KEEP_ALIVE,
        }

        try:
            with httpx.Client(
                timeout=self.timeout
            ) as client:

                response = client.post(
                    f"{self.base_url}/api/embed",
                    json=payload,
                )

                response.raise_for_status()

        except httpx.ConnectError as error:
            raise RuntimeError(
                "Unable to connect to Ollama at "
                f"{self.base_url}."
            ) from error

        except httpx.TimeoutException as error:
            raise RuntimeError(
                "Ollama embedding timed out."
            ) from error

        except httpx.HTTPStatusError as error:
            raise RuntimeError(
                "Ollama HTTP error: "
                f"{error.response.status_code} "
                f"{error.response.text}"
            ) from error

        try:
            response_data = response.json()

        except json.JSONDecodeError as error:
            raise RuntimeError(
                "Ollama returned invalid embedding JSON."
            ) from error

        embeddings = response_data.get(
            "embeddings"
        )

        if (
            not isinstance(embeddings, list)
            or not embeddings
            or not isinstance(
                embeddings[0],
                list,
            )
        ):
            raise RuntimeError(
                "Ollama returned invalid embedding data."
            )

        return [
            float(value)
            for value in embeddings[0]
        ]


ollama_provider = OllamaProvider()