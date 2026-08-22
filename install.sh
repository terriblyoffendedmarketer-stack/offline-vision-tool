#!/bin/bash
# install.sh — Sets up the vision tool: venv, models, launchd service, Claude MCP
# Usage: bash install.sh
#
# What it does:
# 1. Creates a Python venv if missing and installs dependencies
# 2. Pre-downloads ML models so first queries aren't slow
# 3. Generates and installs a launchd plist (paths resolved at install time)
# 4. Starts the server immediately
# 5. Registers the MCP server with Claude Code (if CLI is installed)
#
# Gotchas:
# - Requires Python 3.10+ (tested on 3.11, 3.12, 3.14)
# - macOS only (launchd). Linux users: use systemd or run server.py manually.
# - First model download needs ~1GB of bandwidth.

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$PROJECT_DIR/venv"
PYTHON_BIN="$VENV_DIR/bin/python"
PLIST_DST="$HOME/Library/LaunchAgents/com.local.vision-tool.plist"
MCP_SERVER="$PROJECT_DIR/mcp_server.py"

echo "=== Offline Vision Tool Installer ==="
echo "Project: $PROJECT_DIR"
echo ""

# 0. Check Python version
PYTHON3=$(command -v python3 || true)
if [ -z "$PYTHON3" ]; then
    echo "Error: python3 not found. Install Python 3.10+ first."
    exit 1
fi

PY_VERSION=$($PYTHON3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MAJOR=$($PYTHON3 -c "import sys; print(sys.version_info.major)")
PY_MINOR=$($PYTHON3 -c "import sys; print(sys.version_info.minor)")

if [ "$PY_MAJOR" -lt 3 ] || [ "$PY_MINOR" -lt 10 ]; then
    echo "Error: Python 3.10+ required, found $PY_VERSION"
    exit 1
fi
echo "Python: $PY_VERSION ✓"

# 1. Create venv and install dependencies
if [ ! -f "$PYTHON_BIN" ]; then
    echo ""
    echo "1. Creating virtual environment..."
    $PYTHON3 -m venv "$VENV_DIR"
    echo "   Installing dependencies (this takes a few minutes)..."
    "$PYTHON_BIN" -m pip install --upgrade pip -q
    "$PYTHON_BIN" -m pip install -r "$PROJECT_DIR/requirements.txt" -q
    echo "   Dependencies installed ✓"
else
    echo "1. Virtual environment exists ✓"
fi

# 2. Pre-download models
echo ""
echo "2. Pre-downloading ML models (first time only, ~1GB)..."
"$PYTHON_BIN" "$PROJECT_DIR/setup_models.py"

# 3. Generate and install launchd plist
echo ""
echo "3. Installing launchd service..."
if [ -f "$PLIST_DST" ]; then
    launchctl unload "$PLIST_DST" 2>/dev/null || true
fi

cat > "$PLIST_DST" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.local.vision-tool</string>
    <key>ProgramArguments</key>
    <array>
        <string>${PYTHON_BIN}</string>
        <string>${PROJECT_DIR}/server.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>${PROJECT_DIR}</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/vision-tool.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/vision-tool.err</string>
</dict>
</plist>
PLIST

launchctl load "$PLIST_DST"
echo "   Server will auto-start on login at localhost:9090"

# 4. Wait for server
echo ""
echo "4. Waiting for server..."
for i in $(seq 1 30); do
    if curl -s http://127.0.0.1:9090/health > /dev/null 2>&1; then
        echo "   Server is running! ✓"
        break
    fi
    if [ "$i" -eq 30 ]; then
        echo "   Warning: Server didn't start within 30s. Check /tmp/vision-tool.err"
    fi
    sleep 1
done

# 5. Register MCP server with Claude Code
echo ""
echo "5. Registering MCP server with Claude Code..."
if command -v claude > /dev/null 2>&1; then
    claude mcp add --scope user vision-tool "$PYTHON_BIN" "$MCP_SERVER" 2>/dev/null \
        && echo "   MCP server registered globally ✓" \
        || echo "   MCP registration failed — register manually (see below)"
else
    echo "   Claude CLI not found. To register manually, run:"
    echo "   claude mcp add --scope user vision-tool \"$PYTHON_BIN\" \"$MCP_SERVER\""
fi

echo ""
echo "=== Installation complete ==="
echo ""
echo "Server:  http://127.0.0.1:9090"
echo "CLI:     $PYTHON_BIN $PROJECT_DIR/cli.py check image.png 'is there an error?'"
echo "MCP:     Claude Code will see vision_check, vision_score, vision_compare, vision_caption"
echo ""
echo "To uninstall:"
echo "  launchctl unload ~/Library/LaunchAgents/com.local.vision-tool.plist"
echo "  rm ~/Library/LaunchAgents/com.local.vision-tool.plist"
echo "  claude mcp remove vision-tool"
