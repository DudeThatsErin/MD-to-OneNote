#!/usr/bin/env bash
# md-to-onenote - Mac/Linux one-click runner
# Usage:
#   ./run.sh                          (interactive prompts)
#   ./run.sh "/path/to/vault" "Notebook Name"

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check Python is installed (try python3 first, then python)
if command -v python3 &>/dev/null; then
    PYTHON=python3
    PIP=pip3
elif command -v python &>/dev/null; then
    PYTHON=python
    PIP=pip
else
    echo "ERROR: Python is not installed."
    echo "  Mac:   brew install python   (or download from https://www.python.org)"
    echo "  Linux: sudo apt install python3 python3-pip"
    exit 1
fi

# Install dependencies if not already installed
echo "Checking dependencies..."
$PIP install -r "$SCRIPT_DIR/requirements.txt" --quiet

# Prompt for vault path if not provided
if [ -z "$1" ]; then
    read -rp "Enter the full path to your vault/backup folder: " VAULT
else
    VAULT="$1"
fi

# Prompt for notebook name if not provided
if [ -z "$2" ]; then
    read -rp "Enter the OneNote notebook name to import into: " NOTEBOOK
else
    NOTEBOOK="$2"
fi

echo ""
echo "Starting import..."
echo "  Vault:    $VAULT"
echo "  Notebook: $NOTEBOOK"
echo ""

$PYTHON "$SCRIPT_DIR/main.py" import --vault "$VAULT" --notebook "$NOTEBOOK"
