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

## Project Information

- **Firebase Project ID**: `digital-workshop-hub`
- **Service Account**: `digital-workshop-hub@appspot.gserviceaccount.com`
- **Hosting URL**: https://digital-workshop-hub.web.app

## Related Services

- AI Material Generator: `https://ai-material-mtl-generator-83803613015.us-west1.run.app/`
