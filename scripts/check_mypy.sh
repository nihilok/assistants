#!/bin/bash

# MyPy baseline checker script
# Usage:
#   ./check_mypy.sh                    # Check against baseline
#   ./check_mypy.sh --generate         # Generate new baseline

# Source the color formatting functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/format_colors.sh"

BASELINE_FILE="mypy_baseline.txt"
TEMP_FILE="/tmp/current_mypy.txt"
SOURCE_DIR="assistants"

# Function to generate mypy output
generate_mypy_output() {
    local output_file="$1"
    echo "$(dim "Running mypy on ${SOURCE_DIR}/...")"
    uv run mypy "${SOURCE_DIR}/" --show-error-codes 2>&1 | grep -E "(error|note):" | sort > "$output_file" || true
}

# Function to generate baseline
generate_baseline() {
    echo "$(blue "🔄 Generating new mypy baseline...")"
    generate_mypy_output "$BASELINE_FILE"
    echo "$(bold_green "✅ Baseline file updated:") $(cyan "$BASELINE_FILE")"
    echo "$(bold "📊 Total errors captured:") $(yellow "$(wc -l < "$BASELINE_FILE")")"
    echo ""
    echo "$(bold_yellow "💡 Don't forget to commit the updated baseline file!")"
}

# Function to check against baseline
check_baseline() {
    if [ ! -f "$BASELINE_FILE" ]; then
        echo "$(bold_red "❌ Baseline file '$BASELINE_FILE' not found!")"
        echo ""
        echo "$(bold_blue "🚀 To create the baseline, run:")"
        echo "   $(cyan "$0 --generate")"
        exit 1
    fi

    echo "$(blue "🔍 Checking mypy output against baseline...")"
    generate_mypy_output "$TEMP_FILE"

    if ! diff -u "$BASELINE_FILE" "$TEMP_FILE" > /dev/null; then
        echo ""
        echo "$(bold_red "❌ Mypy baseline check failed!")"
        echo "$(yellow "🔍 New or changed type errors detected.")"
        echo ""

        # Show summary counts
        BASELINE_COUNT=$(wc -l < "$BASELINE_FILE" | tr -d ' ')
        CURRENT_COUNT=$(wc -l < "$TEMP_FILE" | tr -d ' ')
        echo "$(bold "📊 Summary:")"
        echo "  $(dim "Baseline errors:") $(green "$BASELINE_COUNT")"
        echo "  $(dim "Current errors:")  $(if [[ $CURRENT_COUNT -gt $BASELINE_COUNT ]]; then red "$CURRENT_COUNT"; else green "$CURRENT_COUNT"; fi)"
        echo ""

        # Parse the diff to show only the changes
        DIFF_OUTPUT=$(diff -u "$BASELINE_FILE" "$TEMP_FILE")

        # Save diff to a temp file for easier processing
        echo "$DIFF_OUTPUT" > /tmp/diff_output.txt

        # Extract removed errors (lines starting with - but not ---)
        grep "^-" /tmp/diff_output.txt | grep -v "^---" > /tmp/removed_errors.txt 2>/dev/null || true

        # Extract added errors (lines starting with + but not +++)
        grep "^+" /tmp/diff_output.txt | grep -v "^+++" > /tmp/added_errors.txt 2>/dev/null || true

        if [[ -s /tmp/removed_errors.txt ]]; then
            echo "$(bold_green "✅ Errors removed:")"
            cat /tmp/removed_errors.txt | sed 's/^-//' | while IFS= read -r line; do
                echo "  $(green "- $line")"
            done
            echo ""
        fi

        if [[ -s /tmp/added_errors.txt ]]; then
            echo "$(bold_red "❌ Errors added:")"
            cat /tmp/added_errors.txt | sed 's/^+//' | while IFS= read -r line; do
                echo "  $(red "+ $line")"
            done
            echo ""
        fi

        # Clean up temp files
        rm -f /tmp/diff_output.txt /tmp/removed_errors.txt /tmp/added_errors.txt

        echo "$(bold "🔧 To fix this, either:")"
        echo "   $(dim "1. Fix the type errors shown above, or")"
        echo "   $(dim "2. Update the baseline by running:") $(cyan "$0 --generate")"
        exit 1
    else
        echo "$(bold_green "✅ Mypy output matches baseline")"
        echo "$(bold "📊 Total errors in baseline:") $(green "$(wc -l < "$BASELINE_FILE")")"
    fi

    # Clean up temp file
    rm -f "$TEMP_FILE"
}

# Main script logic
case "${1:-}" in
    --generate)
        generate_baseline
        ;;
    "")
        check_baseline
        ;;
    *)
        echo "Usage: $0 [--generate]"
        echo ""
        echo "Options:"
        echo "  --generate    Generate a new mypy baseline file"
        echo "  (no args)     Check current mypy output against baseline"
        exit 1
        ;;
esac
