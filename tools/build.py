#!/usr/bin/env python3
"""Build a Kodi-installable zip of the skin.

Packages the working tree into ``<outdir>/skin.contuary-<version>[-<channel>].zip``
with every file nested under a top-level ``skin.contuary/`` directory, exactly as
Kodi's "Install from zip file" expects, and as the repository's updater expects
of a release asset (it parses the ``-<channel>`` suffix).

This is a variant of the shared Kontell tools/build.py rather than a copy of it,
for three reasons specific to this repo:

* the skin ships a different file set (no README, no Screenshot) — EXCLUDE_TOP
  below mirrors the ``export-ignore`` list in .gitattributes, which is what the
  superseded build.sh relied on via ``git archive``;
* releases are per-channel, so the zip name carries ``-omega`` / ``-piers``;
* it packages the *working tree*, where ``git archive HEAD`` packaged the commit.
  That is the point — it is what makes tools/dev-install.sh able to install
  uncommitted work — but it also means a release built from a dirty tree would
  quietly ship it, so untracked and modified files are reported (see
  ``report_dirty``). CI builds from a clean checkout and prints nothing.

Keep EXCLUDE_TOP and .gitattributes in step. Either alone is a file that ships
when it should not.

Usage: build.py [OUTDIR] [--channel omega|piers]   (default OUTDIR: ./dist)
"""

import os
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Path components skipped wherever they appear: VCS, caches, agent config.
EXCLUDE_ANYWHERE = {
    "CLAUDE.md",
    ".claude",
    ".git",
    ".venv",
    "venv",
    ".tox",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".DS_Store",
}
# Repo-root entries that are development-only. Mirrors the export-ignore list in
# .gitattributes, plus the build's own output dir and editor folders.
EXCLUDE_TOP = {
    "docs",
    "tools",
    "dist",
    "build.sh",
    "README.md",
    "Screenshot.png",
    "ICONS_ONLY_MENU_PLAN.md",
    ".gitattributes",
    ".gitignore",
    ".git-blame-ignore-revs",
    ".github",
    ".vscode",
    ".idea",
}
EXCLUDE_SUFFIX = (".pyc", ".pyo")

CHANNELS = ("omega", "piers")


def addon_meta():
    """(id, version) read from addon.xml — the zip name and top-level dir."""
    root = ET.parse(ROOT / "addon.xml").getroot()
    return root.get("id"), root.get("version")


def iter_files():
    """Every repo-relative path to package, in deterministic order."""
    for dirpath, dirnames, filenames in os.walk(ROOT):
        rel = Path(dirpath).relative_to(ROOT)
        at_root = rel == Path(".")
        # Prune (and order) directories in place so os.walk skips them.
        dirnames[:] = sorted(
            name
            for name in dirnames
            if name not in EXCLUDE_ANYWHERE and not (at_root and name in EXCLUDE_TOP)
        )
        for name in sorted(filenames):
            if name in EXCLUDE_ANYWHERE or name.endswith(EXCLUDE_SUFFIX):
                continue
            if at_root and name in EXCLUDE_TOP:
                continue
            yield rel / name


def report_dirty(packaged):
    """Warn about packaged files git does not have committed.

    The old build.sh could not ship uncommitted work because git archive reads
    the commit. This one reads the working tree, so a release cut from a dirty
    checkout would include whatever happened to be lying around. Not an error —
    that freedom is the reason for the change — but never silent.
    """
    try:
        out = subprocess.run(
            ["git", "-C", str(ROOT), "status", "--porcelain", "--untracked-files=all"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        return  # no git, or not a checkout: nothing to compare against
    packaged = {p.as_posix() for p in packaged}
    dirty = sorted(
        path
        for line in out.splitlines()
        if (path := line[3:].strip().strip('"')) in packaged
    )
    if dirty:
        print(
            f"warning: {len(dirty)} packaged file(s) are not committed:", file=sys.stderr
        )
        for path in dirty[:10]:
            print(f"    {path}", file=sys.stderr)
        if len(dirty) > 10:
            print(f"    ... and {len(dirty) - 10} more", file=sys.stderr)


def build(outdir, channel=None):
    addon_id, version = addon_meta()
    if not addon_id or not version:
        sys.exit("addon.xml is missing an id or version attribute")
    if channel is not None and channel not in CHANNELS:
        sys.exit(f"unknown channel {channel!r}; expected one of {', '.join(CHANNELS)}")

    files = list(iter_files())
    if Path("addon.xml") not in files:
        sys.exit("addon.xml not found in the tree; refusing to build")

    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    suffix = f"-{channel}" if channel else ""
    zip_path = outdir / f"{addon_id}-{version}{suffix}.zip"

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for rel in files:
            arcname = (Path(addon_id) / rel).as_posix()
            archive.write(ROOT / rel, arcname=arcname)

    # Verify the result is a well-formed archive Kodi will accept.
    with zipfile.ZipFile(zip_path) as archive:
        broken = archive.testzip()
        if broken is not None:
            sys.exit(f"built zip is corrupt at {broken}")
        if f"{addon_id}/addon.xml" not in archive.namelist():
            sys.exit(f"built zip lacks {addon_id}/addon.xml")

    report_dirty(files)
    size_kib = zip_path.stat().st_size / 1024
    print(f"{zip_path}  ({len(files)} files, {size_kib:.0f} KiB)")
    return zip_path


def main(argv):
    outdir, channel = None, None
    rest = []
    i = 0
    while i < len(argv):
        if argv[i] == "--channel":
            if i + 1 >= len(argv):
                sys.exit("--channel needs a value")
            channel = argv[i + 1]
            i += 2
            continue
        rest.append(argv[i])
        i += 1
    if len(rest) > 1:
        sys.exit(__doc__.strip())
    if rest:
        outdir = rest[0]
    build(outdir if outdir else ROOT / "dist", channel)


if __name__ == "__main__":
    main(sys.argv[1:])
