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


def verify_google_auth_provider():
    """Verify Google Sign-In provider is configured in Firebase Auth."""
    print("\nVerifying Google Sign-In Provider...")
    
    try:
        import requests
        from google.oauth2 import service_account
        from google.auth.transport.requests import Request
        
        creds_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path:
            print("  ERROR: GOOGLE_APPLICATION_CREDENTIALS not set")
            return False
        
        PROJECT_ID = "digital-workshop-hub"
        
        SCOPES = [
            'https://www.googleapis.com/auth/cloud-platform',
            'https://www.googleapis.com/auth/firebase',
            'https://www.googleapis.com/auth/identitytoolkit'
        ]
        
        credentials = service_account.Credentials.from_service_account_file(
            creds_path,
            scopes=SCOPES
        )
        
        credentials.refresh(Request())
        
        headers = {
            'Authorization': f'Bearer {credentials.token}',
            'Content-Type': 'application/json'
        }
        
        # Check Google provider status
        url = f"https://identitytoolkit.googleapis.com/admin/v2/projects/{PROJECT_ID}/defaultSupportedIdpConfigs/google.com"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            config = response.json()
            enabled = config.get('enabled', False)
            client_id = config.get('clientId', '')
            
            print(f"  Provider exists: True")
            print(f"  Provider enabled: {enabled}")
            if client_id:
                print(f"  OAuth Client ID: {client_id[:30]}..." if len(client_id) > 30 else f"  OAuth Client ID: {client_id}")
            
            if enabled:
                print("  Google Sign-In Provider: OK")
                return True
            else:
                print("  Google Sign-In provider exists but is disabled")
                return False
        elif response.status_code == 404:
            print("  Provider exists: False")
            print("  Google Sign-In provider not configured")
            print(f"  Configure at: https://console.firebase.google.com/project/{PROJECT_ID}/authentication/providers")
            return False
        else:
            print(f"  Warning: Could not check provider status: {response.status_code}")
            return False
            
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
    google_provider_ok = verify_google_auth_provider()
    
    print()
    print("=" * 50)
    print("Summary:")
    print(f"  Google Auth (Service Account): {'OK' if google_ok else 'FAILED'}")
    print(f"  Firebase Admin SDK: {'OK' if firebase_ok else 'FAILED'}")
    print(f"  Google Sign-In Provider: {'OK' if google_provider_ok else 'NOT CONFIGURED'}")
    print("=" * 50)
    
    if google_ok and firebase_ok:
        if google_provider_ok:
            print("All checks passed!")
        else:
            print("Core checks passed. Google Sign-In provider needs configuration.")
            print("Run: python scripts/google_auth_setup.py")
        return 0
    else:
        print("Some checks failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
