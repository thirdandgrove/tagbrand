#!/usr/bin/env python3
"""Check local URLs and publishing constraints in a staged site directory."""
import argparse
from html.parser import HTMLParser
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = set()
        self.noindex = False

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        self.urls.update(attrs[key] for key in ("href", "src", "poster", "data-vid") if attrs.get(key))
        if tag == "meta" and attrs.get("name", "").lower() == "robots":
            directives = {item.strip().lower() for item in attrs.get("content", "").split(",")}
            self.noindex |= "noindex" in directives


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    root = args.directory.resolve()
    source = (root / "index.html").read_text()
    page = Page()
    page.feed(source)
    errors = []
    for forbidden in ("window.claude", "/_blob/", "claude.ai/artifact"):
        if forbidden in source:
            errors.append(f"Forbidden runtime reference: {forbidden}")
    if not page.noindex:
        errors.append("Missing robots noindex meta")
    # Include literal paths in JS-rendered cards and lightbox maps as well as HTML.
    page.urls.update(re.findall(r'''(?:assets|downloads)/[A-Za-z0-9_./ -]+\.(?:zip|svg|png|webp|jpg|mp4|js|woff2)''', source))
    checked = 0
    for url in sorted(page.urls):
        parts = urlsplit(url)
        if parts.scheme or parts.netloc or not parts.path or "${" in url:
            continue
        path = (root / unquote(parts.path).lstrip("/")).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            errors.append(f"Unresolved local URL: {url}")
        checked += 1
    if errors:
        sys.exit("\n".join(errors))
    print(f"Site verified: {checked} local paths; noindex present; no Claude runtime references")


if __name__ == "__main__":
    main()
