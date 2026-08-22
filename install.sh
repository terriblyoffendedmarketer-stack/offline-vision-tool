#!/bin/bash
# install.sh — Sets up the vision tool: launchd service + Claude MCP registration
# Usage: bash install.sh
#
# What it does:
# 1. Installs the launchd plist so the server auto-starts on login
# 2. Starts the server immediately
# 3. Registers the MCP server with Claude Code

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLIST_SRC="$PROJECT_DIR/com.local.vision-tool.plist"
PLIST_DST="$HOME/Library/LaunchAgents/com.local.vision-tool.plist"
MCP_SERVER="$PROJECT_DIR/mcp_server.py"
PYTHON="$PROJECT_DIR/venv/bin/python"

echo "=== Offline Vision Tool Installer ==="
echo ""

# 1. Install launchd plist
echo "1. Installing launchd service..."
if [ -f "$PLIST_DST" ]; then
    launchctl unload "$PLIST_DST" 2>/dev/null || true
fi
cp "$PLIST_SRC" "$PLIST_DST"
launchctl load "$PLIST_DST"
echo "   Server will auto-start on login at localhost:9090"

# 2. Wait for server to come up
echo "2. Waiting for server..."
for i in $(seq 1 30); do
    if curl -s http://127.0.0.1:9090/health > /dev/null 2>&1; then
        echo "   Server is running!"
        break
    fi
    sleep 1
done

# 3. Register MCP server with Claude Code
echo "3. Registering MCP server with Claude Code..."
claude mcp add vision-tool "$PYTHON" "$MCP_SERVER" 2>/dev/null && echo "   MCP server registered" || echo "   Note: claude CLI not found. Register manually with: claude mcp add vision-tool $PYTHON $MCP_SERVER"

echo ""
echo "=== Installation complete ==="
echo "Server: http://127.0.0.1:9090"
echo "CLI:    python $PROJECT_DIR/cli.py check image.png 'is there an error?'"
echo "MCP:    Claude Code will see vision_check, vision_score, vision_compare, vision_caption tools"
