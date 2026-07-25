import json
from datetime import datetime
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from dateutil import parser as date_parser


def _meta_content(
    soup: BeautifulSoup,
    *selectors: tuple[str, str],
) -> str:
    for attribute, value in selectors:
        tag = soup.find(
            "meta",
            attrs={attribute: value},
        )

        if tag:
            content = str(
                tag.get("content") or ""
            ).strip()

            if content:
                return content

    return ""


def _parse_date(
    value: str,
) -> datetime | None:
    if not value:
        return None

    try:
        parsed = date_parser.parse(value)

        if parsed.tzinfo is None:
            return parsed

        return parsed

    except Exception:
        return None


def _json_ld_documents(
    soup: BeautifulSoup,
) -> list[dict[str, Any]]:
    documents: list[dict[str, Any]] = []

    scripts = soup.find_all(
        "script",
        attrs={
            "type": "application/ld+json"
        },
    )

    for script in scripts:
        raw = script.string or script.get_text()

        if not raw:
            continue

        try:
            payload = json.loads(raw)

        except Exception:
            continue

        if isinstance(payload, dict):
            graph = payload.get("@graph")

            if isinstance(graph, list):
                documents.extend(
                    item
                    for item in graph
                    if isinstance(item, dict)
                )

            documents.append(payload)

        elif isinstance(payload, list):
            documents.extend(
                item
                for item in payload
                if isinstance(item, dict)
            )

    return documents


def extract_metadata(
    html: str,
    base_url: str,
) -> dict[str, Any]:
    soup = BeautifulSoup(
        html,
        "lxml",
    )

    title = _meta_content(
        soup,
        ("property", "og:title"),
        ("name", "twitter:title"),
    )

    if not title and soup.title:
        title = soup.title.get_text(
            " ",
            strip=True,
        )

    description = _meta_content(
        soup,
        ("property", "og:description"),
        ("name", "description"),
        ("name", "twitter:description"),
    )

    author = _meta_content(
        soup,
        ("name", "author"),
        ("property", "article:author"),
    )

    publisher = _meta_content(
        soup,
        ("property", "og:site_name"),
        ("name", "application-name"),
    )

    language = ""

    html_tag = soup.find("html")

    if html_tag:
        language = str(
            html_tag.get("lang") or ""
        ).strip()

    published_raw = _meta_content(
        soup,
        (
            "property",
            "article:published_time",
        ),
        ("name", "date"),
        ("name", "publish-date"),
        ("name", "pubdate"),
    )

    hero_image = _meta_content(
        soup,
        ("property", "og:image"),
        ("name", "twitter:image"),
    )

    for document in _json_ld_documents(
        soup
    ):
        document_type = document.get("@type")

        if isinstance(document_type, list):
            types = {
                str(item).lower()
                for item in document_type
            }

        else:
            types = {
                str(document_type).lower()
            }

        relevant_types = {
            "article",
            "blogposting",
            "newsarticle",
            "report",
            "creativework",
        }

        if not types.intersection(
            relevant_types
        ):
            continue

        title = (
            title
            or str(
                document.get("headline")
                or document.get("name")
                or ""
            ).strip()
        )

        description = (
            description
            or str(
                document.get("description")
                or ""
            ).strip()
        )

        author_data = document.get("author")

        if not author:
            if isinstance(author_data, dict):
                author = str(
                    author_data.get("name")
                    or ""
                ).strip()

            elif isinstance(author_data, list):
                author_names = []

                for item in author_data:
                    if isinstance(item, dict):
                        name = str(
                            item.get("name")
                            or ""
                        ).strip()

                        if name:
                            author_names.append(
                                name
                            )

                author = ", ".join(
                    author_names
                )

            elif isinstance(author_data, str):
                author = author_data.strip()

        publisher_data = document.get(
            "publisher"
        )

        if (
            not publisher
            and isinstance(
                publisher_data,
                dict,
            )
        ):
            publisher = str(
                publisher_data.get("name")
                or ""
            ).strip()

        published_raw = (
            published_raw
            or str(
                document.get(
                    "datePublished"
                )
                or ""
            ).strip()
        )

        image_data = document.get("image")

        if not hero_image:
            if isinstance(image_data, str):
                hero_image = image_data

            elif isinstance(image_data, dict):
                hero_image = str(
                    image_data.get("url")
                    or ""
                ).strip()

            elif isinstance(image_data, list):
                for item in image_data:
                    if isinstance(item, str):
                        hero_image = item
                        break

                    if isinstance(item, dict):
                        candidate = str(
                            item.get("url")
                            or ""
                        ).strip()

                        if candidate:
                            hero_image = candidate
                            break

    if hero_image:
        hero_image = urljoin(
            base_url,
            hero_image,
        )

    return {
        "title": title,
        "description": description,
        "author": author,
        "publisher": publisher,
        "language": language,
        "published_at": _parse_date(
            published_raw
        ),
        "hero_image": hero_image,
    }
