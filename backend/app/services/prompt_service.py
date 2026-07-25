from pathlib import Path


class PromptService:
    """
    Loads prompt templates from the project's prompts folder.
    """

    def __init__(self):
        self.project_root = Path(__file__).resolve().parents[3]
        self.prompts_dir = self.project_root / "prompts"

    def load(self, category: str, filename: str) -> str:
        prompt_path = self.prompts_dir / category / filename

        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt not found: {prompt_path}")

        return prompt_path.read_text(encoding="utf-8")


prompt_service = PromptService()