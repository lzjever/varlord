#!/bin/bash
# Security scan script for Varlord repository
# Usage: ./scripts/security-scan.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$REPO_ROOT"

echo "🔍 Security Scan for Varlord"
echo "================================"
echo ""

# Function to print colored output
print_success() {
    echo "✅ $1"
}

print_warning() {
    echo "⚠️  $1"
}

print_error() {
    echo "❌ $1"
}

print_section() {
    echo ""
    echo "📋 $1"
    echo "--------------------------------"
}

# 1. Check for certificate files in git history
print_section "Checking for certificates in git history"
if git log --all --full-history -- "*cert*" 2>/dev/null | grep -q .; then
    print_error "Certificate files found in git history"
    git log --all --full-history -- "*cert*" --oneline | head -5
    HAS_ISSUES=1
else
    print_success "No certificate files in history"
fi

# 2. Check for key files
print_section "Checking for key files in git history"
if git log --all --full-history -- "*.pem" "*.key" "*.crt" 2>/dev/null | grep -q .; then
    print_error "Key files found in git history"
    git log --all --full-history -- "*.pem" "*.key" "*.crt" --oneline | head -5
    HAS_ISSUES=1
else
    print_success "No key files in history"
fi

# 3. Check .gitignore
print_section "Checking .gitignore"
GITIGNORE_ISSUES=0
if ! grep -q "cert/" .gitignore 2>/dev/null; then
    print_warning ".gitignore missing 'cert/' pattern"
    GITIGNORE_ISSUES=1
fi

if ! grep -q "*.pem" .gitignore 2>/dev/null; then
    print_warning ".gitignore missing '*.pem' pattern"
    GITIGNORE_ISSUES=1
fi

if ! grep -q "*.key" .gitignore 2>/dev/null; then
    print_warning ".gitignore missing '*.key' pattern"
    GITIGNORE_ISSUES=1
fi

if ! grep -q ".env" .gitignore 2>/dev/null; then
    print_warning ".gitignore missing '.env' pattern"
    GITIGNORE_ISSUES=1
fi

if [ $GITIGNORE_ISSUES -eq 0 ]; then
    print_success ".gitignore is properly configured"
fi

# 4. Check for obvious secrets in code
print_section "Checking for potential secrets in code"
SECRET_PATTERNS=(
    "password\s*=\s*['\"][^'\"]+['\"]"
    "api_key\s*=\s*['\"][^'\"]+['\"]"
    "secret\s*=\s*['\"][^'\"]+['\"]"
    "token\s*=\s*['\"][^'\"]+['\"]"
)

FOUND_SECRETS=0
for pattern in "${SECRET_PATTERNS[@]}"; do
    if grep -r "$pattern" --include="*.py" varlord/ examples/ 2>/dev/null | \
       grep -v "test\|example\|TODO\|FIXME\|default" | grep -q .; then
        print_warning "Possible secret found: $pattern"
        grep -rn "$pattern" --include="*.py" varlord/ examples/ 2>/dev/null | \
            grep -v "test\|example\|TODO\|FIXME\|default" | head -3
        FOUND_SECRETS=1
    fi
done

if [ $FOUND_SECRETS -eq 0 ]; then
    print_success "No obvious secrets found in code"
fi

# 5. Check dependencies for vulnerabilities
print_section "Checking dependencies for vulnerabilities"
if command -v uv &> /dev/null; then
    if uv run pip-audit --strict 2>/dev/null; then
        print_success "No known vulnerabilities found"
    else
        print_error "Vulnerabilities found in dependencies"
        HAS_ISSUES=1
    fi
else
    print_warning "uv not found, skipping dependency audit"
    print_warning "Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
fi

# 6. Check for hardcoded paths
print_section "Checking for hardcoded paths"
if grep -r "/home/\|/root/\|/Users/" --include="*.py" varlord/ | \
   grep -v "test\|example\|TODO" | grep -q .; then
    print_warning "Hardcoded paths found in code"
    grep -rn "/home/\|/root/\|/Users/" --include="*.py" varlord/ | \
        grep -v "test\|example\|TODO" | head -3
else
    print_success "No hardcoded paths found"
fi

# 7. Summary
echo ""
echo "================================"
echo "📊 Scan Summary"
echo "================================"

if [ "${HAS_ISSUES:-0}" -eq 1 ]; then
    print_error "Security issues found! Please review and fix."
    exit 1
else
    print_success "No critical security issues found!"
    exit 0
fi
