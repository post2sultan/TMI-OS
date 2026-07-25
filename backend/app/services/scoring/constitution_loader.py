from pathlib import Path


class ConstitutionLoader:

    def __init__(
        self,
        constitution_directory: Path | None = None,
    ) -> None:

        if constitution_directory is None:
            constitution_directory = (
                Path(__file__).resolve().parents[3]
                / "prompts"
                / "framework"
            )

        self.constitution_directory = constitution_directory

    def load(
        self,
        version: str,
    ) -> str:

        normalized_version = version.strip()

        if not normalized_version:
            raise ValueError(
                "Constitution version cannot be empty."
            )

        if not normalized_version.replace(".", "").isdigit():
            raise ValueError(
                "Constitution version must contain only "
                "numbers and periods."
            )

        filename_version = normalized_version.replace(
            ".",
            "_",
        )

        constitution_path = (
            self.constitution_directory
            / f"constitution_v{filename_version}.md"
        )

        if not constitution_path.is_file():
            raise FileNotFoundError(
                "Constitution file was not found: "
                f"{constitution_path}"
            )

        content = constitution_path.read_text(
            encoding="utf-8",
        ).strip()

        if not content:
            raise ValueError(
                "Constitution file cannot be empty."
            )

        return content


constitution_loader = ConstitutionLoader()