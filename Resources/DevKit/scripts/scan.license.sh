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
WORKSPACE_PATH="${PROJECT_ROOT}/ModernUIKit.xcworkspace"
LICENSE_OUTPUT="${PROJECT_ROOT}/ModernUIKit/Resources/OpenSourceLicenses.md"

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

RESOLVE_SCHEMES=("ModernUIKit")

for scheme in "${RESOLVE_SCHEMES[@]}"; do
    echo "[*] resolving scheme: $scheme"
    if command -v xcbeautify >/dev/null 2>&1; then
        with_retry xcodebuild -resolvePackageDependencies \
            -clonedSourcePackagesDirPath "$PACKAGE_CLONE_ROOT" \
            -workspace "$WORKSPACE_PATH" \
            -scheme "$scheme" |
            xcbeautify --disable-colored-output --disable-logging
    else
        with_retry xcodebuild -resolvePackageDependencies \
            -clonedSourcePackagesDirPath "$PACKAGE_CLONE_ROOT" \
            -workspace "$WORKSPACE_PATH" \
            -scheme "$scheme"
    fi
done

echo "[*] scanning licenses..."

SCANNER_DIR=(
    "$PROJECT_ROOT/Resources/AdditionalLicenses"
    "$PACKAGE_CLONE_ROOT/checkouts"
    "$PROJECT_ROOT/Vendor"
)

SCANNED_LICENSE_CONTENT="# Open Source License\n\n"

function append_license_file {
    local file=$1
    local package_name
    package_name=$(basename "$(dirname "$file")")
    SCANNED_LICENSE_CONTENT="${SCANNED_LICENSE_CONTENT}\n\n## ${package_name}\n\n$(cat "$file")"
}

for dir in "${SCANNER_DIR[@]}"; do
    if [[ -d "$dir" ]]; then
        while IFS= read -r file; do
            append_license_file "$file"
        done < <(find "$dir" -maxdepth 2 -type f \( -name "LICENSE*" -o -name "COPYING*" \) | sort)
    fi
done

mkdir -p "$(dirname "$LICENSE_OUTPUT")"
echo -e "$SCANNED_LICENSE_CONTENT" >"$LICENSE_OUTPUT"
echo "[*] wrote $LICENSE_OUTPUT"

if command -v prettier >/dev/null 2>&1; then
    prettier --write "$LICENSE_OUTPUT"
elif command -v npx >/dev/null 2>&1; then
    npx --yes prettier --write "$LICENSE_OUTPUT"
fi

echo "[*] done"
