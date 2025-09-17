#!/bin/bash

# Terminal formatting functions using ANSI escape sequences
# Usage: echo "$(red "This is red text")"
#        echo "$(green "This is green text")"
#        echo "$(bold "This is bold text")"

# Color functions
red() {
    echo -e "\033[31m$1\033[0m"
}

green() {
    echo -e "\033[32m$1\033[0m"
}

yellow() {
    echo -e "\033[33m$1\033[0m"
}

blue() {
    echo -e "\033[34m$1\033[0m"
}

magenta() {
    echo -e "\033[35m$1\033[0m"
}

cyan() {
    echo -e "\033[36m$1\033[0m"
}

# Style functions
bold() {
    echo -e "\033[1m$1\033[0m"
}

dim() {
    echo -e "\033[2m$1\033[0m"
}

underline() {
    echo -e "\033[4m$1\033[0m"
}

# Combined functions
bold_red() {
    echo -e "\033[1;31m$1\033[0m"
}

bold_green() {
    echo -e "\033[1;32m$1\033[0m"
}

bold_yellow() {
    echo -e "\033[1;33m$1\033[0m"
}

bold_blue() {
    echo -e "\033[1;34m$1\033[0m"
}

# Reset all formatting
reset() {
    echo -e "\033[0m"
}

# Check if terminal supports colors
supports_color() {
    if [[ -t 1 ]] && [[ "${TERM:-}" != "dumb" ]] && command -v tput >/dev/null 2>&1; then
        if tput colors >/dev/null 2>&1; then
            return 0
        fi
    fi
    return 1
}

# Disable colors if terminal doesn't support them
if ! supports_color; then
    red() { echo "$1"; }
    green() { echo "$1"; }
    yellow() { echo "$1"; }
    blue() { echo "$1"; }
    magenta() { echo "$1"; }
    cyan() { echo "$1"; }
    bold() { echo "$1"; }
    dim() { echo "$1"; }
    underline() { echo "$1"; }
    bold_red() { echo "$1"; }
    bold_green() { echo "$1"; }
    bold_yellow() { echo "$1"; }
    bold_blue() { echo "$1"; }
    reset() { echo ""; }
fi
