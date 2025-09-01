#!/usr/bin/env bash
set -euo pipefail

FILE=$1
if [[ ! -f "$FILE" ]]; then
  echo "Usage: $0 issues.json"
  exit 1
fi

jq -c '.[]' "$FILE" | while read -r issue; do
  title=$(echo "$issue" | jq -r '.title')
  body=$(echo "$issue" | jq -r '.body')
  labels=$(echo "$issue" | jq -r '.labels | join(",")')

  echo "Creating issue: $title"
  gh issue create --title "$title" --body "$body" --label "$labels"
done

