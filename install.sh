#!/usr/bin/env bash
# install.sh — one-liner install for news-cli
# Usage: curl -sSL https://raw.githubusercontent.com/kzclaw/news-cli/main/install.sh | bash

set -e

REPO="kzclaw/news-cli"
GH_TOKEN=""

# Accept token as second arg or from env
[[ -n "$2" ]] && GH_TOKEN="$2"
[[ -z "$GH_TOKEN" && -n "$GITHUB_TOKEN" ]] && GH_TOKEN="$GITHUB_TOKEN"

echo "📦 Downloading news-cli v1.0.0 wheel..."
if [[ -n "$GH_TOKEN" ]]; then
    curl -fsSL \
        -H "Authorization: token $GH_TOKEN" \
        -o /tmp/newscli-1.0.0-py3-none-any.whl \
        "https://github.com/$REPO/releases/download/v1.0.0/newscli-1.0.0-py3-none-any.whl"
else
    curl -fsSL \
        -o /tmp/newscli-1.0.0-py3-none-any.whl \
        "https://github.com/$REPO/releases/download/v1.0.0/newscli-1.0.0-py3-none-any.whl"
fi

echo "🔧 Installing..."
python3 -m pip install --user /tmp/newscli-1.0.0-py3-none-any.whl 2>/dev/null || \
python3 -m pip install --user --force-reinstall /tmp/newscli-1.0.0-py3-none-any.whl

rm -f /tmp/newscli-1.0.0-py3-none-any.whl

echo ""
echo "✅ news-cli v1.0.0 installed!"
echo "   Run: newscli get hackernews topstories 5"
echo "   Docs: https://github.com/$REPO#readme"
