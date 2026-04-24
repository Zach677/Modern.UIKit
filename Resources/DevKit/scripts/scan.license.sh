#!/bin/zsh

cd "$(dirname "$0")"

while [[ ! -d .git ]] && [[ "$(pwd)" != "/" ]]; do
    cd ..
done

if [[ -d .git ]] && [[ -d ModernUIKit.xcworkspace ]]; then
    echo "[*] found project root: $(pwd)"
else
    echo "[!] could not find project root"
    exit 1
fi

PROJECT_ROOT=$(pwd)
PACKAGE_CLONE_ROOT="${PROJECT_ROOT}/.build/license.scanner/dependencies"

function with_retry {
    local retries=3
    local count=0
    while [[ $count -lt $retries ]]; do
        "$@"
        if [[ $? -eq 0 ]]; then
            return 0
        fi
        count=$((count + 1))
    done
    return 1
}

if [[ -n $(git status --porcelain) ]]; then
    if [[ "${ALLOW_DIRTY:-0}" == "1" ]]; then
        echo "[*] git is not clean; continuing because ALLOW_DIRTY=1"
    else
        echo "[!] git is not clean"
        exit 1
    fi
fi

echo "[*] resolving packages..."

rm -rf "$PACKAGE_CLONE_ROOT"
mkdir -p "$PACKAGE_CLONE_ROOT"

RESOLVE_SCHEMES=("ModernUIKit")

for scheme in "${RESOLVE_SCHEMES[@]}"; do
    echo "[*] resolving scheme: $scheme"
    with_retry xcodebuild -resolvePackageDependencies \
        -clonedSourcePackagesDirPath "$PACKAGE_CLONE_ROOT" \
        -workspace *.xcworkspace \
        -scheme "$scheme" |
        xcbeautify --disable-colored-output --disable-logging
done

echo "[*] scanning licenses..."

SCANNER_DIR=(
    "$PROJECT_ROOT/Resources/AdditionalLicenses"
    "$PACKAGE_CLONE_ROOT/checkouts"
    "$PROJECT_ROOT/Vendor"
)

declare -A MANUAL_LICENSE_OVERRIDES

# Build package name mapping from Package.resolved
declare -A PACKAGE_NAME_MAP
PACKAGE_RESOLVED="${PROJECT_ROOT}/ModernUIKit.xcworkspace/xcshareddata/swiftpm/Package.resolved"

# Manual corrections for packages where GitHub URL does not match desired display name
declare -A MANUAL_CORRECTIONS=()

if [[ -f "$PACKAGE_RESOLVED" ]]; then
    echo "[*] reading package names from Package.resolved..."
    while IFS=$'\t' read -r identity repo_name; do
        if [[ -z "$identity" ]]; then
            continue
        fi

        if [[ -n "${MANUAL_CORRECTIONS[$identity]}" ]]; then
            PACKAGE_NAME_MAP[$identity]="${MANUAL_CORRECTIONS[$identity]}"
        elif [[ -n "$repo_name" ]]; then
            PACKAGE_NAME_MAP[$identity]="$repo_name"
        fi
    done < <(python3 - "$PACKAGE_RESOLVED" <<'PY'
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
pins = data.get("pins") or data.get("object", {}).get("pins") or []

for pin in pins:
    identity = str(pin.get("identity") or "").lower()
    location = str(pin.get("location") or "")
    repo_name = Path(urlparse(location).path or location).name
    if repo_name.endswith(".git"):
        repo_name = repo_name[:-4]

    if identity:
        print(f"{identity}\t{repo_name}")
PY
    )
fi

function get_correct_package_name {
    local dir_name=$1
    local lowercase_name=$(echo "$dir_name" | tr '[:upper:]' '[:lower:]')

    if [[ -n "${PACKAGE_NAME_MAP[$lowercase_name]}" ]]; then
        echo "${PACKAGE_NAME_MAP[$lowercase_name]}"
    else
        echo "$dir_name"
    fi
}

function should_skip_license_package {
    local package_name=$1

    case "$package_name" in
    LookInside|LookInsideServer|LookinServer|LookinServerDynamic|LookinServerInjected)
        return 0
        ;;
    *)
        return 1
        ;;
    esac
}

function append_license_file {
    local file=$1
    local package_name
    package_name=$(get_correct_package_name "$(basename "$(dirname "$file")")")

    # Skip optional debug inspection tooling so local setups do not pollute app notices.
    if should_skip_license_package "$package_name"; then
        return
    fi

    if [[ "$2" == "manual" ]]; then
        MANUAL_LICENSE_OVERRIDES[$package_name]=1
    elif [[ -n "${MANUAL_LICENSE_OVERRIDES[$package_name]}" ]]; then
        echo "[*] skipping bundled license for $package_name because an AdditionalLicenses override exists"
        return
    fi

    SCANNED_LICENSE_CONTENT="${SCANNED_LICENSE_CONTENT}\n\n## ${package_name}\n\n$(cat "$file")"
}

SCANNED_LICENSE_CONTENT="# Open Source License\n\n"

for dir in "${SCANNER_DIR[@]}"; do
    if [[ -d "$dir" ]]; then
        source_kind="scanned"
        if [[ "$dir" == "$PROJECT_ROOT/Resources/AdditionalLicenses" ]]; then
            source_kind="manual"
        fi

        while IFS= read -r file; do
            append_license_file "$file" "$source_kind"
        done < <(find "$dir" -maxdepth 2 -type f \( -name "LICENSE*" -o -name "COPYING*" \) | sort)
    fi
done

if [[ ${#MANUAL_LICENSE_OVERRIDES[@]} -gt 0 ]]; then
    echo "[*] loaded manual license overrides for:"
    for package_name in ${(ok)MANUAL_LICENSE_OVERRIDES}; do
        echo "    - $package_name"
    done
fi

LICENSE_OUTPUTS=(
    "$PROJECT_ROOT/ModernUIKit/Resources/OpenSourceLicenses.md"
)

for output_path in "${LICENSE_OUTPUTS[@]}"; do
    mkdir -p "$(dirname "$output_path")"
    echo -e "$SCANNED_LICENSE_CONTENT" >"$output_path"
    echo "[*] wrote $output_path"
done

echo "[*] checking for incompatible licenses..."

INCOMPATIBLE_LICENSES_KEYWORDS=(
    "GNU General Public License"
    "GNU Lesser General Public License"
    "GNU Affero General Public License"
)

for output_path in "${LICENSE_OUTPUTS[@]}"; do
    for keyword in "${INCOMPATIBLE_LICENSES_KEYWORDS[@]}"; do
        if grep -q "$keyword" "$output_path"; then
            echo "[!] found incompatible license: $keyword in $output_path"
            exit 1
        fi
    done
done

echo "[*] formatting license files with prettier..."
npx --yes prettier --write "${LICENSE_OUTPUTS[@]}"

echo "[*] done"
