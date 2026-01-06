# Codex Skills Repo

This repo stores personal OpenAI Codex skills.

## Structure
- `skills/`: skill folders with `SKILL.md` and optional `scripts/`, `references/`, `assets/`.

## Sync Claude Skills (optional)
Use the sync skill to copy from Claude into Codex:

```bash
python3 ~/.codex/skills/claude-skill-sync/scripts/claude_skill_sync.py --include-official-plugins
```

## Install Into Codex
Copy a skill folder into `~/.codex/skills/` (or package it if needed).
