"""Aiven Bot Blog: an archive of AI-generated blog posts for Aiven."""

import json
from pathlib import Path

from render_engine import Collection, Site
from render_engine.page import Page
from render_engine_json import JSONPageParser
from render_engine_markdown import MarkdownPageParser

MODEL = "Claude Sonnet 5.5"
# The same JSON file feeds the Authors page (via JSONPageParser) and the author lookup in post templates.
AUTHORS_BY_SLUG = {
    a["slug"]: a for a in json.loads(Path("content/authors.json").read_text())
}

SITE_URL = (
    "https://aiven-bot-blog.example.com"  # TODO: set the real URL before publishing
)

app = Site()
app.site_vars.update(
    {
        "SITE_TITLE": "Aiven Bot Blog",
        "SITE_URL": SITE_URL,
        "SITE_TAGLINE": "An archive of AI-generated posts about Aiven and open source data infrastructure.",
        "AUTHORS": AUTHORS_BY_SLUG,
    }
)
app.output_path = "output"


class MarkdownPage(Page):
    Parser = MarkdownPageParser
    parser_extras = {"markdown_extras": ["fenced-code-blocks", "tables", "header-ids"]}


@app.collection
class Posts(Collection):
    """Every AI-generated post lives in content/posts as a Markdown file."""

    content_path = "content/posts"
    content_type = MarkdownPage
    Parser = MarkdownPageParser
    parser_extras = {"markdown_extras": ["fenced-code-blocks", "tables", "header-ids"]}
    template = "post.html"
    archive_template = "archive.html"
    routes = ["./"]  # the archive *is* the home page
    sort_by = "date"
    sort_reverse = True
    has_archive = True
    include_suffixes = ["*.md"]
    feed_title = "Aiven Bot Blog"
    template_vars = {"collection_title": "All posts", "authors": AUTHORS_BY_SLUG}
    plugins = []


@app.page
class About(MarkdownPage):
    """Explains what this site is and how its posts are made."""

    title = "About"
    template = "page.html"
    content_path = "content/about.md"
    routes = ["./"]
    slug = "about"


@app.page
class Authors(Page):
    """Bios for the AI personas who write the posts, loaded from content/authors.json."""

    Parser = JSONPageParser
    title = "Authors"
    template = "authors.html"
    content_path = "content/authors.json"
    routes = ["./"]
    slug = "authors"
    template_vars = {"model": MODEL}
