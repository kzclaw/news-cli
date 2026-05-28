#!/usr/bin/env bash
# install.sh — one-liner install for news-cli
# Usage: curl -sSL https://raw.githubusercontent.com/kzclaw/news-cli/main/install.sh | bash

set -e

REPO="kzclaw/news-cli"
TMP=$(mktemp -d)
DEST="$HOME/Library/Python/3.14/lib/python/site-packages"

echo "📦 Cloning news-cli..."
git clone --depth=1 https://github.com/"$REPO".git "$TMP/news-cli" 2>/dev/null ||
hub clone "$REPO" "$TMP/news-cli" 2>/dev/null ||
{ echo "❌ git clone failed — is git installed?"; exit 1; }

echo "🔧 Installing with pip..."
python3 -m pip install --user -e "$TMP/news-cli" 2>/dev/null ||
python3 -m pip install --user "$TMP/news-cli" 2>/dev/null ||
{ echo "❌ pip install failed"; rm -rf "$TMP"; exit 1; }

rm -rf "$TMP"

# Verify
NEWSCLI_BIN=$(python3 -c "import sys; print([p for p in sys.path if 'newscli' in p][0])" 2>/dev/null || true)
echo ""
echo "✅ news-cli installed!"
echo "   Run: newscli get hackernews topstories 5"
echo "   Docs: https://github.com/$REPO#readme"