#!/usr/bin/env python3
"""Validate Localizable.xcstrings files for release readiness."""

from __future__ import annotations

import json
import sys
from pathlib import Path

EXCLUDE_DIR_NAMES = {
    "Vendor",
    "build",
    ".build",
    "DerivedData",
    "Pods",
    "Carthage",
    ".git",
}

DEFAULT_SOURCE_LANGUAGE = "en"


def iter_xcstrings(root: Path):
    for path in root.rglob("Localizable.xcstrings"):
        if any(part in EXCLUDE_DIR_NAMES for part in path.parts):
            continue
        yield path


def discover_locales(strings: dict) -> set[str]:
    locales: set[str] = set()
    for entry in strings.values():
        if not isinstance(entry, dict):
            continue
        localizations = entry.get("localizations")
        if isinstance(localizations, dict):
            locales.update(localizations.keys())
    return locales


def validate_entry(
    key: str, entry: dict, source_lang: str, required_locales: set[str]
) -> list[str]:
    errors: list[str] = []

    if not isinstance(entry, dict):
        errors.append(f"{key!r}: entry is not an object")
        return errors

    if entry.get("extractionState") == "stale":
        errors.append(f"{key!r}: stale entry present (run `mise strip-xcstrings`)")

    localizations = entry.get("localizations")
    if not isinstance(localizations, dict) or not localizations:
        errors.append(f"{key!r}: missing localizations block")
        return errors

    for locale in sorted(required_locales):
        loc = localizations.get(locale)
        if not isinstance(loc, dict):
            errors.append(f"{key!r}: missing {locale} localization")
            continue

        string_unit = loc.get("stringUnit")
        if not isinstance(string_unit, dict):
            errors.append(f"{key!r}: {locale} has no stringUnit")
            continue

        value = string_unit.get("value")
        state = string_unit.get("state")

        if not isinstance(value, str) or not value:
            errors.append(f"{key!r}: {locale} value is empty")
        elif locale == source_lang and value != key:
            errors.append(
                f"{key!r}: {locale} value does not mirror the key "
                f"(got {value!r}; run `mise strip-xcstrings`)"
            )

        if state != "translated":
            errors.append(
                f"{key!r}: {locale} state is {state!r}, expected 'translated'"
            )

    return errors


def validate_file(path: Path) -> list[str]:
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"{path}: invalid JSON ({exc})"]

    strings = doc.get("strings")
    if not isinstance(strings, dict):
        return [f"{path}: missing or malformed `strings` object"]

    source_lang = doc.get("sourceLanguage") or DEFAULT_SOURCE_LANGUAGE
    required_locales = discover_locales(strings)
    required_locales.add(source_lang)

    errors: list[str] = []
    for key, entry in strings.items():
        for err in validate_entry(key, entry, source_lang, required_locales):
            errors.append(f"{path}: {err}")
    return errors


def main() -> int:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()
    if not root.exists():
        print(f"[!] path does not exist: {root}", file=sys.stderr)
        return 1

    files = list(iter_xcstrings(root))
    if not files:
        print(f"[!] no Localizable.xcstrings found under {root}")
        return 0

    all_errors: list[str] = []
    for path in files:
        file_errors = validate_file(path)
        if file_errors:
            all_errors.extend(file_errors)
            print(f"[fail] {path} ({len(file_errors)} issue(s))")
        else:
            print(f"[ok]   {path}")

    if all_errors:
        print(f"\n[!] {len(all_errors)} validation issue(s):", file=sys.stderr)
        for err in all_errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print("[*] all xcstrings validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
