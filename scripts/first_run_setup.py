#!/usr/bin/env python3
"""
First Run Setup Script for Devin Sessions

This script automatically configures Firebase and Google Auth for new Devin sessions,
then downloads the Firebase project (digital-workshop-hub) ready for editing.

Credentials can be provided in two ways:
1. GOOGLE_SERVICE_ACCOUNT_JSON - Environment variable containing the JSON key content
2. GOOGLE_APPLICATION_CREDENTIALS - Path to an existing JSON key file

Usage:
    python scripts/first_run_setup.py
"""

import os
import sys
import json
import subprocess
import requests
import stat
from pathlib import Path


# Configuration
PROJECT_ID = "digital-workshop-hub"
FIREBASE_PROJECT_DIR = os.path.expanduser("~/repos/digital-workshop-hub")
CREDENTIALS_DIR = os.path.expanduser("~/.config/gcloud")
CREDENTIALS_FILE = os.path.join(CREDENTIALS_DIR, "digital-workshop-hub-credentials.json")
SENTINEL_DIR = os.path.expanduser("~/.config/dev-od-computer")
SENTINEL_FILE = os.path.join(SENTINEL_DIR, "setup_complete")


def setup_credentials_from_secret():
    """Create credentials file from GOOGLE_SERVICE_ACCOUNT_JSON secret."""
    json_content = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON')
    
    if not json_content:
        return None
    
    print("Found GOOGLE_SERVICE_ACCOUNT_JSON secret")
    
    try:
        # Validate JSON content
        creds_data = json.loads(json_content)
        
        # Verify it looks like a service account key
        required_fields = ['type', 'project_id', 'private_key', 'client_email']
        for field in required_fields:
            if field not in creds_data:
                print(f"ERROR: Invalid service account JSON - missing '{field}'")
                return None
        
        if creds_data.get('type') != 'service_account':
            print("ERROR: JSON is not a service account key")
            return None
        
        # Create credentials directory with secure permissions
        os.makedirs(CREDENTIALS_DIR, mode=0o700, exist_ok=True)
        
        # Write credentials file with secure permissions
        with open(CREDENTIALS_FILE, 'w') as f:
            json.dump(creds_data, f, indent=2)
        
        # Set file permissions to owner read/write only (600)
        os.chmod(CREDENTIALS_FILE, stat.S_IRUSR | stat.S_IWUSR)
        
        print(f"Created credentials file: {CREDENTIALS_FILE}")
        print(f"  Project ID: {creds_data.get('project_id')}")
        print(f"  Service Account: {creds_data.get('client_email')}")
        
        # Set environment variable for this session
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = CREDENTIALS_FILE
        
        return CREDENTIALS_FILE
        
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in GOOGLE_SERVICE_ACCOUNT_JSON: {e}")
        return None
    except Exception as e:
        print(f"ERROR: Could not create credentials file: {e}")
        return None


def check_credentials():
    """Check if Google credentials are configured."""
    print("=" * 50)
    print("Step 1: Checking Google Credentials")
    print("=" * 50)
    
    # First, try to set up credentials from the JSON secret
    creds_path = setup_credentials_from_secret()
    
    if creds_path:
        return creds_path
    
    # Fall back to GOOGLE_APPLICATION_CREDENTIALS environment variable
    creds_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    
    if not creds_path:
        print("ERROR: No credentials found")
        print("\nTo fix this, set one of the following:")
        print("1. GOOGLE_SERVICE_ACCOUNT_JSON - The JSON content of your service account key")
        print("   (Recommended for Devin secrets)")
        print("2. GOOGLE_APPLICATION_CREDENTIALS - Path to your service account JSON file")
        return None
    
    if not os.path.exists(creds_path):
        print(f"ERROR: Credentials file not found: {creds_path}")
        return None
    
    print(f"Credentials file found: {creds_path}")
    return creds_path


def verify_google_auth(creds_path):
    """Verify Google Auth is working."""
    print("\n" + "=" * 50)
    print("Step 2: Verifying Google Auth")
    print("=" * 50)
    
    try:
        from google.oauth2 import service_account
        from google.auth.transport.requests import Request
        
        SCOPES = [
            'https://www.googleapis.com/auth/cloud-platform',
            'https://www.googleapis.com/auth/firebase'
        ]
        
        credentials = service_account.Credentials.from_service_account_file(
            creds_path,
            scopes=SCOPES
        )
        
        print(f"Service Account: {credentials.service_account_email}")
        print(f"Project ID: {credentials.project_id}")
        
        credentials.refresh(Request())
        print(f"Token valid: {credentials.valid}")
        print("Google Auth: OK")
        return credentials
        
    except ImportError:
        print("ERROR: google-auth package not installed")
        print("Installing required packages...")
        subprocess.run([sys.executable, "-m", "pip", "install", "google-auth", "google-auth-oauthlib", "requests", "-q"])
        return verify_google_auth(creds_path)
    except Exception as e:
        print(f"ERROR: {e}")
        return None


