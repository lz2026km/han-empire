---
allowed-tools: Bash(git:*), Bash(gh pr create:*)
description: Commit and push changes, then create a pull request
---

## Context
- Current git status: !`git status`
- Current git diff (staged and unstaged): !`git diff HEAD`
- Current branch: !`git branch --show-current`
- Repository: https://github.com/lz2026km/han-empire

## Your Task

Based on the changes above:
1. Create a new branch from master if currently on main/master
2. Create a single commit with an appropriate message following the format:
   - `fix: 简短描述` for bug fixes
   - `feat: 简短描述` for new features
   - `ui: 简短描述` for UI changes
   - `refactor: 简短描述` for refactoring
3. Push the branch to origin
4. Create a pull request using `gh pr create`
5. You MUST do all of the above in a single message. Do not use any other tools.