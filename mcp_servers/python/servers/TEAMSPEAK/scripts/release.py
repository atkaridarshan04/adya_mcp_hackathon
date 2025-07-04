#!/usr/bin/env python3
"""
Release automation script for TeamSpeak MCP
Usage: python scripts/release.py [patch|minor|major]
"""

import re
import subprocess
import sys
from pathlib import Path

def get_current_version():
    """Get current version from pyproject.toml"""
    pyproject_path = Path("pyproject.toml")
    content = pyproject_path.read_text()
    match = re.search(r'version = "([^"]+)"', content)
    if not match:
        raise ValueError("Could not find version in pyproject.toml")
    return match.group(1)

def bump_version(version, bump_type):
    """Bump version according to semantic versioning"""
    parts = list(map(int, version.split('.')))
    
    if bump_type == "patch":
        parts[2] += 1
    elif bump_type == "minor":
        parts[1] += 1
        parts[2] = 0
    elif bump_type == "major":
        parts[0] += 1
        parts[1] = 0
        parts[2] = 0
    else:
        raise ValueError(f"Invalid bump type: {bump_type}")
    
    return ".".join(map(str, parts))

def update_version_in_file(file_path, old_version, new_version):
    """Update version in a file"""
    content = Path(file_path).read_text()
    if file_path.endswith("__init__.py"):
        updated = content.replace(f'__version__ = "{old_version}"', f'__version__ = "{new_version}"')
    else:
        updated = content.replace(f'version = "{old_version}"', f'version = "{new_version}"')
    Path(file_path).write_text(updated)

def run_command(cmd, check=True):
    """Run a shell command."""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"❌ Command failed: {cmd}", file=sys.stderr)
        print(f"Error: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    return result

def show_usage():
    """Show usage information."""
    print("Usage: python scripts/release.py [patch|minor|major]", file=sys.stderr)
    print("Examples:", file=sys.stderr)
    print("  python scripts/release.py patch   # 1.0.3 -> 1.0.4", file=sys.stderr)
    print("  python scripts/release.py minor   # 1.0.3 -> 1.1.0", file=sys.stderr)
    print("  python scripts/release.py major   # 1.0.3 -> 2.0.0", file=sys.stderr)

def main():
    """Main release function."""
    if len(sys.argv) != 2 or sys.argv[1] not in ['patch', 'minor', 'major']:
        show_usage()
        sys.exit(1)
    
    bump_type = sys.argv[1]
    
    # Check git status
    result = run_command("git status --porcelain", check=False)
    if result.stdout.strip():
        print("❌ Git working directory is not clean. Commit your changes first.", file=sys.stderr)
        sys.exit(1)
    
    # Get current version and calculate new version
    current_version = get_current_version()
    new_version = bump_version(current_version, bump_type)
    tag_name = f"v{new_version}"
    
    print(f"🚀 Releasing TeamSpeak MCP", file=sys.stderr)
    print(f"📋 Current version: {current_version}", file=sys.stderr)
    print(f"📋 New version: {new_version}", file=sys.stderr)
    print(f"📋 Bump type: {bump_type}", file=sys.stderr)
    
    # Confirm
    response = input("Continue? (y/N): ").strip().lower()
    if response != 'y':
        print("❌ Release cancelled", file=sys.stderr)
        sys.exit(1)
    
    # Update version in pyproject.toml
    print("📝 Updating version in pyproject.toml...", file=sys.stderr)
    update_version_in_file("pyproject.toml", current_version, new_version)
    
    # Update version in __init__.py
    print("📝 Updating version in __init__.py...", file=sys.stderr)
    update_version_in_file("teamspeak_mcp/__init__.py", current_version, new_version)
    
    # Commit changes
    print("📝 Committing version bump...", file=sys.stderr)
    run_command(f'git add pyproject.toml teamspeak_mcp/__init__.py')
    run_command(f'git commit -m "chore: bump version to {new_version}"')
    
    # Create and push tag
    print("🏷️ Creating and pushing tag...", file=sys.stderr)
    run_command(f'git tag {tag_name}')
    run_command('git push origin main')
    run_command(f'git push origin {tag_name}')
    
    print(f"", file=sys.stderr)
    print(f"🎉 Release initiated!", file=sys.stderr)
    print(f"🔗 Tag: {tag_name}", file=sys.stderr)
    print(f"🤖 GitHub Actions will now:", file=sys.stderr)
    print(f"   1. Build the package", file=sys.stderr)
    print(f"   2. Test on TestPyPI", file=sys.stderr)
    print(f"   3. Publish to PyPI", file=sys.stderr)
    print(f"   4. Build Docker images", file=sys.stderr)
    print(f"   5. Create GitHub release", file=sys.stderr)
    print(f"", file=sys.stderr)
    print(f"🔍 Monitor progress:", file=sys.stderr)
    print(f"   - Actions: https://github.com/MarlBurroW/teamspeak-mcp/actions", file=sys.stderr)
    print(f"   - PyPI: https://pypi.org/project/teamspeak-mcp/{new_version}/", file=sys.stderr)
    print(f"   - Docker: ghcr.io/marlburrow/teamspeak-mcp:{tag_name}", file=sys.stderr)

if __name__ == "__main__":
    main() 