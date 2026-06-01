#!/usr/bin/env bash
# install.sh — one-liner install for news-cli
# Usage: curl -sSL https://raw.githubusercontent.com/kzclaw/news-cli/main/install.sh | bash

set -e

REPO="kzclaw/news-cli"
GH_TOKEN=""

# Accept token as second arg or from env (only needed for GitHub wheel)
[[ -n "$2" ]] && GH_TOKEN="$2"
[[ -z "$GH_TOKEN" && -n "$GITHUB_TOKEN" ]] && GH_TOKEN="$GITHUB_TOKEN"

# Prefer PyPI (production). Fall back to TestPyPI / GitHub release if needed.
VERSION="${VERSION:-1.1.0}"

echo "📦 Installing news-cli v${VERSION} from PyPI..."
if python3 -m pip install --user "newscli-tool==${VERSION}" 2>/dev/null; then
    echo "✅ news-cli v${VERSION} installed via PyPI"
else
    # Fallback: download wheel from GitHub release (requires GH_TOKEN for private)
    echo "⚠️  PyPI install failed, falling back to GitHub release v${VERSION}..."
    WHEEL="newscli_tool-${VERSION}-py3-none-any.whl"
    if [[ -n "$GH_TOKEN" ]]; then
        curl -fsSL \
            -H "Authorization: token $GH_TOKEN" \
            -o "/tmp/${WHEEL}" \
            "https://github.com/${REPO}/releases/download/v${VERSION}/${WHEEL}"
    else
        curl -fsSL \
            -o "/tmp/${WHEEL}" \
            "https://github.com/${REPO}/releases/download/v${VERSION}/${WHEEL}" 2>/dev/null || \
            curl -fsSL \
                -o "/tmp/${WHEEL}" \
                "https://github.com/${REPO}/releases/download/v${VERSION}/${WHEEL//_/-}"
    fi
    python3 -m pip install --user --force-reinstall "/tmp/${WHEEL}"
    rm -f "/tmp/${WHEEL}"
    echo "✅ news-cli v${VERSION} installed via GitHub release"
fi

echo ""
echo "   Run: newscli get hackernews topstories 5"
echo "   Docs: https://github.com/${REPO}#readme"
