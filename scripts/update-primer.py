#!/usr/bin/env python
import argparse
import re

from pathlib import Path

root_dir = Path(__file__).parent.parent.parent
primer_recipe_dir = root_dir / "ice" / "ice" / "recipes" / "primer"
primer_dir = root_dir / "primer"

pattern = re.compile(
    r"""
    (?P<prefix>
        ^\{%\ code\ title="(?P<path> [^"]+)"[^%]*\ %\}\n+
        ```python\n)
    (?P<content> .*?)
    (?P<suffix> ^```\n)
    """,
    re.MULTILINE | re.DOTALL | re.VERBOSE,
)


def update_ice():
    for md_path in primer_dir.glob("**/*.md"):
        for c in pattern.finditer(md_path.read_text()):
            if " " in c["path"]:
                continue
            code_path = primer_recipe_dir / c["path"]
            code_path.parent.mkdir(parents=True, exist_ok=True)
            code_path.write_text(c["content"])


def updated_code_block(c):
    code_path = primer_recipe_dir / c["path"]
    if not code_path.exists():
        return c[0]
    return c["prefix"] + code_path.read_text() + c["suffix"]


def update_primer():
    for md_path in primer_dir.glob("**/*.md"):
        md_path.write_text(pattern.sub(updated_code_block, md_path.read_text()))


def main():
    parser = argparse.ArgumentParser(description="Update Primer code.")
    parser.add_argument(
        "--reverse",
        action="store_true",
        default=False,
        help="update ICE code based on Primer code",
    )
    args = parser.parse_args()
    if args.reverse:
        update_ice()
    else:
        update_primer()


if __name__ == "__main__":
    main()
