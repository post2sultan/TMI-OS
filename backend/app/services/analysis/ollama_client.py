import json
from typing import Any

import httpx

from app.core.settings import settings


class OllamaClient:

    def __init__(self) -> None:

        self.base_url = settings.OLLAMA_URL.rstrip("/")

        self.model = settings.OLLAMA_MODEL

        self.timeout = httpx.Timeout(
            connect=10.0,
            read=600.0,
            write=30.0,
            pool=10.0,
        )

    def generate(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.1,
        max_output_tokens: int = 1800,
    ) -> str:

        normalized_prompt = prompt.strip()

        if not normalized_prompt:
            raise ValueError(
                "Prompt cannot be empty."
            )

        if max_output_tokens <= 0:
            raise ValueError(
                "Maximum output tokens must be greater than zero."
            )

        selected_model = model or self.model

        payload: dict[str, Any] = {
            "model": selected_model,
            "prompt": normalized_prompt,
            "stream": False,
            "format": "json",
            "keep_alive": "10m",
            "options": {
                "temperature": temperature,
                "num_predict": max_output_tokens,
                "num_ctx": 8192,
            },
        }

        try:

            with httpx.Client(
                timeout=self.timeout,
            ) as client:

                response = client.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                )

                response.raise_for_status()

        except httpx.ConnectError as exc:

            raise RuntimeError(
                f"Unable to connect to Ollama at "
                f"{self.base_url}."
            ) from exc

        except httpx.TimeoutException as exc:

            raise RuntimeError(
                "Ollama request exceeded the configured "
                "generation timeout."
            ) from exc

        except httpx.HTTPStatusError as exc:

            raise RuntimeError(
                "Ollama returned an HTTP error: "
                f"{exc.response.status_code} "
                f"{exc.response.text}"
            ) from exc

        try:

            response_data = response.json()

        except json.JSONDecodeError as exc:

            raise RuntimeError(
                "Ollama returned an invalid HTTP response."
            ) from exc

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

        return generated_text


ollama_client = OllamaClient()