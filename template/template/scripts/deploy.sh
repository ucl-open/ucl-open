#!/usr/bin/env bash
set -euo pipefail

if ! command -v pwsh > /dev/null; then
    echo "The 'pwsh' command was not found. Install PowerShell: https://learn.microsoft.com/powershell/scripting/install/installing-powershell" >&2
    exit 1
fi

pwsh -NoProfile -ExecutionPolicy Bypass -File "$(dirname "$0")/deploy.ps1"
