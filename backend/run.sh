#!/bin/bash

# Kino Backend Auto-Restart Script
# This script will automatically restart the backend server if it exits
# Exit codes:
#   0 - Restart requested, will auto-restart
#   1 - Shutdown requested, will stop
#   Other - Crash, will auto-restart after delay
# Press Ctrl+C to stop completely

cd "$(dirname "$0")"

echo "🎬 Kino Backend Auto-Restart Script"
echo "=================================="
echo "Press Ctrl+C to stop the server"
echo ""

# Activate virtual environment
source venv/bin/activate

# Infinite loop for auto-restart
while true; do
    echo "🚀 Starting backend server..."
    python main.py

    EXIT_CODE=$?

    if [ $EXIT_CODE -eq 0 ]; then
        echo "🔄 Server restart requested (code 0) - restarting..."
        sleep 2
    elif [ $EXIT_CODE -eq 1 ]; then
        echo "🛑 Server shutdown requested (code 1) - stopping..."
        break
    elif [ $EXIT_CODE -eq 130 ]; then
        # Ctrl+C was pressed
        echo "⛔ Interrupted by user (Ctrl+C) - stopping..."
        break
    else
        echo "⚠️  Server crashed with code $EXIT_CODE - restarting..."
        sleep 3
    fi

    echo ""
done

echo "👋 Server stopped"

