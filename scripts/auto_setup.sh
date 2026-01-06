#!/bin/bash
#
# Auto Setup Script for Devin Sessions
#
# This script is designed to be called from ~/.bashrc to automatically
# run the first-run setup on new Devin sessions. It exits quickly if
# setup has already been completed.
#
# Usage (add to ~/.bashrc):
#   if [ -f ~/repos/DEV-OD-Computer/scripts/auto_setup.sh ]; then
#       ~/repos/DEV-OD-Computer/scripts/auto_setup.sh
#   fi
#

# Configuration
SENTINEL_DIR="$HOME/.config/dev-od-computer"
SENTINEL_FILE="$SENTINEL_DIR/setup_complete"
CREDENTIALS_FILE="$HOME/.config/gcloud/digital-workshop-hub-credentials.json"
FIREBASE_PROJECT_DIR="$HOME/repos/digital-workshop-hub"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Prevent running multiple times in the same shell session
if [ -n "$DEV_OD_AUTOSETUP_RAN" ]; then
    exit 0
fi
export DEV_OD_AUTOSETUP_RAN=1

# Quick check: if sentinel exists and credentials file exists, skip setup
if [ -f "$SENTINEL_FILE" ] && [ -f "$CREDENTIALS_FILE" ]; then
    # Verify the credentials file has correct permissions
    if [ "$(stat -c %a "$CREDENTIALS_FILE" 2>/dev/null)" = "600" ]; then
        # Setup already complete, exit silently
        exit 0
    fi
fi

# Check if we have the required secret
if [ -z "$GOOGLE_SERVICE_ACCOUNT_JSON" ] && [ -z "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    # No credentials available, can't run setup
    # Exit silently to avoid noise on every shell
    exit 0
fi

# Run the first-run setup
echo ""
echo "=========================================="
echo "DEV-OD-Computer: Running first-time setup"
echo "=========================================="
echo ""

python3 "$SCRIPT_DIR/first_run_setup.py"
SETUP_EXIT_CODE=$?

if [ $SETUP_EXIT_CODE -eq 0 ]; then
    echo ""
    echo "Setup complete! Firebase project ready at: $FIREBASE_PROJECT_DIR"
    echo ""
fi

exit $SETUP_EXIT_CODE
