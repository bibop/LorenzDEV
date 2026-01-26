#!/bin/bash
# LORENZ Gateway - Setup & Rebrand Script

set -e

echo "🚀 LORENZ Gateway Setup"

GATEWAY_DIR="/Users/bibop/Documents/AI/Lorenz/third_party/clawdbot"
LORENZ_HOME="$HOME/.lorenz"

# 1. Ensure .lorenz directory exists
mkdir -p "$LORENZ_HOME/skills"
mkdir -p "$LORENZ_HOME/credentials"

# 2. Check if lorenz.json exists, if not create a default one
CONFIG_PATH="$LORENZ_HOME/lorenz.json"

if [ ! -f "$CONFIG_PATH" ]; then
    echo "📝 Creating initial lorenz.json..."
    cat > "$CONFIG_PATH" <<EOF
{
  "ui": {
    "assistant": {
      "name": "LORENZ",
      "avatar": "🧠"
    }
  },
  "core": {
    "enabled": true,
    "apiUrl": "http://localhost:8000",
    "apiKey": "LORENZ_DEV_KEY"
  },
  "channels": {
    "telegram": {
      "enabled": false,
      "botToken": "REPLACE_WITH_TELEGRAM_BOT_TOKEN"
    },
    "whatsapp": {
      "enabled": false,
      "accessToken": "REPLACE_WITH_WHATSAPP_ACCESS_TOKEN",
      "phoneNumberId": "REPLACE_WITH_PHONE_NUMBER_ID"
    }
  }
}
EOF
fi

# 3. Clean up any remaining clawdbot references in dependencies (package-lock.json, etc.)
cd "$GATEWAY_DIR"
# Note: we don't want to break 'npm install' if it hasn't been run yet
if [ -f "package.json" ]; then
    sed -i '' 's/clawdbot/lorenz/g' package.json
fi

echo "✅ Rebranding and configuration initialized."
echo "📍 Configuration path: $CONFIG_PATH"
echo "👉 Edit lorenz.json to enable channels."
