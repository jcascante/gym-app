#!/usr/bin/env bash
# PostToolUse hook: runs ruff on any Python file edited in the backend directory.
# Receives tool info as JSON on stdin.

set -euo pipefail

INPUT=$(cat)

FILE_PATH=$(echo "$INPUT" | python3 -c "
import json, sys
data = json.load(sys.stdin)
inp = data.get('tool_input', {})
# Edit tool uses 'file_path'; Write tool uses 'file_path'
print(inp.get('file_path', ''))
" 2>/dev/null || true)

# Only act on .py files inside the backend or engine directories
if [[ "$FILE_PATH" != *.py ]]; then
  exit 0
fi
if [[ "$FILE_PATH" != */backend/* && "$FILE_PATH" != backend/* && \
      "$FILE_PATH" != */engine/* && "$FILE_PATH" != engine/* ]]; then
  exit 0
fi

echo "[ruff] Checking $FILE_PATH"
if [[ "$FILE_PATH" == */engine/* || "$FILE_PATH" == engine/* ]]; then
  cd engine
else
  cd backend
fi
uv run ruff check --fix "$FILE_PATH" 2>&1 || true
