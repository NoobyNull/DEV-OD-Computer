# DEV-OD-Computer

Devin development environment configuration for OD (Open Digital) projects.

## Zero-Touch Deployment

This repo supports fully automatic setup on new Devin sessions. Once configured, the setup runs automatically on login and skips if already completed.

### One-Time Setup

1. **Add the Devin secret** (in Devin settings):
   - **Secret Name**: `GOOGLE_SERVICE_ACCOUNT_JSON`
   - **Secret Value**: The entire contents of your service account JSON key file

2. **Enable auto-setup** (run once in any Devin session):
   ```bash
   echo '' >> ~/.bashrc
   echo '# DEV-OD-Computer auto-setup' >> ~/.bashrc
   echo 'if [ -f ~/repos/DEV-OD-Computer/scripts/auto_setup.sh ]; then ~/repos/DEV-OD-Computer/scripts/auto_setup.sh; fi' >> ~/.bashrc
   ```

That's it! Future sessions will automatically set up Firebase and be ready for editing.

### What Auto-Setup Does

The setup automatically:
1. Reads credentials from `GOOGLE_SERVICE_ACCOUNT_JSON` secret
2. Creates a secure credentials file at `~/.config/gcloud/digital-workshop-hub-credentials.json`
3. Verifies Google Auth and Firebase Admin SDK access
4. Downloads the Firebase project to `~/repos/digital-workshop-hub`
5. Downloads current Firestore and Storage rules
6. Creates a sentinel file to skip setup on subsequent runs

### Manual Setup (Alternative)

If you prefer to run setup manually:

```bash
python scripts/first_run_setup.py
```

After setup, you can edit files and deploy:
```bash
cd ~/repos/digital-workshop-hub
# Edit firestore.rules, storage.rules, etc.
firebase deploy --project digital-workshop-hub
```

## Prerequisites

- Python 3.x with `firebase-admin` and `google-auth` packages (auto-installed by setup script)
- Firebase CLI (`npm install -g firebase-tools`)
- Service account JSON key for the `digital-workshop-hub` project with **Firebase Admin** role

## Scripts

- `scripts/first_run_setup.py` - Automated first-run setup for new Devin sessions
- `scripts/verify_firebase.py` - Verify Firebase access is working
- `scripts/google_auth_setup.py` - Configure Google Sign-In authentication provider

## Google Authentication

The setup now includes verification and configuration of Google Sign-In as an authentication provider in Firebase.

### Automatic Verification

During first-run setup, the script automatically checks if Google Sign-In provider is configured. If not configured, it provides instructions on how to enable it.

### Manual Configuration

To configure Google Sign-In provider manually:

```bash
# Verify current status
python scripts/google_auth_setup.py --verify

# Configure with OAuth credentials
export GOOGLE_OAUTH_CLIENT_ID="your-client-id.apps.googleusercontent.com"
export GOOGLE_OAUTH_CLIENT_SECRET="your-client-secret"
python scripts/google_auth_setup.py
```

### Getting OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Select the `digital-workshop-hub` project
3. Create an OAuth 2.0 Client ID (Web application type)
4. Add authorized redirect URIs:
   - `https://digital-workshop-hub.firebaseapp.com/__/auth/handler`
   - `https://digital-workshop-hub.web.app/__/auth/handler`
5. Copy the Client ID and Client Secret

### Alternative: Firebase Console

You can also enable Google Sign-In directly in the Firebase Console:
1. Go to [Firebase Console Authentication](https://console.firebase.google.com/project/digital-workshop-hub/authentication/providers)
2. Click on "Google" provider
3. Enable it and save

### Using Google Sign-In in Your App

Once configured, users can sign in with Google using the Firebase SDK:

```javascript
import { getAuth, signInWithPopup, GoogleAuthProvider } from "firebase/auth";

const auth = getAuth();
const provider = new GoogleAuthProvider();

signInWithPopup(auth, provider)
  .then((result) => {
    const user = result.user;
    console.log("Signed in as:", user.email);
  })
  .catch((error) => {
    console.error("Sign-in error:", error);
  });
```

## Project Information

- **Firebase Project ID**: `digital-workshop-hub`
- **Service Account**: `digital-workshop-hub@appspot.gserviceaccount.com`
- **Hosting URL**: https://digital-workshop-hub.web.app

## Related Services

- AI Material Generator: `https://ai-material-mtl-generator-83803613015.us-west1.run.app/`
