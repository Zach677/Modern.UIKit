#!/usr/bin/env python3
"""Validate Localizable.xcstrings files for release readiness.

Checks per catalog:
  1. Entry hygiene: no stale entries, no empty values, source values mirror keys.
  2. Locale coverage: every key covers the locales already used by the catalog
     plus any locale passed via --require-locale.
  3. Source cross-reference: every catalog key is referenced from the owning
     target's Swift sources, and every `String(localized:)` /
     `NSLocalizedString` key in those sources exists in the catalog.

The owning target of `<Target>/Resources/Localizable.xcstrings` is `<Target>/`.
Keys built from variables at runtime are invisible to the cross-reference; if
one ever appears, register it with an explicit literal alongside the dynamic
call site.
"""

from __future__ import annotations

import argparse
import json
import re
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

LOCALIZED_KEY_RE = re.compile(
    r'(?:String\(\s*localized:|NSLocalizedString\()\s*"((?:[^"\\]|\\.)*)"'
)

SWIFT_ESCAPES = {
    "n": "\n",
    "t": "\t",
    "r": "\r",
    "0": "\0",
    '"': '"',
    "'": "'",
    "\\": "\\",
}


def iter_xcstrings(root: Path):
    for path in root.rglob("Localizable.xcstrings"):
        if any(part in EXCLUDE_DIR_NAMES for part in path.parts):
            continue
        yield path


def unescape_swift_literal(literal: str) -> str:
    result: list[str] = []
    i = 0
    while i < len(literal):
        ch = literal[i]
        if ch == "\\" and i + 1 < len(literal):
            replacement = SWIFT_ESCAPES.get(literal[i + 1])
            if replacement is not None:
                result.append(replacement)
                i += 2
                continue
        result.append(ch)
        i += 1
    return "".join(result)


def target_scope(catalog_path: Path, root: Path) -> Path:
    if catalog_path.parent.name == "Resources" and catalog_path.parent.parent != root:
        return catalog_path.parent.parent
    return root


def referenced_keys(scope: Path) -> set[str]:
    keys: set[str] = set()
    for swift_file in scope.rglob("*.swift"):
        if any(part in EXCLUDE_DIR_NAMES for part in swift_file.parts):
            continue
        text = swift_file.read_text(encoding="utf-8")
        for match in LOCALIZED_KEY_RE.finditer(text):
            keys.add(unescape_swift_literal(match.group(1)))
    return keys


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


def validate_file(path: Path, root: Path, extra_locales: set[str]) -> list[str]:
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
    required_locales.update(extra_locales)

    errors: list[str] = []
    for key, entry in strings.items():
        for err in validate_entry(key, entry, source_lang, required_locales):
            errors.append(f"{path}: {err}")

    scope = target_scope(path, root)
    source_keys = referenced_keys(scope)
    catalog_keys = set(strings.keys())

    for key in sorted(catalog_keys - source_keys):
        errors.append(
            f"{path}: {key!r}: orphaned key (no String(localized:) or "
            f"NSLocalizedString reference under {scope})"
        )
    for key in sorted(source_keys - catalog_keys):
        errors.append(
            f"{path}: {key!r}: referenced under {scope} but missing from the catalog"
        )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".", help="repository root")
    parser.add_argument(
        "--require-locale",
        action="append",
        default=[],
        metavar="LOCALE",
        help="locale every key must cover, in addition to locales already "
        "used by the catalog (repeatable)",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.exists():
        print(f"[!] path does not exist: {root}", file=sys.stderr)
        return 1

    files = list(iter_xcstrings(root))
    if not files:
        print(f"[!] no Localizable.xcstrings found under {root}")
        return 0

    extra_locales = set(args.require_locale)
    all_errors: list[str] = []
    for path in files:
        file_errors = validate_file(path, root, extra_locales)
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
