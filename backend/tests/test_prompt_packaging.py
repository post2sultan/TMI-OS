import unittest

from app.services.prompt_service import PromptService


class PromptPackagingTests(unittest.TestCase):

    def test_analysis_prompt_is_loaded_from_backend_package(self) -> None:
        service = PromptService()
        content = service.load("analysis", "campaign_analysis.md")

        self.assertTrue(content.strip())
        self.assertEqual(service.prompts_dir.name, "prompts")
        self.assertEqual(service.prompts_dir.parent.name, "app")


if __name__ == "__main__":
    unittest.main()

