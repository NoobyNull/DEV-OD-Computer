#!/usr/bin/env python3
"""
Google Authentication Setup Script for Firebase

This script configures Google Sign-In as an authentication provider in Firebase.
It uses the Firebase Identity Toolkit API to enable and configure the Google provider.

Prerequisites:
- Service account with Firebase Admin role
- GOOGLE_APPLICATION_CREDENTIALS environment variable set
- Optional: GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET for custom OAuth config

Usage:
    python scripts/google_auth_setup.py
    
    # With custom OAuth credentials:
    export GOOGLE_OAUTH_CLIENT_ID="your-client-id.apps.googleusercontent.com"
    export GOOGLE_OAUTH_CLIENT_SECRET="your-client-secret"
    python scripts/google_auth_setup.py
"""

import os
import sys
import json
import requests
from typing import Optional, Dict, Any


PROJECT_ID = "digital-workshop-hub"


def get_access_token() -> Optional[str]:
    """Get an access token using the service account credentials."""
    try:
        from google.oauth2 import service_account
        from google.auth.transport.requests import Request
        
        creds_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path:
            print("ERROR: GOOGLE_APPLICATION_CREDENTIALS not set")
            return None
        
        if not os.path.exists(creds_path):
            print(f"ERROR: Credentials file not found: {creds_path}")
            return None
        
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
        return credentials.token
        
    except ImportError:
        print("ERROR: google-auth package not installed")
        print("Run: pip install google-auth google-auth-oauthlib")
        return None
    except Exception as e:
        print(f"ERROR: Could not get access token: {e}")
        return None


def get_identity_config(token: str) -> Optional[Dict[str, Any]]:
    """Get the current Identity Platform configuration."""
    url = f"https://identitytoolkit.googleapis.com/v2/projects/{PROJECT_ID}/config"
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 404:
        print("Identity Platform not yet configured for this project")
        return {}
    else:
        print(f"ERROR: Could not get Identity config: {response.status_code}")
        print(response.text)
        return None


def get_auth_providers(token: str) -> Optional[Dict[str, Any]]:
    """Get the current authentication providers configuration."""
    url = f"https://identitytoolkit.googleapis.com/admin/v2/projects/{PROJECT_ID}/defaultSupportedIdpConfigs"
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Note: Could not get IdP configs: {response.status_code}")
        return {}


def check_google_provider_status(token: str) -> Dict[str, Any]:
    """Check if Google Sign-In provider is enabled."""
    url = f"https://identitytoolkit.googleapis.com/admin/v2/projects/{PROJECT_ID}/defaultSupportedIdpConfigs/google.com"
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        config = response.json()
        return {
            'exists': True,
            'enabled': config.get('enabled', False),
            'client_id': config.get('clientId', ''),
            'config': config
        }
    elif response.status_code == 404:
        return {
            'exists': False,
            'enabled': False,
            'client_id': '',
            'config': {}
        }
    else:
        print(f"Warning: Could not check Google provider: {response.status_code}")
        return {
            'exists': False,
            'enabled': False,
            'client_id': '',
            'error': response.text
        }


def enable_google_provider(token: str, client_id: Optional[str] = None, 
                          client_secret: Optional[str] = None) -> bool:
    """Enable Google Sign-In provider in Firebase Auth."""
    
    # Check current status
    status = check_google_provider_status(token)
    
    if status.get('enabled') and not client_id:
        print("Google Sign-In provider is already enabled")
        if status.get('client_id'):
            print(f"  Client ID: {status['client_id'][:20]}...")
        return True
    
    # Get OAuth credentials from environment if not provided
    if not client_id:
        client_id = os.environ.get('GOOGLE_OAUTH_CLIENT_ID')
    if not client_secret:
        client_secret = os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        print("\nTo enable Google Sign-In with custom OAuth credentials:")
        print("  1. Go to Google Cloud Console > APIs & Services > Credentials")
        print("  2. Create an OAuth 2.0 Client ID (Web application)")
        print("  3. Set the following environment variables:")
        print("     export GOOGLE_OAUTH_CLIENT_ID='your-client-id'")
        print("     export GOOGLE_OAUTH_CLIENT_SECRET='your-client-secret'")
        print("\nAlternatively, enable Google Sign-In in Firebase Console:")
        print(f"  https://console.firebase.google.com/project/{PROJECT_ID}/authentication/providers")
        
        if status.get('exists'):
            print("\nNote: Google provider exists but may need OAuth configuration")
            return True
        return False
    
    # Prepare the configuration
    config = {
        'enabled': True,
        'clientId': client_id,
        'clientSecret': client_secret
    }
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    if status.get('exists'):
        # Update existing configuration
        url = f"https://identitytoolkit.googleapis.com/admin/v2/projects/{PROJECT_ID}/defaultSupportedIdpConfigs/google.com"
        response = requests.patch(url, headers=headers, json=config)
    else:
        # Create new configuration
        url = f"https://identitytoolkit.googleapis.com/admin/v2/projects/{PROJECT_ID}/defaultSupportedIdpConfigs?idpId=google.com"
        response = requests.post(url, headers=headers, json=config)
    
    if response.status_code in [200, 201]:
        print("Google Sign-In provider enabled successfully!")
        return True
    else:
        print(f"ERROR: Could not enable Google provider: {response.status_code}")
        print(response.text)
        return False