def verify_firebase_admin(creds_path):
    """Verify Firebase Admin SDK is working."""
    print("\n" + "=" * 50)
    print("Step 3: Verifying Firebase Admin SDK")
    print("=" * 50)
    
    try:
        import firebase_admin
        from firebase_admin import credentials, auth
        
        # Clean up any existing app
        try:
            firebase_admin.delete_app(firebase_admin.get_app())
        except:
            pass
        
        cred = credentials.Certificate(creds_path)
        app = firebase_admin.initialize_app(cred)
        
        print(f"App name: {app.name}")
        print(f"Project ID: {app.project_id}")
        
        # Test Firebase Auth access
        page = auth.list_users()
        user_count = len(list(page.users))
        print(f"Users found: {user_count}")
        print("Firebase Admin SDK: OK")
        return True
        
    except ImportError:
        print("ERROR: firebase-admin package not installed")
        print("Installing required packages...")
        subprocess.run([sys.executable, "-m", "pip", "install", "firebase-admin", "-q"])
        return verify_firebase_admin(creds_path)
    except Exception as e:
        print(f"ERROR: {e}")
        print("Firebase Admin SDK may need additional IAM permissions")
        return False


def download_firebase_rules(credentials, project_dir):
    """Download Firestore and Storage rules from Firebase."""
    print("\n" + "=" * 50)
    print("Step 4: Downloading Firebase Rules")
    print("=" * 50)
    
    from google.auth.transport.requests import Request
    
    # Refresh credentials if needed
    if not credentials.valid:
        credentials.refresh(Request())
    
    headers = {'Authorization': f'Bearer {credentials.token}'}
    
    # Get releases to find current rulesets
    releases_url = f"https://firebaserules.googleapis.com/v1/projects/{PROJECT_ID}/releases"
    response = requests.get(releases_url, headers=headers)
    
    if response.status_code != 200:
        print(f"ERROR: Could not fetch releases: {response.status_code}")
        return False
    
    releases = response.json().get('releases', [])
    
    for release in releases:
        release_name = release.get('name', '')
        ruleset_name = release.get('rulesetName', '')
        
        if not ruleset_name:
            continue
        
        # Fetch the ruleset content
        ruleset_url = f"https://firebaserules.googleapis.com/v1/{ruleset_name}"
        ruleset_response = requests.get(ruleset_url, headers=headers)
        
        if ruleset_response.status_code != 200:
            continue
        
        ruleset = ruleset_response.json()
        
        if 'source' in ruleset and 'files' in ruleset['source']:
            for f in ruleset['source']['files']:
                filename = f.get('name', '')
                content = f.get('content', '')
                
                if 'firestore' in release_name.lower() or 'firestore' in filename.lower():
                    filepath = os.path.join(project_dir, 'firestore.rules')
                    with open(filepath, 'w') as outfile:
                        outfile.write(content)
                    print(f"Downloaded: firestore.rules")
                
                elif 'storage' in release_name.lower() or 'storage' in filename.lower():
                    filepath = os.path.join(project_dir, 'storage.rules')
                    with open(filepath, 'w') as outfile:
                        outfile.write(content)
                    print(f"Downloaded: storage.rules")
    
    return True


def setup_firebase_project(project_dir):
    """Set up the Firebase project directory with configuration files."""
    print("\n" + "=" * 50)
    print("Step 5: Setting Up Firebase Project Directory")
    print("=" * 50)
    
    # Create project directory
    os.makedirs(project_dir, exist_ok=True)
    print(f"Project directory: {project_dir}")
    
    # Create firebase.json
    firebase_config = {
        "firestore": {
            "rules": "firestore.rules",
            "indexes": "firestore.indexes.json"
        },
        "hosting": {
            "public": "public",
            "ignore": [
                "firebase.json",
                "**/.*",
                "**/node_modules/**"
            ]
        },
        "storage": {
            "rules": "storage.rules"
        }
    }
    
    with open(os.path.join(project_dir, 'firebase.json'), 'w') as f:
        json.dump(firebase_config, f, indent=2)
    print("Created: firebase.json")
    
    # Create .firebaserc
    firebaserc = {
        "projects": {
            "default": PROJECT_ID
        }
    }
    
    with open(os.path.join(project_dir, '.firebaserc'), 'w') as f:
        json.dump(firebaserc, f, indent=2)
    print("Created: .firebaserc")
    
    # Create empty indexes file
    indexes = {"indexes": [], "fieldOverrides": []}
    with open(os.path.join(project_dir, 'firestore.indexes.json'), 'w') as f:
        json.dump(indexes, f, indent=2)
    print("Created: firestore.indexes.json")
    
    # Create public directory for hosting
    os.makedirs(os.path.join(project_dir, 'public'), exist_ok=True)
    print("Created: public/")
    
    return True


