"""MkDocs hook (mkdocs.yml).

- Headings get the same ids as on GitHub, so the manuals' tables of contents
  (#let-varid--varexpression-1) work on the site too.
- ```cyd blocks are highlighted with the CYD lexer (tools/cyd_pygments.py).

GitHub: lowercase, everything but letters, digits, '_', '-' and spaces out,
each space to '-', and a repeated id gets -1, -2... Python-Markdown would
collapse the spaces and number the repeats _1, _2...
"""

import re
import sys
from pathlib import Path

import markdown.extensions.toc as toc
import pymdownx.highlight as highlight

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cyd_pygments import CydLexer  # noqa: E402

_get_lexer_by_name = highlight.get_lexer_by_name


def github_slug(value, separator="-"):
    value = re.sub(r"[^\w\- ]", "", value.strip().lower())
    return value.replace(" ", separator)


def github_unique(id, ids, counters=None):
    # `counters` (Markdown >= 3.11.3) is only a speed-up cache for repeated
    # ids; the manuals are small, so it is not needed here.
    base, n = id, 0
    while id in ids or not id:
        n += 1
        id = f"{base}-{n}"
    ids.add(id)
    return id


def get_lexer_by_name(name, **options):
    if name.lower() == "cyd":
        return CydLexer(**options)
    return _get_lexer_by_name(name, **options)


def on_config(config, **kwargs):
    toc.unique = github_unique
    config["mdx_configs"].setdefault("toc", {})["slugify"] = github_slug
    highlight.get_lexer_by_name = get_lexer_by_name
    return config
