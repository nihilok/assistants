#!/bin/bash

# MyPy baseline checker script
# Usage:
#   ./check_mypy.sh                    # Check against baseline
#   ./check_mypy.sh --generate         # Generate new baseline

set -e

BASELINE_FILE="mypy_baseline.txt"
TEMP_FILE="/tmp/current_mypy.txt"
SOURCE_DIR="assistants"

# Function to generate mypy output
generate_mypy_output() {
    local output_file="$1"
    echo "Running mypy on ${SOURCE_DIR}/..."
    mypy "${SOURCE_DIR}/" --show-error-codes 2>&1 | grep -E "(error|note)" | sort > "$output_file" || true
}

# Function to generate baseline
generate_baseline() {
    echo "🔄 Generating new mypy baseline..."
    generate_mypy_output "$BASELINE_FILE"
    echo "✅ Baseline file updated: $BASELINE_FILE"
    echo "📊 Total errors captured: $(wc -l < "$BASELINE_FILE")"
    echo ""
    echo "💡 Don't forget to commit the updated baseline file!"
}

# Function to check against baseline
check_baseline() {
    if [ ! -f "$BASELINE_FILE" ]; then
        echo "❌ Baseline file '$BASELINE_FILE' not found!"
        echo ""
        echo "🚀 To create the baseline, run:"
        echo "   $0 --generate"
        exit 1
    fi

    echo "🔍 Checking mypy output against baseline..."
    generate_mypy_output "$TEMP_FILE"

    if ! diff -u "$BASELINE_FILE" "$TEMP_FILE"; then
        echo ""
        echo "❌ Mypy baseline check failed!"
        echo "🔍 New or changed type errors detected."
        echo ""
        echo "🔧 To fix this, either:"
        echo "   1. Fix the type errors shown above, or"
        echo "   2. Update the baseline by running: $0 --generate"
        exit 1
    else
        echo "✅ Mypy output matches baseline"
        echo "📊 Total errors in baseline: $(wc -l < "$BASELINE_FILE")"
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
