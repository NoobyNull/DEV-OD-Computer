# DEV-OD-Computer

Devin development environment configuration for OD (Open Digital) projects.

## Quick Start - First Run Setup

When starting a new Devin session, simply run the first-run setup script:

```bash
python scripts/first_run_setup.py
```

The script will automatically:
1. Read credentials from `GOOGLE_SERVICE_ACCOUNT_JSON` secret (or `GOOGLE_APPLICATION_CREDENTIALS` file path)
2. Create a secure credentials file at `~/.config/gcloud/digital-workshop-hub-credentials.json`
3. Verify Google Auth and Firebase Admin SDK access
4. Download the Firebase project to `~/repos/digital-workshop-hub`
5. Download current Firestore and Storage rules
6. Set up the project ready for editing

After setup, you can edit files and deploy:
```bash
cd ~/repos/digital-workshop-hub
# Edit firestore.rules, storage.rules, etc.
firebase deploy --project digital-workshop-hub
```

## Devin Secret Setup (Recommended)

For automatic setup in new Devin sessions, add the service account JSON as a Devin secret:

1. **Secret Name**: `GOOGLE_SERVICE_ACCOUNT_JSON`
2. **Secret Value**: The entire contents of your service account JSON key file

The first-run script will automatically create a secure credentials file from this secret.

## Alternative: File-based Authentication

If you prefer to use a file path instead of a secret:

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
python scripts/first_run_setup.py
```

## Prerequisites

- Python 3.x with `firebase-admin` and `google-auth` packages (auto-installed by setup script)
- Firebase CLI (`npm install -g firebase-tools`)
- Service account JSON key for the `digital-workshop-hub` project with **Firebase Admin** role

## Scripts

- `scripts/first_run_setup.py` - Automated first-run setup for new Devin sessions
- `scripts/verify_firebase.py` - Verify Firebase access is working

## Project Information

- **Firebase Project ID**: `digital-workshop-hub`
- **Service Account**: `digital-workshop-hub@appspot.gserviceaccount.com`
- **Hosting URL**: https://digital-workshop-hub.web.app

## Related Services

- AI Material Generator: `https://ai-material-mtl-generator-83803613015.us-west1.run.app/`
