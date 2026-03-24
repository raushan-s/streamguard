# StreamGuard Git Workflow & Security Guide

This document outlines the Git workflow and security practices for the StreamGuard project.

## Table of Contents

1. [Current Security Status](#current-security-status)
2. [Pre-Commit Checklist](#pre-commit-checklist)
3. [Branch Strategy](#branch-strategy)
4. [Commit Message Guidelines](#commit-message-guidelines)
5. [Pre-Push Verification](#pre-push-verification)
6. [Security Best Practices](#security-best-practices)
7. [Pre-Commit Hooks](#pre-commit-hooks)
8. [Regular Security Audits](#regular-security-audits)
9. [Environment Setup](#environment-setup)
10. [Optional: Pre-Commit Framework](#optional-pre-commit-framework)

---

## Current Security Status

✅ **Currently Secure:**
- `.env` file is NOT tracked (contains actual API keys)
- `.env.example` IS tracked (contains placeholders)
- `.gitignore` is comprehensive and well-structured
- Repository has clean structure with `tests/`, `examples/`, and `layers/` folders
- Pre-commit hook is installed and active

**Repository:** https://github.com/raushan-s/streamguard

---

## Pre-Commit Checklist

Run this checklist before every commit:

```bash
# 1. Check what files will be committed
git status

# 2. Review the actual changes
git diff

# 3. For staged changes
git diff --staged

# 4. Verify .env is NOT in the list
git ls-files | grep "^\.env$"  # Should return nothing

# 5. Check for potential secrets in staged files
git diff --staged | grep -i "password\|secret\|api_key\|token"

# 6. Run tests (optional but recommended)
python tests/run_all_tests.py
```

**If any secrets are found:**
- Remove them from the file
- Update `.gitignore` if needed
- Commit the fix before pushing

---

## Branch Strategy

### Branch Types

- **`main`** - Production-ready code (always deployable)
- **`feature/*`** - New features (e.g., `feature/add-rate-limiting`)
- **`bugfix/*`** - Bug fixes (e.g., `bugfix/fix-pii-detection`)
- **`hotfix/*`** - Urgent production fixes

### Workflow

```bash
# 1. Create feature branch
git checkout -b feature/your-feature-name

# 2. Make changes and commit
git add .
git commit -m "feat: add new feature"

# 3. Push to GitHub
git push origin feature/your-feature-name

# 4. Create PR on GitHub
# 5. Review and merge to main
# 6. Delete feature branch
git branch -d feature/your-feature-name
```

---

## Commit Message Guidelines

Follow the **Conventional Commits** format:

```
<type>[optional scope]: <description>

[optional body]

[optional footer]
```

### Commit Types

- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation only
- `style` - Formatting, no code change
- `refactor` - Code change without feature/fix
- `perf` - Performance improvement
- `test` - Adding/updating tests
- `chore` - Build process, dependencies
- `ci` - CI/CD changes

### Examples

**Good commits:**
```bash
feat(layer4): add Redis-based stateful analysis
fix(pii): correct entity_type field showing None
docs: update installation instructions for Windows
refactor: consolidate test files into tests/ directory
test: add integration tests for Layer 2
```

**Bad commits:**
```bash
update stuff
fix bug
changes
wip
```

### Rules

- Subject line: 50 characters or less
- Use imperative mood ("Add feature" not "Added feature")
- Capitalize subject
- No period at end of subject
- Separate subject from body with blank line
- Reference issues: `Closes #123` or `Refs #456`

---

## Pre-Push Verification

Before pushing to GitHub, run these commands:

```bash
# 1. Check what will be pushed
git log origin/main..HEAD --oneline

# 2. See which files changed
git diff --stat origin/main..HEAD

# 3. Verify no .env files in commits
git diff --name-only origin/main..HEAD | grep "\.env"

# 4. Search for potential secrets in commits
git log --patch origin/main..HEAD | grep -i "password\|secret\|api_key\|token"

# 5. Run tests (optional but recommended)
python tests/run_all_tests.py

# If all checks pass, push
git push origin feature/your-branch-name
```

---

## Security Best Practices

### ✅ DO

- Keep `.env` in `.gitignore` (already done)
- Commit `.env.example` with placeholders (already done)
- Use environment variables for all sensitive data
- Review `git diff` before every commit
- Review `git log` before every push
- Use strong, unique API keys
- Rotate API keys regularly

### ❌ NEVER

- Commit `.env` files with real values
- Commit API keys, passwords, or tokens
- Commit `credentials.json` or `service-account.json`
- Hardcode secrets in Python files
- Include debugging output with real data
- Commit database dumps or user data

### If You Accidentally Commit Secrets

1. Remove the file from the current commit:
   ```bash
   git rm --cached .env
   ```
2. Commit the removal:
   ```bash
   git commit -m "fix: remove sensitive .env file"
   ```
3. Force push (CAUTION):
   ```bash
   git push --force
   ```
4. **Rotate the compromised API keys immediately**
5. Consider using BFG Repo-Cleaner for history cleanup

---

## Pre-Commit Hooks

A pre-commit hook is installed at `.git/hooks/pre-commit` that automatically checks for:

1. **.env files** - Blocks commits containing `.env` or `.env.local`
2. **Potential secrets** - Warns if sensitive patterns are detected

### The Hook Automatically

- Blocks `.env` files from being committed
- Warns about potential secrets in staged changes
- Prompts for confirmation if secrets are detected

### Bypass the Hook (Not Recommended)

```bash
git commit --no-verify -m "your message"
```

**Only use `--no-verify` if you're absolutely sure the commit is safe.**

---

## Regular Security Audits

Run these commands **monthly** to verify security:

```bash
# 1. Check for .env files in git history (should return nothing)
git log --all --full-history --oneline -- ".env"

# 2. List all tracked files (review for anything suspicious)
git ls-files

# 3. Check for large files that shouldn't be tracked
git rev-list --objects --all |
  git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' |
  awk '/^blob/ {print substr($0,6)}' |
  sort -n -k2 |
  tail -10

# 4. Verify .gitignore is working
git check-ignore -v .env venv/ __pycache__/
```

---

## Environment Setup

For new developers joining the project:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/raushan-s/streamguard.git
   cd streamguard
   ```

2. **Copy the example environment file:**
   ```bash
   cp .env.example .env
   ```

3. **Edit `.env` with your actual API keys:**
   - `HF_TOKEN`: Get from https://huggingface.co/settings/tokens
   - `OPENAI_API_KEY`: Get from https://platform.openai.com/api-keys

4. **IMPORTANT:** Never commit `.env` to git (it's in .gitignore)

5. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

## Optional: Pre-Commit Framework

For enterprise-level security, install the pre-commit framework:

### Installation

```bash
pip install pre-commit
```

### Install Hooks

```bash
pre-commit install
```

### Configuration

The `.pre-commit-config.yaml` file includes:

- **Large file detection** - Blocks files > 1MB
- **Private key detection** - Blocks SSH keys, certificates
- **AWS credentials detection** - Blocks AWS access keys
- **YAML/JSON validation** - Ensures config files are valid
- **Code formatting** - Auto-formats Python code with Black

### Run Manually

```bash
# Run all hooks on all files
pre-commit run --all-files

# Run on staged files only
pre-commit run
```

---

## Summary of Files Modified

### Modified Files

1. **`.gitignore`** - Enhanced with additional security patterns:
   - HuggingFace cache directories (`.cache/`, `.huggingface/`)
   - Temporary files (`*.tmp`, `*.temp`, `download_*/`)
   - Jupyter checkpoints (`.ipynb_checkpoints/`)
   - Additional OS files (`desktop.ini`, `*.lnk`, `.AppleDouble`, `.LSOverride`)
   - All `.env` files (`*.env` pattern)

### Created Files

2. **`.git/hooks/pre-commit`** - Pre-commit hook script that:
   - Blocks `.env` and `.env.local` files from being committed
   - Warns about potential secrets in staged changes
   - Prompts for confirmation if secrets are detected

3. **`.pre-commit-config.yaml`** - Optional pre-commit framework configuration:
   - Large file detection
   - Private key detection
   - AWS credentials detection
   - YAML/JSON validation
   - Code formatting with Black

4. **`GIT_WORKFLOW.md`** - This documentation file

---

## Verification Results

All verification steps passed:

✅ `.env` is NOT tracked
✅ `.env.example` IS tracked
✅ `.gitignore` patterns work correctly (tested with `test.env`)
✅ Repository is clean (no unexpected files)
✅ Recent commits show no sensitive data
✅ Pre-commit hook is installed and executable

---

## Risk Assessment

**Risk Level:** LOW

- No code modifications required
- Only adding more protection to `.gitignore`
- Pre-commit hooks are optional (can be bypassed with `--no-verify`)
- Current repository state is already secure

### Rollback Plan

If `.gitignore` changes cause issues, revert the additions:

```bash
git checkout .gitignore
```

---

## End State

After implementing this plan:

- ✅ Enhanced `.gitignore` with additional security patterns
- ✅ Clear pre-commit checklist documented
- ✅ Branch strategy defined
- ✅ Commit message guidelines established
- ✅ Pre-push verification steps documented
- ✅ Security best practices clearly outlined
- ✅ Pre-commit hooks configured and active
- ✅ Regular audit procedures defined
- ✅ Verification steps confirm security

**Result:** StreamGuard repository now has industry-standard Git security practices, ensuring no sensitive files are ever committed to GitHub.

---

**Made with secure development practices in mind**
