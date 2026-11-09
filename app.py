"""Aiven Bot Blog: an archive of AI-generated blog posts for Aiven."""

import html as htmllib
import json
import os
import re
from pathlib import Path

from render_engine import Collection, Site
from render_engine.page import Page
from render_engine.plugins import hook_impl
from render_engine_json import JSONPageParser
from render_engine_markdown import MarkdownPageParser

MODEL = "Claude Sonnet 5.5"
# The same JSON file feeds the Authors page (via JSONPageParser) and the author lookup in post templates.
AUTHORS_BY_SLUG = {
    a["slug"]: a for a in json.loads(Path("content/authors.json").read_text())
}

# Set SITE_URL in the deployment environment to the public origin (no trailing slash).
SITE_URL = os.environ.get("SITE_URL", "https://aivens-bot-blog.com").rstrip("/")


class SitemapPlugin:
    """Write sitemap.xml, robots.txt and llms.txt into the output folder after every build."""

    @hook_impl
    def post_build_site(site, settings):
        out = Path(site.output_path)
        names = ["index.html"] + sorted(
            f.name
            for f in out.glob("*.html")
            if f.name not in {"index.html", "404.html"}
        )
        entries = []
        post_links = []
        for name in names:
            loc = f"{SITE_URL}/" if name == "index.html" else f"{SITE_URL}/{name}"
            html = (out / name).read_text()
            # Posts carry their publish date; archive/about/authors have none, so omit lastmod.
            m = re.search(r'article:published_time" content="([^"]+)"', html)
            lastmod = f"<lastmod>{m.group(1)}</lastmod>" if m else ""
            entries.append(f"  <url><loc>{loc}</loc>{lastmod}</url>")
            if m:
                title = re.search(r"<title>(.*?)</title>", html, re.DOTALL)
                desc = re.search(r'<meta name="description" content="([^"]*)"', html)
                name_text = htmllib.unescape(title.group(1).strip())
                name_text = name_text.removesuffix(" · Aiven Bot Blog")
                link = f"- [{name_text}]({loc})"
                if desc:
                    link += f": {htmllib.unescape(desc.group(1)).strip()}"
                post_links.append(link)
        entries = "\n".join(entries)
        (out / "sitemap.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            f"{entries}\n</urlset>\n"
        )
        posts = "\n".join(post_links)
        (out / "llms.txt").write_text(
            "# Aiven Bot Blog\n\n"
            "> An archive of AI-generated posts about Aiven and open source data "
            "infrastructure. Nothing here is reviewed or endorsed by Aiven; verify "
            "commands, versions and pricing against https://aiven.io/docs.\n\n"
            "## Pages\n\n"
            f"- [About]({SITE_URL}/about.html): What this site is and how posts are made\n"
            f"- [Authors]({SITE_URL}/authors.html): The AI personas who write the posts\n"
            f"- [Sitemap]({SITE_URL}/sitemap.xml)\n\n"
            f"## Posts\n\n{posts}\n"
        )
        (out / "robots.txt").write_text(
            f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n"
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
app.register_plugins(SitemapPlugin)


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
