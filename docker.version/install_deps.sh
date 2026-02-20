#!/bin/bash
# Sync dependencies from main project to Docker version requirements.txt

echo "Syncing dependencies from main project..."

# Extract production dependencies from main pyproject.toml
grep -A 15 'dependencies = \[' ../pyproject.toml | \
grep -E '^    "[^"]*"' | \
sed 's/^    "//g; s/"$//g' | \
sort > requirements.txt.tmp

# Verify dependencies
echo "Extracted dependencies:"
cat requirements.txt.tmp

# Replace existing requirements.txt
mv requirements.txt.tmp requirements.txt

echo "Dependencies sync complete!"
echo "Current requirements.txt:"
cat requirements.txt
