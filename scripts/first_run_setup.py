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
    creds_value = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    
    if not creds_value:
        print("ERROR: No credentials found")
        print("\nTo fix this, set one of the following:")
        print("1. GOOGLE_SERVICE_ACCOUNT_JSON - The JSON content of your service account key")
        print("   (Recommended for Devin secrets)")
        print("2. GOOGLE_APPLICATION_CREDENTIALS - Path to your service account JSON file")
        return None
    
    # Check if GOOGLE_APPLICATION_CREDENTIALS contains JSON content directly
    # (instead of a file path)
    creds_value_stripped = creds_value.strip()
    if creds_value_stripped.startswith('{'):
        print("Found JSON content in GOOGLE_APPLICATION_CREDENTIALS")
        try:
            creds_data = json.loads(creds_value_stripped)
            
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
            
            # Update environment variable to point to the file
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = CREDENTIALS_FILE
            
            return CREDENTIALS_FILE
            
        except json.JSONDecodeError as e:
            print(f"ERROR: Invalid JSON in GOOGLE_APPLICATION_CREDENTIALS: {e}")
            return None
        except Exception as e:
            print(f"ERROR: Could not create credentials file: {e}")
            return None
    
    # It's a file path
    if not os.path.exists(creds_value):
        print(f"ERROR: Credentials file not found: {creds_value}")
        return None
    
    print(f"Credentials file found: {creds_value}")
    return creds_value


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
    
    # Create Google OAuth login page
    create_google_login_page(project_dir)
    
    return True


def create_google_login_page(project_dir):
    """Create a Google OAuth login page for Firebase Auth."""
    public_dir = os.path.join(project_dir, 'public')
    
    # Create index.html with Google Sign-In
    index_html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Digital Workshop Hub - Login</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .login-container {
            background: white;
            padding: 40px;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            text-align: center;
            max-width: 400px;
            width: 90%;
        }
        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 24px;
        }
        .subtitle {
            color: #666;
            margin-bottom: 30px;
            font-size: 14px;
        }
        .google-btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 12px;
            background: #fff;
            border: 2px solid #ddd;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 500;
            color: #333;
            transition: all 0.3s ease;
            width: 100%;
        }
        .google-btn:hover {
            border-color: #4285f4;
            box-shadow: 0 4px 12px rgba(66, 133, 244, 0.3);
        }
        .google-btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        .google-icon {
            width: 20px;
            height: 20px;
        }
        .user-info {
            display: none;
            text-align: left;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
            margin-top: 20px;
        }
        .user-info.show {
            display: block;
        }
        .user-info img {
            width: 60px;
            height: 60px;
            border-radius: 50%;
            margin-bottom: 10px;
        }
        .user-info h3 {
            color: #333;
            margin-bottom: 5px;
        }
        .user-info p {
            color: #666;
            font-size: 14px;
            margin-bottom: 15px;
        }
        .sign-out-btn {
            background: #dc3545;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            transition: background 0.3s ease;
        }
        .sign-out-btn:hover {
            background: #c82333;
        }
        .status {
            margin-top: 20px;
            padding: 10px;
            border-radius: 6px;
            font-size: 14px;
        }
        .status.error {
            background: #f8d7da;
            color: #721c24;
        }
        .status.success {
            background: #d4edda;
            color: #155724;
        }
        .status.info {
            background: #cce5ff;
            color: #004085;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <h1>Digital Workshop Hub</h1>
        <p class="subtitle">Sign in to access your workspace</p>
        
        <button id="googleSignIn" class="google-btn">
            <svg class="google-icon" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            Sign in with Google
        </button>
        
        <div id="userInfo" class="user-info">
            <img id="userPhoto" src="" alt="Profile">
            <h3 id="userName"></h3>
            <p id="userEmail"></p>
            <button id="signOut" class="sign-out-btn">Sign Out</button>
        </div>
        
        <div id="status" class="status" style="display: none;"></div>
    </div>

    <script type="module">
        import { initializeApp } from 'https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js';
        import { getAuth, signInWithPopup, signOut, onAuthStateChanged, GoogleAuthProvider } from 'https://www.gstatic.com/firebasejs/10.7.1/firebase-auth.js';

        // Firebase configuration for digital-workshop-hub
        const firebaseConfig = {
            apiKey: "AIzaSyBxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            authDomain: "digital-workshop-hub.firebaseapp.com",
            projectId: "digital-workshop-hub",
            storageBucket: "digital-workshop-hub.appspot.com",
            messagingSenderId: "000000000000",
            appId: "1:000000000000:web:xxxxxxxxxxxxxxxx"
        };

        // Initialize Firebase
        const app = initializeApp(firebaseConfig);
        const auth = getAuth(app);
        const provider = new GoogleAuthProvider();

        // DOM elements
        const googleSignInBtn = document.getElementById('googleSignIn');
        const userInfoDiv = document.getElementById('userInfo');
        const userPhoto = document.getElementById('userPhoto');
        const userName = document.getElementById('userName');
        const userEmail = document.getElementById('userEmail');
        const signOutBtn = document.getElementById('signOut');
        const statusDiv = document.getElementById('status');

        function showStatus(message, type) {
            statusDiv.textContent = message;
            statusDiv.className = 'status ' + type;
            statusDiv.style.display = 'block';
            if (type === 'success') {
                setTimeout(() => { statusDiv.style.display = 'none'; }, 3000);
            }
        }

        function updateUI(user) {
            if (user) {
                googleSignInBtn.style.display = 'none';
                userInfoDiv.classList.add('show');
                userPhoto.src = user.photoURL || 'https://via.placeholder.com/60';
                userName.textContent = user.displayName || 'User';
                userEmail.textContent = user.email;
                showStatus('Signed in successfully!', 'success');
            } else {
                googleSignInBtn.style.display = 'flex';
                userInfoDiv.classList.remove('show');
            }
        }

        // Listen for auth state changes
        onAuthStateChanged(auth, (user) => {
            updateUI(user);
        });

        // Google Sign-In
        googleSignInBtn.addEventListener('click', async () => {
            googleSignInBtn.disabled = true;
            try {
                const result = await signInWithPopup(auth, provider);
                const credential = GoogleAuthProvider.credentialFromResult(result);
                const token = credential.accessToken;
                const user = result.user;
                console.log('Signed in:', user.email);
            } catch (error) {
                console.error('Sign-in error:', error);
                showStatus('Sign-in failed: ' + error.message, 'error');
            } finally {
                googleSignInBtn.disabled = false;
            }
        });

        // Sign Out
        signOutBtn.addEventListener('click', async () => {
            try {
                await signOut(auth);
                showStatus('Signed out successfully', 'info');
            } catch (error) {
                console.error('Sign-out error:', error);
                showStatus('Sign-out failed: ' + error.message, 'error');
            }
        });
    </script>
</body>
</html>
'''
    
    with open(os.path.join(public_dir, 'index.html'), 'w') as f:
        f.write(index_html)
    print("Created: public/index.html (Google OAuth login page)")


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
