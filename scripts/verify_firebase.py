#!/usr/bin/env python3
"""
Firebase Setup Verification Script

This script verifies that Firebase SDK and Google Auth are properly configured
for the digital-workshop-hub project.

Usage:
    export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
    python scripts/verify_firebase.py
"""

import os
import sys

def verify_google_auth():
    """Verify Google Auth credentials are working."""
    print("Verifying Google Auth...")
    
    try:
        from google.oauth2 import service_account
        from google.auth.transport.requests import Request
        
        creds_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path:
            print("  ERROR: GOOGLE_APPLICATION_CREDENTIALS environment variable not set")
            return False
        
        if not os.path.exists(creds_path):
            print(f"  ERROR: Credentials file not found: {creds_path}")
            return False
        
        SCOPES = [
            'https://www.googleapis.com/auth/cloud-platform',
            'https://www.googleapis.com/auth/firebase'
        ]
        
        credentials = service_account.Credentials.from_service_account_file(
            creds_path,
            scopes=SCOPES
        )
        
        print(f"  Service Account: {credentials.service_account_email}")
        print(f"  Project ID: {credentials.project_id}")
        
        credentials.refresh(Request())
        print(f"  Token valid: {credentials.valid}")
        print("  Google Auth: OK")
        return True
        
    except Exception as e:
        print(f"  ERROR: {e}")
        return False


def verify_firebase_admin():
    """Verify Firebase Admin SDK is working."""
    print("\nVerifying Firebase Admin SDK...")
    
    try:
        import firebase_admin
        from firebase_admin import credentials, auth
        
        # Clean up any existing app
        try:
            firebase_admin.delete_app(firebase_admin.get_app())
        except:
            pass
        
        creds_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
        cred = credentials.Certificate(creds_path)
        app = firebase_admin.initialize_app(cred)
        
        print(f"  App name: {app.name}")
        print(f"  Project ID: {app.project_id}")
        
        # Test Firebase Auth access
        page = auth.list_users()
        user_count = len(list(page.users))
        print(f"  Users found: {user_count}")
        print("  Firebase Admin SDK: OK")
        return True
        
    except Exception as e:
        print(f"  ERROR: {e}")
        return False


def main():
    print("=" * 50)
    print("Firebase Setup Verification")
    print("=" * 50)
    print()
    
    google_ok = verify_google_auth()
    firebase_ok = verify_firebase_admin()
    
    print()
    print("=" * 50)
    if google_ok and firebase_ok:
        print("All checks passed!")
        return 0
    else:
        print("Some checks failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
