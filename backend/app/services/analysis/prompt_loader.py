from pathlib import Path


class PromptLoader:

    def __init__(self) -> None:
        self.prompts_root = (
            Path(__file__).resolve().parents[3]
            / "prompts"
        )

    def load(
        self,
        prompt_name: str,
        category: str = "analysis",
    ) -> str:

        if not prompt_name:
            raise ValueError(
                "Prompt name cannot be empty."
            )

        prompt_path = (
            self.prompts_root
            / category
            / f"{prompt_name}.md"
        )

        if not prompt_path.exists():
            raise FileNotFoundError(
                f"Prompt file not found: {prompt_path}"
            )

        if not prompt_path.is_file():
            raise ValueError(
                f"Prompt path is not a file: {prompt_path}"
            )

        content = prompt_path.read_text(
            encoding="utf-8"
        ).strip()

        if not content:
            raise ValueError(
                f"Prompt file is empty: {prompt_path}"
            )

        return content


prompt_loader = PromptLoader()