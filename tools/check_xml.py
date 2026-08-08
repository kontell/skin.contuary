#!/usr/bin/env python3
"""Check every skin XML file is well-formed enough for Kodi to load it.

A malformed skin XML is a silent failure that costs an hour: Kodi logs a parse
error somewhere in kodi.log, renders the window without the broken include, and
carries on. Nothing in this repo caught that before.

**Comments are stripped before parsing, deliberately.** Kodi parses skin XML with
pugixml, which finds the end of a comment by scanning for ``-->`` and does not
enforce the XML rule that ``--`` may not appear inside one. Several files here
have prose comments containing ``--`` (``xml/Includes_Lyrics.xml`` is one) and
Kodi loads them perfectly. A spec-exact check would fail them on day one and the
"fix" would be rewording documentation to satisfy a parser Kodi does not use.
Stripping comments keeps everything that actually breaks a skin — unescaped
ampersands, mismatched or unclosed tags, unquoted attributes, stray ``<`` — while
ignoring the one difference that is only theoretical here.

Covers ``*.xml`` (windows, includes, colours, addon.xml) and ``*.xsp``
(smart playlists), which are XML too.

Usage: check_xml.py [ROOT]      (default ROOT: the repo root)
"""

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
SUFFIXES = ("*.xml", "*.xsp")
SKIP_DIRS = {".git", ".github", ".claude", ".tox", "dist", "__pycache__"}


def candidates(root):
    for pattern in SUFFIXES:
        for path in root.rglob(pattern):
            if SKIP_DIRS.isdisjoint(path.parts):
                yield path


def main(argv):
    root = Path(argv[0]).resolve() if argv else ROOT
    failures = []
    checked = 0
    for path in sorted(candidates(root)):
        checked += 1
        text = path.read_text(encoding="utf-8", errors="replace")
        try:
            ET.fromstring(COMMENT.sub("", text))
        except ET.ParseError as exc:
            failures.append((path.relative_to(root), exc))

    if not checked:
        sys.exit(f"no XML found under {root} — wrong directory?")

    for rel, exc in failures:
        print(f"{rel}: {exc}", file=sys.stderr)
    if failures:
        sys.exit(f"{len(failures)} of {checked} XML file(s) are malformed")
    print(f"{checked} XML files are well-formed")


if __name__ == "__main__":
    main(sys.argv[1:])