def create_sentinel_file(creds_path):
    """Create sentinel file to mark setup as complete."""
    try:
        os.makedirs(SENTINEL_DIR, mode=0o700, exist_ok=True)
        
        # Read credentials to get metadata
        with open(creds_path, 'r') as f:
            creds_data = json.load(f)
        
        sentinel_data = {
            "setup_complete": True,
            "project_id": creds_data.get('project_id'),
            "client_email": creds_data.get('client_email'),
            "private_key_id": creds_data.get('private_key_id'),
            "credentials_file": CREDENTIALS_FILE,
            "firebase_project_dir": FIREBASE_PROJECT_DIR,
            "setup_timestamp": subprocess.check_output(['date', '-Iseconds']).decode().strip()
        }
        
        with open(SENTINEL_FILE, 'w') as f:
            json.dump(sentinel_data, f, indent=2)
        
        os.chmod(SENTINEL_FILE, stat.S_IRUSR | stat.S_IWUSR)
        return True
    except Exception as e:
        print(f"Warning: Could not create sentinel file: {e}")
        return False


def verify_google_auth_provider(credentials):
    """Verify Google Sign-In provider is configured in Firebase Auth."""
    print("\n" + "=" * 50)
    print("Step 6: Verifying Google Sign-In Provider")
    print("=" * 50)
    
    from google.auth.transport.requests import Request
    
    # Refresh credentials if needed
    if not credentials.valid:
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
        
        print(f"Google Sign-In provider: {'Enabled' if enabled else 'Disabled'}")
        if client_id:
            print(f"OAuth Client ID: {client_id[:30]}..." if len(client_id) > 30 else f"OAuth Client ID: {client_id}")
        
        if enabled:
            print("Google Sign-In: OK")
            return True
        else:
            print("Google Sign-In provider exists but is disabled")
            print(f"Enable it at: https://console.firebase.google.com/project/{PROJECT_ID}/authentication/providers")
            return False
    elif response.status_code == 404:
        print("Google Sign-In provider: Not configured")
        print(f"\nTo enable Google Sign-In:")
        print(f"  1. Go to Firebase Console: https://console.firebase.google.com/project/{PROJECT_ID}/authentication/providers")
        print("  2. Click on 'Google' provider")
        print("  3. Enable it and configure OAuth settings")
        print("\nOr run: python scripts/google_auth_setup.py")
        return False
    else:
        print(f"Warning: Could not check Google provider status: {response.status_code}")
        return False


def verify_firebase_cli():
    """Verify Firebase CLI is installed and working."""
    print("\n" + "=" * 50)
    print("Step 7: Verifying Firebase CLI")
    print("=" * 50)
    
    try:
        result = subprocess.run(
            ['firebase', '--version'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"Firebase CLI version: {result.stdout.strip()}")
            return True
        else:
            print("Firebase CLI not working properly")
            return False
    except FileNotFoundError:
        print("Firebase CLI not installed")
        print("Installing Firebase CLI...")
        subprocess.run(['npm', 'install', '-g', 'firebase-tools'], capture_output=True)
        return verify_firebase_cli()


def main():
    print("=" * 50)
    print("DEV-OD-Computer First Run Setup")
    print("=" * 50)
    print(f"\nThis script will configure Firebase for project: {PROJECT_ID}")
    print(f"Firebase project will be downloaded to: {FIREBASE_PROJECT_DIR}")
    print()
    
    # Step 1: Check credentials
    creds_path = check_credentials()
    if not creds_path:
        print("\n[FAILED] Setup cannot continue without credentials")
        return 1
    
    # Step 2: Verify Google Auth
    credentials = verify_google_auth(creds_path)
    if not credentials:
        print("\n[FAILED] Google Auth verification failed")
        return 1
    
    # Step 3: Verify Firebase Admin SDK
    firebase_ok = verify_firebase_admin(creds_path)
    if not firebase_ok:
        print("\n[WARNING] Firebase Admin SDK verification failed")
        print("Some features may not work. Consider adding Firebase Admin role to the service account.")
    
    # Step 4: Set up Firebase project directory
    if not setup_firebase_project(FIREBASE_PROJECT_DIR):
        print("\n[FAILED] Could not set up Firebase project directory")
        return 1
    
    # Step 5: Download Firebase rules
    if not download_firebase_rules(credentials, FIREBASE_PROJECT_DIR):
        print("\n[WARNING] Could not download Firebase rules")
    
    # Step 6: Verify Google Sign-In provider
    google_auth_ok = verify_google_auth_provider(credentials)
    if not google_auth_ok:
        print("\n[INFO] Google Sign-In provider not configured")
        print("Run 'python scripts/google_auth_setup.py' to configure it")
    
    # Step 7: Verify Firebase CLI
    verify_firebase_cli()
    
    # Step 8: Create sentinel file to mark setup complete
    create_sentinel_file(creds_path)
    
    # Summary
    print("\n" + "=" * 50)
    print("Setup Complete!")
    print("=" * 50)
    print(f"\nFirebase project ready at: {FIREBASE_PROJECT_DIR}")
    print("\nYou can now:")
    print(f"  1. cd {FIREBASE_PROJECT_DIR}")
    print("  2. Edit firestore.rules, storage.rules, etc.")
    print(f"  3. Deploy with: firebase deploy --project {PROJECT_ID}")
    print("\nRelated services:")
    print("  - AI Material Generator: https://ai-material-mtl-generator-83803613015.us-west1.run.app/")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
