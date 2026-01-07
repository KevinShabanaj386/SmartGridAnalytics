#!/bin/bash

# Pre-commit Code Review Script
# Uses Cursor AI principles to review code before committing
# 100% private - no GitHub integration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🔍 Pre-Commit Code Review"
echo "=========================="
echo ""

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}❌ Error: Not in a git repository${NC}"
    exit 1
fi

# Get list of files to review
if [ -n "$1" ]; then
    FILES="$1"
else
    # Get staged files or modified files
    FILES=$(git diff --cached --name-only --diff-filter=ACM 2>/dev/null || git diff --name-only --diff-filter=ACM 2>/dev/null || echo "")
fi

if [ -z "$FILES" ]; then
    echo -e "${YELLOW}⚠️  No files to review${NC}"
    exit 0
fi

echo "📋 Files to review:"
echo "$FILES" | sed 's/^/  - /'
echo ""

# Review checklist
ISSUES=0
WARNINGS=0

review_file() {
    local file="$1"
    local ext="${file##*.}"
    
    echo -e "\n${GREEN}Reviewing: $file${NC}"
    
    # Python-specific checks
    if [ "$ext" = "py" ]; then
        # Check for common issues
        if grep -q "TODO\|FIXME\|XXX\|HACK" "$file"; then
            echo -e "${YELLOW}  ⚠️  Found TODO/FIXME comments${NC}"
            WARNINGS=$((WARNINGS + 1))
        fi
        
        if grep -q "password\s*=\s*['\"]" "$file" || grep -q "api_key\s*=\s*['\"]" "$file"; then
            echo -e "${RED}  ❌ Potential hardcoded credentials!${NC}"
            ISSUES=$((ISSUES + 1))
        fi
        
        if grep -q "print(" "$file" && ! grep -q "# DEBUG" "$file"; then
            echo -e "${YELLOW}  ⚠️  Found print() statements (consider using logger)${NC}"
            WARNINGS=$((WARNINGS + 1))
        fi
        
        # Check for basic error handling
        if grep -q "except:" "$file" && ! grep -q "except.*Exception" "$file"; then
            echo -e "${YELLOW}  ⚠️  Bare except clause found (be more specific)${NC}"
            WARNINGS=$((WARNINGS + 1))
        fi
    fi
    
    # General checks
    if grep -qi "localhost\|127.0.0.1" "$file" && [[ "$file" != *"test"* ]] && [[ "$file" != *"docker-compose"* ]]; then
        echo -e "${YELLOW}  ⚠️  Found localhost reference (check if this should be configurable)${NC}"
        WARNINGS=$((WARNINGS + 1))
    fi
    
    # Check file size (warn if very large)
    local lines=$(wc -l < "$file" 2>/dev/null || echo "0")
    if [ "$lines" -gt 500 ]; then
        echo -e "${YELLOW}  ⚠️  Large file ($lines lines) - consider splitting${NC}"
        WARNINGS=$((WARNINGS + 1))
    fi
}

# Review each file
for file in $FILES; do
    if [ -f "$file" ]; then
        review_file "$file"
    fi
done

# Summary
echo ""
echo "=========================="
echo "📊 Review Summary"
echo "=========================="
echo -e "${GREEN}✅ Files reviewed: $(echo "$FILES" | wc -l | tr -d ' ')${NC}"

if [ $ISSUES -gt 0 ]; then
    echo -e "${RED}❌ Critical issues found: $ISSUES${NC}"
    echo -e "${RED}   Please fix these before committing!${NC}"
    exit 1
fi

if [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Warnings: $WARNINGS${NC}"
    echo -e "${YELLOW}   Consider addressing these${NC}"
    exit 0
fi

echo -e "${GREEN}✅ No issues found!${NC}"
echo ""
echo "💡 Tip: Use Cursor AI (Cmd+K) for deeper code analysis"
exit 0

