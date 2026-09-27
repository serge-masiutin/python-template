#!/usr/bin/env python3
"""Validate immutable originals, lossless file mapping and Python example syntax."""

import ast
import hashlib
import json
import re
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
lock = json.loads((ROOT / "config/skills-lock.json").read_text())
examples = 0
for skill in lock["skills"]:
    if skill["mode"] == "upstream":
        continue
    with tarfile.open(ROOT / skill["archive"], "r:gz") as archive:
        original = {}
        for member in archive:
            if not member.isfile():
                continue
            if member.name in original:
                raise ValueError(f"Duplicate archive member: {member.name}")
            original[member.name] = archive.extractfile(member).read()
    hashes = {name: hashlib.sha256(content).hexdigest() for name, content in original.items()}
    if hashes != skill["sourceFiles"]:
        raise ValueError(f"Original source drift: {skill['name']}")
    if skill["mode"] != "adapted":
        continue
    mapping = skill["mapping"]
    if set(mapping) != set(original) or any(value is None for value in mapping.values()):
        raise ValueError(f"Incomplete original-file coverage: {skill['name']}")
    if len(set(mapping.values())) != len(mapping):
        raise ValueError(f"Multiple originals overwrite one target: {skill['name']}")
    directory = ROOT / ".agents/skills" / skill["name"]
    for filename in directory.rglob("*.md"):
        text = filename.read_text()
        if re.search(r"(?:```|` ` `)(?:ruby|erb)\b", text):
            raise ValueError(f"Unadapted executable fence: {filename.relative_to(ROOT)}")
        for match in re.finditer(r"(?:```|` ` `)python\n(.*?)\n\s*(?:```|` ` `)", text, re.S):
            ast.parse(match[1], filename=str(filename.relative_to(ROOT)))
            examples += 1
print(f"Verified immutable sources, complete mappings and syntax of {examples} Python snippets.")
