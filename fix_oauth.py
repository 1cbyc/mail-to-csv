#!/usr/bin/env python3
"""
OAuth Consent Screen Fix Helper
"""

import webbrowser
import time

def main():
    print("OAuth Consent Screen Fix Helper")
    print("=" * 40)
    
    print("\nYou're getting the 'testing mode' error because:")
    print("  - Your OAuth consent screen is in testing mode")
    print("  - Your email isn't added as a test user")
    print("  - OR the app needs to be published")
    
    print("\nHere are your options:")
    print("\nOption 1: Add yourself as a test user (Quick fix)")
    print("1. Go to Google Cloud Console > OAuth consent screen")
    print("2. Scroll to 'Test users' section")
    print("3. Click 'Add Users'")
    print("4. Add your Gmail address")
    print("5. Save and try again")
    
    print("\nOption 2: Publish the app (Recommended)")
    print("1. Go to Google Cloud Console > OAuth consent screen")
    print("2. Click 'Publish App' at the top")
    print("3. Choose 'In production'")
    print("4. Save changes")
    print("5. Wait 2-3 minutes and try again")
    
    print("\nWould you like me to open Google Cloud Console?")
    choice = input("Enter 'y' to open, or 'n' to continue manually: ").lower()
    
    if choice == 'y':
        print("\nOpening Google Cloud Console...")
        webbrowser.open("https://console.cloud.google.com/apis/credentials/consent")
        print("Opened in your browser!")
        print("\nSteps to follow:")
        print("1. Add your email as a test user, OR")
        print("2. Click 'Publish App' to make it public")
        print("3. Come back and run: python gmail_to_csv.py")
    
    print("\nAfter fixing the OAuth consent screen:")
    print("  python gmail_to_csv.py --query 'in:sent \"Phrase\"' --output emails_with_phrase.csv")
    
    print("\nIf you published the app, wait 2-3 minutes before trying again.")

if __name__ == "__main__":
    main() 