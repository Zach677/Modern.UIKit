#!/usr/bin/env bash
# Run xcodebuild for the App scheme. Show the output live, and fail when the
# exit code or the log reports an error.
#
# Usage: run_xcodebuild.sh <action> <destination> [extra xcodebuild arguments]
# Env:   CONFIGURATION  Build configuration (default: Debug)

set -euo pipefail

action=$1
destination=$2
shift 2

workspaces=(*.xcworkspace)
if [[ ${#workspaces[@]} -ne 1 || ! -d ${workspaces[0]} ]]; then
    echo "error: expected exactly one .xcworkspace in $PWD" >&2
    exit 1
fi

log=$(mktemp -t xcodebuild)
trap 'rm -f "$log"' EXIT

beautify() {
    if ! command -v xcbeautify >/dev/null; then
        cat
    elif [[ -t 1 ]]; then
        xcbeautify --disable-logging
    else
        xcbeautify --disable-logging --disable-colored-output
    fi
}

set +e
xcodebuild \
    -workspace "${workspaces[0]}" \
    -scheme App \
    -configuration "${CONFIGURATION:-Debug}" \
    -destination "$destination" \
    -derivedDataPath .DerivedData \
    CODE_SIGNING_ALLOWED=NO \
    -skipMacroValidation \
    "$@" \
    "$action" 2>&1 | tee "$log" | beautify
status=${PIPESTATUS[0]}
set -e

# Match only lines that xcodebuild or the compiler emit: diagnostics start with a
# source path (`file:line:col:` or `Package.swift:PACKAGE-TARGET:name:`) or
# "error:", and summaries start with "**". The test host process also writes to
# this log, and its system logs can contain "error:" mid-line.
error_pattern='^(/[^:]+(:[^: ]+)*: |xcodebuild: )?error:|^\*\* (BUILD|TEST|ARCHIVE|CLEAN|ANALYZE) FAILED \*\*|^Testing failed:|^Failing tests:'
errors=$(grep -E "$error_pattern" "$log" || true)

if [[ $status -ne 0 || -n $errors ]]; then
    echo "" >&2
    echo "error: xcodebuild $action failed (exit $status)" >&2
    [[ -n $errors ]] && head -40 <<<"$errors" >&2
    exit $((status == 0 ? 1 : status))
fi
