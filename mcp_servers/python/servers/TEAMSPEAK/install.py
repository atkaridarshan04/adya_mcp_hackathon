#!/usr/bin/env python3
"""
Interactive installation script for TeamSpeak MCP.
"""

import json
import os
import platform
import subprocess
import sys
from pathlib import Path

def print_banner():
    """Display installation banner."""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                    🎮 TeamSpeak MCP Installer                 ║
║          Configure your MCP server for Claude                ║
╚══════════════════════════════════════════════════════════════╝
""", file=sys.stderr)

def install_dependencies():
    """Install Python dependencies."""
    print("📦 Installing dependencies...", file=sys.stderr)
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully", file=sys.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}", file=sys.stderr)
        return False

def collect_teamspeak_config():
    """Collect TeamSpeak configuration from user."""
    print("\n🔧 TeamSpeak Configuration", file=sys.stderr)
    print("Please enter your TeamSpeak server information:\n", file=sys.stderr)
    
    config = {}
    
    # Host
    host = input("📍 TeamSpeak server address: ").strip()
    while not host:
        host = input("❌ Address is required. Try again: ").strip()
    config["TEAMSPEAK_HOST"] = host
    
    # Port
    port = input("🔌 ServerQuery port (default: 10011): ").strip()
    config["TEAMSPEAK_PORT"] = port if port else "10011"
    
    # User
    user = input("👤 ServerQuery username (default: serveradmin): ").strip()
    config["TEAMSPEAK_USER"] = user if user else "serveradmin"
    
    # Password
    password = input("🔒 ServerQuery password: ").strip()
    while not password:
        password = input("❌ Password is required. Try again: ").strip()
    config["TEAMSPEAK_PASSWORD"] = password
    
    # Server ID
    server_id = input("🆔 Virtual server ID (default: 1): ").strip()
    config["TEAMSPEAK_SERVER_ID"] = server_id if server_id else "1"
    
    return config

def create_env_file(config):
    """Create .env file with configuration."""
    print("\n📄 Creating configuration file...", file=sys.stderr)
    
    try:
        with open(".env", "w") as f:
            f.write("# TeamSpeak MCP Configuration\n")
            f.write("# Generated automatically by installer\n\n")
            
            for key, value in config.items():
                f.write(f"{key}={value}\n")
        
        print("✅ .env file created successfully", file=sys.stderr)
        return True
    except Exception as e:
        print(f"❌ Error creating .env file: {e}", file=sys.stderr)
        return False

def find_claude_config_path():
    """Find Claude Desktop configuration path."""
    system = platform.system()
    
    if system == "Darwin":  # macOS
        return Path.home() / "Library/Application Support/Claude/claude_desktop_config.json"
    elif system == "Windows":
        return Path.home() / "AppData/Roaming/Claude/claude_desktop_config.json"  
    else:  # Linux
        return Path.home() / ".config/claude/claude_desktop_config.json"

def update_claude_config(ts_config):
    """Update Claude Desktop configuration."""
    print("\n🤖 Configuring Claude Desktop...", file=sys.stderr)
    
    claude_config_path = find_claude_config_path()
    print(f"📍 Claude configuration path: {claude_config_path}", file=sys.stderr)
    
    # Create directory if needed
    claude_config_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing configuration or create new
    if claude_config_path.exists():
        try:
            with open(claude_config_path, 'r') as f:
                claude_config = json.load(f)
        except json.JSONDecodeError:
            claude_config = {}
    else:
        claude_config = {}
    
    # Add TeamSpeak MCP configuration
    if "mcpServers" not in claude_config:
        claude_config["mcpServers"] = {}
    
    claude_config["mcpServers"]["teamspeak"] = {
        "command": "python",
        "args": ["-m", "teamspeak_mcp.server"],
        "env": ts_config
    }
    
    # Save configuration
    try:
        with open(claude_config_path, 'w') as f:
            json.dump(claude_config, f, indent=2)
        
        print("✅ Claude Desktop configuration updated", file=sys.stderr)
        return True
    except Exception as e:
        print(f"❌ Error updating Claude configuration: {e}", file=sys.stderr)
        print(f"💡 You can manually copy the content from claude_desktop_config.json", file=sys.stderr)
        return False

def test_installation():
    """Test the installation."""
    print("\n🧪 Testing installation...", file=sys.stderr)
    
    try:
        subprocess.check_call([sys.executable, "test_mcp.py"])
        return True
    except subprocess.CalledProcessError:
        print("❌ Tests failed", file=sys.stderr)
        return False

def main():
    """Main installation function."""
    print_banner()
    
    # Check Python version
    if sys.version_info < (3, 10):
        print("❌ Python 3.10+ is required", file=sys.stderr)
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # TeamSpeak configuration
    ts_config = collect_teamspeak_config()
    
    # Create .env file
    if not create_env_file(ts_config):
        sys.exit(1)
    
    # Claude Desktop configuration
    claude_updated = update_claude_config(ts_config)
    
    # Test installation
    test_success = test_installation()
    
    # Summary
    print("\n" + "="*60, file=sys.stderr)
    print("📋 INSTALLATION SUMMARY", file=sys.stderr)
    print("="*60, file=sys.stderr)
    print(f"✅ Dependencies installed", file=sys.stderr)
    print(f"✅ TeamSpeak configuration created", file=sys.stderr)
    print(f"{'✅' if claude_updated else '❌'} Claude Desktop configuration", file=sys.stderr)
    print(f"{'✅' if test_success else '❌'} Installation tests", file=sys.stderr)
    
    if claude_updated and test_success:
        print("\n🎉 Installation completed successfully!", file=sys.stderr)
        print("\n🚀 Next steps:", file=sys.stderr)
        print("1. Restart Claude Desktop", file=sys.stderr)
        print("2. Open a new conversation", file=sys.stderr)
        print("3. Test with: 'Connect to TeamSpeak server'", file=sys.stderr)
        print("4. Use: 'List connected users'", file=sys.stderr)
    else:
        print("\n⚠️  Installation partially successful", file=sys.stderr)
        if not claude_updated:
            print("💡 Manually configure Claude Desktop with claude_desktop_config.json", file=sys.stderr)
        if not test_success:
            print("💡 Check your TeamSpeak configuration in .env", file=sys.stderr)

if __name__ == "__main__":
    main() 