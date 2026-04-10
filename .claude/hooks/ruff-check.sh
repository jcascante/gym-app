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

# Only act on .py files inside the backend directory
if [[ "$FILE_PATH" != *.py ]] || [[ "$FILE_PATH" != */backend/* && "$FILE_PATH" != backend/* ]]; then
  exit 0
fi

echo "[ruff] Checking $FILE_PATH"
cd backend
uv run ruff check --fix "$FILE_PATH" 2>&1 || true
