# Development Scripts

## Pre-Commit Review Script

### Purpose
Automated code review script that checks for common issues before committing code. Helps maintain code quality and catch issues early.

### Usage

```bash
# Review all staged or modified files
./scripts/pre-commit-review.sh

# Review a specific file
./scripts/pre-commit-review.sh path/to/file.py

# Review multiple files
./scripts/pre-commit-review.sh file1.py file2.py
```

### What It Checks

#### Security Issues
- Hardcoded credentials (passwords, API keys)
- Potential SQL injection risks

#### Code Quality
- TODO/FIXME comments
- Print statements (should use logger)
- Bare except clauses
- Large files (>500 lines)

#### Configuration
- Localhost references (should be configurable)
- Hardcoded values

### Exit Codes
- `0` - No critical issues (warnings may exist)
- `1` - Critical issues found (should fix before committing)

### Integration

You can integrate this into your git workflow:

```bash
# Add to .git/hooks/pre-commit (optional)
#!/bin/bash
./scripts/pre-commit-review.sh
```

### Example Output

```
🔍 Pre-Commit Code Review
==========================

📋 Files to review:
  - app.py
  - utils.py

Reviewing: app.py
  ⚠️  Found print() statements (consider using logger)

Reviewing: utils.py
  ✅ No issues found

==========================
📊 Review Summary
==========================
✅ Files reviewed: 2
⚠️  Warnings: 1
   Consider addressing these
```

### Notes

- This script is a **supplement** to other review tools
- Use Cursor AI for deeper code analysis
- Run tests separately: `pytest`
- Run linting separately: `flake8 .`

