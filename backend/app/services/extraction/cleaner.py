import re

from bs4 import BeautifulSoup


REMOVABLE_TAGS = {
    "aside",
    "button",
    "canvas",
    "dialog",
    "footer",
    "form",
    "iframe",
    "input",
    "nav",
    "noscript",
    "script",
    "select",
    "style",
    "svg",
    "template",
    "textarea",
}


def clean_text(
    value: str,
) -> str:
    if not value:
        return ""

    value = value.replace(
        "\u00a0",
        " ",
    )

    value = re.sub(
        r"[ \t]+",
        " ",
        value,
    )

    value = re.sub(
        r"\n[ \t]+",
        "\n",
        value,
    )

    value = re.sub(
        r"\n{3,}",
        "\n\n",
        value,
    )

    return value.strip()


def html_to_markdown_like_text(
    html: str,
) -> str:
    soup = BeautifulSoup(
        html,
        "lxml",
    )

    for tag_name in REMOVABLE_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    for heading_level in range(1, 7):
        for heading in soup.find_all(
            f"h{heading_level}"
        ):
            text = heading.get_text(
                " ",
                strip=True,
            )

            if text:
                heading.replace_with(
                    "\n"
                    + ("#" * heading_level)
                    + " "
                    + text
                    + "\n"
                )

    for item in soup.find_all("li"):
        text = item.get_text(
            " ",
            strip=True,
        )

        if text:
            item.replace_with(
                f"\n- {text}"
            )

    for paragraph in soup.find_all(
        ["p", "blockquote"]
    ):
        text = paragraph.get_text(
            " ",
            strip=True,
        )

        if text:
            paragraph.replace_with(
                f"\n{text}\n"
            )

    return clean_text(
        soup.get_text(
            "\n",
            strip=True,
        )
    )
