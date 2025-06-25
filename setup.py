#!/usr/bin/env python3
"""
Setup script for Gmail to CSV exporter
"""

import subprocess
import sys
import os

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 7):
        print("Python 3.7 or higher is required.")
        print(f"Current version: {sys.version}")
        return False
    print(f"Python version: {sys.version.split()[0]}")
    return True

def install_requirements():
    """Install required packages."""
    try:
        print("Installing required packages...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("Packages installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to install packages: {e}")
        return False

def check_credentials_file():
    """Check if credentials.json exists."""
    if os.path.exists("credentials.json"):
        print("credentials.json found")
        return True
    else:
        print("credentials.json not found")
        print("\nTo get credentials.json:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a new project or select existing one")
        print("3. Enable Gmail API (APIs & Services > Library > Gmail API)")
        print("4. Configure OAuth consent screen (APIs & Services > OAuth consent screen)")
        print("5. Create OAuth 2.0 credentials (APIs & Services > Credentials)")
        print("  - Choose 'Desktop application' (NOT Android/iOS)")
        print("  - If asked for store ID, you selected wrong app type")
        print("6. Download and rename to 'credentials.json'")
        print("7. Place in this directory")
        return False

def check_oauth_consent_screen():
    """Provide guidance on OAuth consent screen setup."""
    print("\nOAuth Consent Screen Setup:")
    print("If you haven't configured the OAuth consent screen:")
    print("1. Go to APIs & Services > OAuth consent screen")
    print("2. Choose 'External' user type")
    print("3. Fill in required information:")
    print("  - App name: 'Gmail CSV Exporter'")
    print("  - User support email: Your email")
    print("  - Developer contact: Your email")
    print("4. Add scope: https://www.googleapis.com/auth/gmail.readonly")
    print("5. Add your Gmail address as test user")
    print("6. Save and continue")

def main():
    print("Gmail to CSV Exporter Setup")
    print("=" * 40)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install requirements
    if not install_requirements():
        sys.exit(1)
    
    # Check credentials
    credentials_found = check_credentials_file()
    
    # Provide OAuth consent screen guidance
    check_oauth_consent_screen()
    
    if not credentials_found:
        print("\n IMPORTANT: Store ID Issue")
        print("If you're being asked for a 'store ID' when creating credentials:")
        print("- Make sure you select 'Desktop application' NOT 'Android' or 'iOS'")
        print("- The store ID is only required for mobile apps")
        print("- Desktop applications don't need a store ID")
    
    print("\nSetup complete!")
    if not os.path.exists(".env") and os.path.exists(".env.example"):
        print("\nCopy .env.example to .env and add your Yahoo / path settings:")
        print("  cp .env.example .env")

    print("\nNext steps:")
    print("1. Fill in .env (see .env.example)")
    print("2. Place credentials.json in this directory for Gmail")
    print("3. Run: make gmail   or   python gmail_to_csv.py")
    print("4. See WORKFLOW.md for the full pipeline")

if __name__ == "__main__":
    main() 