#!/usr/bin/env bash
# =============================================================================
# create_from_file.sh - Bulk Create GitHub Issues from JSON
# =============================================================================
# Usage: ./create_from_file.sh issues.json
#
# Creates multiple GitHub issues from a JSON file.
# Requires: gh CLI (GitHub CLI) authenticated
#
# JSON format:
# [
#   {
#     "title": "Issue title",
#     "body": "Issue description",
#     "labels": ["bug", "priority:high"]
#   }
# ]
# =============================================================================
set -euo pipefail

FILE=${1:-}
if [[ -z "$FILE" || ! -f "$FILE" ]]; then
    echo "Usage: $0 issues.json"
    echo ""
    echo "Create issues from a JSON file containing an array of issue objects."
    exit 1
fi

echo "==> Creating issues from $FILE..."

jq -c '.[]' "$FILE" | while read -r issue; do
    title=$(echo "$issue" | jq -r '.title')
    body=$(echo "$issue" | jq -r '.body')
    labels=$(echo "$issue" | jq -r '.labels | join(",")')
    
    echo "  Creating: $title"
    gh issue create --title "$title" --body "$body" --label "$labels"
done

echo "==> Done!"
