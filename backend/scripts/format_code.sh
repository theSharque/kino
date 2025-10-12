#!/bin/bash
# Code formatting script for backend
# Ensures consistent code style

echo "Formatting Python files..."

# Remove trailing whitespace from all Python files
find . -name "*.py" -type f ! -path "./venv/*" ! -path "./__pycache__/*" ! -path "*/__pycache__/*" ! -name "get-pip.py" -exec sed -i 's/[[:space:]]*$//' {} \;

# Ensure newline at end of all Python files
find . -name "*.py" -type f ! -path "./venv/*" ! -path "./__pycache__/*" ! -path "*/__pycache__/*" ! -name "get-pip.py" -exec sh -c 'tail -c1 "$1" | read -r _ || echo >> "$1"' _ {} \;

echo "Formatting Markdown files..."
find . -name "*.md" -type f ! -path "./venv/*" -exec sed -i 's/[[:space:]]*$//' {} \;

echo "Formatting config files..."
find . -name ".gitignore" -type f -exec sed -i 's/[[:space:]]*$//' {} \;
find . -name ".env*" -type f -exec sed -i 's/[[:space:]]*$//' {} \;

echo "✓ Code formatting complete!"

