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
#   1. Run `xcodebuild "$@"` directly and capture the raw log.
#   2. Normalize the captured transcript into a plain-text log.
#   3. Replay the normalized log through xcbeautify when available.
#   4. Scan the log for error markers. If any are found, or the xcodebuild
#      invocation itself exited non-zero, exit with a non-zero status so the
#      task runner halts the chain.
#
# Env:
#   XCBUILD_LABEL  Optional label (e.g. "build-sim") used in failure messages.

set -u -o pipefail

LABEL="${XCBUILD_LABEL:-xcodebuild}"
RAW_LOG=$(mktemp -t "modern-uikit-${LABEL//\//_}.raw.XXXXXX.log")
LOG=$(mktemp -t "modern-uikit-${LABEL//\//_}.XXXXXX.log")
trap 'rm -f "$RAW_LOG" "$LOG"' EXIT

ARGS=("$@")
WORKSPACE_PATH=""
PROJECT_PATH=""

select_xcode_container() {
    local filtered=()
    local i=0

    while [ $i -lt ${#ARGS[@]} ]; do
        case "${ARGS[$i]}" in
            -workspace)
                if [ $((i + 1)) -lt ${#ARGS[@]} ]; then
                    WORKSPACE_PATH="${ARGS[$((i + 1))]}"
                fi
                i=$((i + 2))
                ;;
            -project)
                if [ $((i + 1)) -lt ${#ARGS[@]} ]; then
                    PROJECT_PATH="${ARGS[$((i + 1))]}"
                fi
                i=$((i + 2))
                ;;
            *)
                filtered+=("${ARGS[$i]}")
                i=$((i + 1))
                ;;
        esac
    done

    if [ -n "$WORKSPACE_PATH" ] && [ -d "$WORKSPACE_PATH" ] && [ -f "$WORKSPACE_PATH/contents.xcworkspacedata" ]; then
        ARGS=(-workspace "$WORKSPACE_PATH" "${filtered[@]}")
        return
    fi

    if [ -n "$PROJECT_PATH" ]; then
        ARGS=(-project "$PROJECT_PATH" "${filtered[@]}")
        return
    fi

    ARGS=("${filtered[@]}")
}

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

select_xcode_container
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
