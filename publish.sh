#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print step information
print_step() {
    echo -e "${YELLOW}[STEP]${NC} $1"
}

# Function to print success messages
print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Function to print error messages and exit
print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Function to update version in pyproject.toml
update_version() {
    local version=$1
    print_step "Updating version to $version in pyproject.toml"

    VERSION_VALUE="$version" python - <<'PY'
import os
import re
from pathlib import Path

version = os.environ["VERSION_VALUE"]
pyproject = Path("pyproject.toml")
text = pyproject.read_text(encoding="utf-8")
pattern = r'(?m)^version\s*=\s*"[0-9]+\.[0-9]+\.[0-9]+"'
replacement = f'version = "{version}"'
new_text, count = re.subn(pattern, replacement, text)
if count == 0:
    raise SystemExit("version field not found in pyproject.toml")
pyproject.write_text(new_text, encoding="utf-8")
PY

    if [ $? -eq 0 ]; then
        print_success "Version updated successfully"
    else
        print_error "Failed to update version in pyproject.toml"
    fi
}

# Check if version parameter is provided
if [ -z "$1" ]; then
print_error "Please provide version number (e.g., ./publish.sh 1.0.0)"
fi

VERSION=$1

# Validate version format
if ! [[ $VERSION =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    print_error "Invalid version format. Please use semantic versioning (e.g., 1.0.0)"
fi

# Update version in pyproject.toml
update_version $VERSION

# Ensure pip is up to date
print_step "Upgrading pip"
python -m pip install --upgrade pip || print_error "Failed to upgrade pip"

# Install/upgrade build tools
print_step "Installing/upgrading build tools"
python -m pip install --upgrade build twine || print_error "Failed to install build tools"

# Clean previous builds
print_step "Cleaning previous builds"
rm -rf dist/ build/ *.egg-info/ || print_error "Failed to clean previous builds"

# Build distribution packages
print_step "Building distribution packages"
python -m build || print_error "Failed to build distribution packages"

# Validate the built packages
print_step "Validating packages"
python -m twine check dist/* || print_error "Failed to validate packages"

# Upload to PyPI
print_step "Uploading to PyPI"
python -m twine upload dist/* || print_error "Failed to upload to PyPI"

print_success "Package v$VERSION has been successfully built and uploaded to PyPI!"