def verify_google_auth_setup() -> bool:
    """Verify that Google authentication is properly configured."""
    print("=" * 50)
    print("Google Authentication Setup Verification")
    print("=" * 50)
    print()
    
    # Get access token
    print("Step 1: Getting access token...")
    token = get_access_token()
    if not token:
        return False
    print("  Access token: OK")
    
    # Check Identity Platform config
    print("\nStep 2: Checking Identity Platform configuration...")
    config = get_identity_config(token)
    if config is None:
        return False
    
    if config:
        print(f"  Project: {PROJECT_ID}")
        if 'signIn' in config:
            sign_in = config['signIn']
            print(f"  Email sign-in enabled: {sign_in.get('email', {}).get('enabled', False)}")
            print(f"  Anonymous sign-in enabled: {sign_in.get('anonymous', {}).get('enabled', False)}")
    
    # Check Google provider status
    print("\nStep 3: Checking Google Sign-In provider...")
    status = check_google_provider_status(token)
    
    if status.get('error'):
        print(f"  Warning: {status['error']}")
    
    print(f"  Provider exists: {status.get('exists', False)}")
    print(f"  Provider enabled: {status.get('enabled', False)}")
    
    if status.get('client_id'):
        client_id = status['client_id']
        print(f"  OAuth Client ID: {client_id[:30]}..." if len(client_id) > 30 else f"  OAuth Client ID: {client_id}")
    
    return status.get('enabled', False) or status.get('exists', False)


def setup_google_auth() -> bool:
    """Main function to set up Google authentication."""
    print("=" * 50)
    print("Google Authentication Setup")
    print("=" * 50)
    print(f"\nProject: {PROJECT_ID}")
    print()
    
    # Get access token
    print("Getting access token...")
    token = get_access_token()
    if not token:
        print("\n[FAILED] Could not get access token")
        return False
    print("  OK")
    
    # Check and enable Google provider
    print("\nConfiguring Google Sign-In provider...")
    success = enable_google_provider(token)
    
    if success:
        print("\n" + "=" * 50)
        print("Google Authentication Setup Complete!")
        print("=" * 50)
        print(f"\nUsers can now sign in with Google at:")
        print(f"  https://{PROJECT_ID}.firebaseapp.com")
        print(f"  https://{PROJECT_ID}.web.app")
        print("\nTo use Google Sign-In in your app:")
        print("  1. Add Firebase SDK to your web app")
        print("  2. Use firebase.auth().signInWithPopup(new firebase.auth.GoogleAuthProvider())")
        print("  3. Or use signInWithRedirect() for mobile-friendly flow")
    
    return success


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Google Authentication Setup for Firebase')
    parser.add_argument('--verify', action='store_true', 
                       help='Only verify current configuration, do not make changes')
    parser.add_argument('--client-id', type=str,
                       help='OAuth Client ID (or set GOOGLE_OAUTH_CLIENT_ID env var)')
    parser.add_argument('--client-secret', type=str,
                       help='OAuth Client Secret (or set GOOGLE_OAUTH_CLIENT_SECRET env var)')
    
    args = parser.parse_args()
    
    if args.verify:
        success = verify_google_auth_setup()
    else:
        # Set credentials from args if provided
        if args.client_id:
            os.environ['GOOGLE_OAUTH_CLIENT_ID'] = args.client_id
        if args.client_secret:
            os.environ['GOOGLE_OAUTH_CLIENT_SECRET'] = args.client_secret
        
        success = setup_google_auth()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
