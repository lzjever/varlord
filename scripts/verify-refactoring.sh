#!/bin/bash
# Verification script for Phase 1 refactoring
# Usage: ./scripts/verify-refactoring.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$REPO_ROOT"

echo "🔍 Phase 1 Refactoring Verification"
echo "================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_section() {
    echo ""
    echo "📋 $1"
    echo "--------------------------------"
}

# 1. Check method complexity
print_section "Checking method complexity"

# Check _dict_to_model complexity
if command -v radon &> /dev/null; then
    echo "Checking _dict_to_model complexity..."
    COMPLEXITY=$(radon cc varlord/config.py -a | grep "_dict_to_model" | awk '{print $2}')
    if [ ! -z "$COMPLEXITY" ]; then
        if [ "$COMPLEXITY" -lt 10 ]; then
            print_success "_dict_to_model complexity: $COMPLEXITY (good)"
        elif [ "$COMPLEXITY" -lt 15 ]; then
            print_warning "_dict_to_model complexity: $COMPLEXITY (acceptable)"
        else
            print_error "_dict_to_model complexity: $COMPLEXITY (too high)"
        fi
    fi
else
    print_warning "radon not installed, skipping complexity check"
    echo "Install with: pip install radon"
fi

# 2. Check for duplicate code
print_section "Checking for duplicate code"

if command -v pycpd &> /dev/null; then
    echo "Checking for duplicate code blocks..."
    DUPLICATES=$(pycpd --min-lines=5 varlord/ 2>/dev/null | grep "Found" || echo "No duplicates found")
    echo "$DUPLICATES"
else
    print_warning "pycpd not installed, skipping duplicate check"
    echo "Install with: pip install pycpd"
fi

# 3. Check line length
print_section "Checking line length"

LONG_LINES=$(grep -n ".\{100\}" varlord/config.py | wc -l)
if [ "$LONG_LINES" -eq 0 ]; then
    print_success "No lines exceed 100 characters"
else
    print_warning "$LONG_LINES lines exceed 100 characters"
fi

# 4. Run all tests
print_section "Running test suite"

echo "Running unit tests..."
if uv run pytest tests/ -m "not integration" -v --tb=short; then
    print_success "All unit tests passed"
else
    print_error "Some unit tests failed"
    exit 1
fi

# 5. Check test coverage
print_section "Checking test coverage"

echo "Running coverage check..."
COVERAGE_REPORT=$(uv run pytest tests/ -m "not integration" --cov=varlord --cov-report=term-missing 2>&1)
COVERAGE_PCT=$(echo "$COVERAGE_REPORT" | grep "TOTAL" | awk '{print $4}' | sed 's/%//')

if [ ! -z "$COVERAGE_PCT" ]; then
    if [ "$(echo "$COVERAGE_PCT >= 80" | bc)" -eq 1 ]; then
        print_success "Coverage: ${COVERAGE_PCT}% (good)"
    elif [ "$(echo "$COVERAGE_PCT >= 70" | bc)" -eq 1 ]; then
        print_warning "Coverage: ${COVERAGE_PCT}% (acceptable, target: 80%)"
    else
        print_error "Coverage: ${COVERAGE_PCT}% (below 70%)"
    fi
fi

# 6. Check type hints
print_section "Checking type hints coverage"

if command -v mypy &> /dev/null; then
    echo "Running mypy..."
    if uv run mypy varlord/ --ignore-missing-imports; then
        print_success "Type hints check passed"
    else
        print_warning "Some type hint issues found"
    fi
else
    print_warning "mypy not installed, skipping type check"
fi

# 7. Summary
echo ""
echo "================================"
echo "📊 Verification Summary"
echo "================================"

print_success "Verification complete!"
echo ""
echo "Next steps:"
echo "1. Review complexity warnings"
echo "2. Address duplicate code blocks"
echo "3. Improve test coverage if needed"
echo "4. Run: make check (full quality checks)"
