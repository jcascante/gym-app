---
name: commit
description: Lint, run tests, then create a semantic git commit for staged or unstaged changes
disable-model-invocation: true
allowed-tools: Bash(git *), Bash(uv run ruff*), Bash(uv run pytest*), Bash(npm run lint*)
---

Create a git commit following these steps:

## 1. Check what changed
```
!git diff --stat HEAD
!git status --short
```

## 2. Lint changed files

For any changed Python files in `backend/`:
```bash
cd backend && uv run ruff check --fix app/
```

For any changed TypeScript/TSX files in `frontend/`:
```bash
cd frontend && npm run lint -- --fix 2>/dev/null || true
```

## 3. Run tests relevant to changed files

If backend files changed:
```bash
cd backend && uv run pytest -x -q
```

If frontend files changed and a test script exists, run it. If no frontend tests are configured, skip silently.

Stop and report to the user if any step fails — do not proceed to commit.

## 4. Stage and commit

Stage all tracked modifications (do not add untracked files unless the user explicitly listed them):
```bash
git add -u
```

If the user provided a message via `$ARGUMENTS`, use it as the commit subject. Otherwise, analyze the diff and write a commit message that:
- Uses a semantic prefix: `feat:`, `fix:`, `refactor:`, `test:`, `chore:`, `docs:`
- Subject line ≤ 72 characters, imperative mood ("add X", not "adds X" or "added X")
- No body unless the change is genuinely complex

```bash
git commit -m "<message>"
```

Show the resulting `git log --oneline -1` to confirm.
