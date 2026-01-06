# DEV-OD-Computer

Devin development environment configuration for OD (Open Digital) projects.

## Quick Start - First Run Setup

When starting a new Devin session, run the first-run setup script to automatically configure Firebase and download the project:

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/digital-workshop-hub-service-account.json"
python scripts/first_run_setup.py
```

This will:
1. Verify Google Auth credentials
2. Verify Firebase Admin SDK access
3. Download the Firebase project to `~/repos/digital-workshop-hub`
4. Download current Firestore and Storage rules
5. Set up the project ready for editing

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

## Authentication

For non-interactive authentication (recommended for Devin/CI), use a service account:

1. Obtain a service account JSON key from the `digital-workshop-hub` GCP project
2. The service account needs the **Firebase Admin** role in IAM
3. Set the environment variable:
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
   ```

## Devin Session Setup

For new Devin sessions, ensure the following secrets are configured:
- `GOOGLE_APPLICATION_CREDENTIALS` - Path to the service account JSON key file

## Scripts

- `scripts/first_run_setup.py` - Automated first-run setup for new Devin sessions
- `scripts/verify_firebase.py` - Verify Firebase access is working

## Project Information

- **Firebase Project ID**: `digital-workshop-hub`
- **Service Account**: `digital-workshop-hub@appspot.gserviceaccount.com`
- **Hosting URL**: https://digital-workshop-hub.web.app

## Related Services

- AI Material Generator: `https://ai-material-mtl-generator-83803613015.us-west1.run.app/`
