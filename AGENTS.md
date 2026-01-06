# Repository Guidelines

## Purpose
This repository stores personal OpenAI Codex skills. Use it as the source of truth
before installing or packaging skills into your Codex environment.

## Project Structure & Module Organization
- `skills/<skill-name>/`: Individual skill folders.
- `skills/<skill-name>/SKILL.md`: Required metadata + instructions.
- `skills/<skill-name>/scripts/`: Optional helper scripts.
- `skills/<skill-name>/references/`: Optional reference docs.
- `skills/<skill-name>/assets/`: Optional templates or files used in outputs.
- `dist/`: Optional packaged `.skill` bundles.

Example layout:
```
skills/my-skill/
  SKILL.md
  scripts/
  references/
  assets/
```

## Build, Test, and Development Commands
There is no global build system. Use the Codex skill-creator scripts when needed:
- Initialize a skill: `python ~/.codex/skills/.system/skill-creator/scripts/init_skill.py my-skill --path skills`
- Package a skill: `python ~/.codex/skills/.system/skill-creator/scripts/package_skill.py skills/my-skill dist`

## Coding Style & Naming Conventions
- Skill folder names: lowercase, digits, and hyphens only (e.g., `gh-address-comments`).
- `SKILL.md` frontmatter must include only `name` and `description`.
- Keep `SKILL.md` concise; move large details into `references/`.
- Prefer ASCII text and short, imperative instructions.

## Testing Guidelines
- No formal test framework. Manually run scripts in `scripts/` and verify outputs.
- If a script has CLI options, prefer `--help` to confirm usage.

## Commit & Pull Request Guidelines
- No established commit history in this repo yet; use short, imperative messages.
- For PRs, include: the skill name, trigger examples, and any packaging or test steps.

## Agent-Specific Instructions
- Follow the skill-creator workflow: define concrete trigger examples, then add
  reusable scripts, references, or assets.
- Avoid extra documentation files outside `SKILL.md` and `references/`.
