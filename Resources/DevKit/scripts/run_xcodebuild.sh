#!/usr/bin/env bash
# Wrapper around xcodebuild that treats the log content as the source of truth,
# not the process exit code.
#
# Why: xcodebuild is known to exit 0 even when compilation fails, when test cases
# fail, or when the log contains "** BUILD FAILED **" / "** TEST FAILED **".
# Relying on exit status alone causes higher-level automation to keep running
# past real failures.
#
# Behavior:
#   1. Isolate build caches under DERIVED_DATA so repeated runs stay hermetic.
#   2. Run `xcodebuild "$@"` and capture the raw log.
#   3. Normalize the captured transcript into a plain-text log.
#   4. Replay the normalized log through xcbeautify when available.
#   5. Scan the log for error markers. If any are found, or the xcodebuild
#      invocation itself exited non-zero, exit with a non-zero status so the
#      task runner halts the chain.
#
# Env:
#   XCBUILD_LABEL  Optional label (e.g. "build-sim") used in failure messages.
#   DERIVED_DATA   Derived data root (default: $PWD/.DerivedData). Passed to
#                  xcodebuild as -derivedDataPath unless the caller provides one.

set -u -o pipefail

LABEL="${XCBUILD_LABEL:-xcodebuild}"
RAW_LOG=$(mktemp -t "modern-uikit-${LABEL//\//_}.raw.XXXXXX.log")
LOG=$(mktemp -t "modern-uikit-${LABEL//\//_}.XXXXXX.log")
trap 'rm -f "$RAW_LOG" "$LOG"' EXIT

DERIVED_DATA="${DERIVED_DATA:-$PWD/.DerivedData}"
BUILD_HOME="${BUILD_HOME:-$DERIVED_DATA/home}"
MODULE_CACHE="${MODULE_CACHE:-$DERIVED_DATA/ModuleCache.noindex}"
XDG_CACHE_HOME="${XDG_CACHE_HOME:-$DERIVED_DATA/xdg-cache}"

mkdir -p "$BUILD_HOME" "$XDG_CACHE_HOME" "$MODULE_CACHE"
export HOME="$BUILD_HOME"
export XDG_CACHE_HOME
export CLANG_MODULE_CACHE_PATH="$MODULE_CACHE"
export SWIFTPM_MODULECACHE_OVERRIDE="$MODULE_CACHE"

ARGS=("$@")
HAS_DERIVED_DATA_ARG=0
for arg in "${ARGS[@]}"; do
    if [ "$arg" = "-derivedDataPath" ]; then
        HAS_DERIVED_DATA_ARG=1
        break
    fi
done
if [ "$HAS_DERIVED_DATA_ARG" -eq 0 ]; then
    ARGS=(-derivedDataPath "$DERIVED_DATA" "${ARGS[@]}")
fi

capture_direct() {
    : >"$RAW_LOG"
    if xcodebuild "$@" >"$RAW_LOG" 2>&1; then
        XC_STATUS=0
    else
        XC_STATUS=$?
    fi
}

normalize_log() {
    perl -ne '
        s/\r/\n/g;
        s/\x08//g;
        s/\x04//g;
        print;
    ' "$RAW_LOG" >"$LOG"
}

capture_direct "${ARGS[@]}"
normalize_log

if command -v xcbeautify >/dev/null 2>&1; then
    xcbeautify --disable-colored-output --disable-logging <"$LOG"
else
    cat "$LOG"
fi

ERR_RE='(^|[[:space:]])error:|^\*\* (BUILD|TEST|ARCHIVE|CLEAN|ANALYZE) FAILED \*\*|^Testing failed:|^Failing tests:'
IGNORED_ERR_RE='connection to service named com\.apple\.linkd\.autoShortcut|\[Connection\] Unable to (get synchronousRemoteObjectProxy|re-register with Process Instance Registry), error:'

FOUND_ERRORS=0
ERROR_LINES=$(grep -En "$ERR_RE" "$LOG" | grep -Ev "$IGNORED_ERR_RE" || true)
if [ -n "$ERROR_LINES" ]; then
    FOUND_ERRORS=1
fi

if [ "$XC_STATUS" -ne 0 ] || [ "$FOUND_ERRORS" -ne 0 ]; then
    echo "" >&2
    echo "❌ [$LABEL] xcodebuild failed (exit=$XC_STATUS, errors_in_log=$FOUND_ERRORS)" >&2
    if [ "$FOUND_ERRORS" -ne 0 ]; then
        echo "---- first 40 error lines from log ----" >&2
        printf "%s\n" "$ERROR_LINES" | head -40 >&2 || true
        echo "---------------------------------------" >&2
    fi
    if [ "$XC_STATUS" -ne 0 ]; then
        exit "$XC_STATUS"
    fi
    exit 1
fi
