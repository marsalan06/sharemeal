# Cloud Run Deployment Guide

Step-by-step guide to deploy ShareMeal backend to Google Cloud Run using Docker.

---

## Prerequisites

**Note:** Cloud Run is just the hosting platform. Your backend still needs these services:

1. ✅ **Google Cloud account** with billing enabled
2. ✅ **Google OAuth Client ID** - Required because:
   - Your backend uses Google OAuth to validate authentication tokens
   - Flutter app authenticates users via Google Sign-In
   - Backend validates those tokens using Google's tokeninfo API (see `auth.py`)
   - Get from: [Google Cloud Console](https://console.cloud.google.com/apis/credentials) → Create OAuth 2.0 Client ID
3. ✅ **MongoDB Atlas cluster** - Required because:
   - All data (food items, requests, users) is stored in MongoDB Atlas
   - Backend connects to MongoDB, not a local database (see `database.py`)
4. ✅ **Google Cloud CLI** installed (`gcloud`)
5. ✅ **Docker** installed (for local testing)

**Optional:** Firebase project (only for FCM push notifications - FCM is Google Cloud's push notification service)

---

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **"Open Project Picker"** (or press `Ctrl+O` / `Cmd+O`)
3. Click **"New Project"**
4. Enter project name: `sharemeal-backend` (or your choice)
5. Click **"Create"**

## Step 2: Enable Required APIs

1. Make sure your new project is selected
2. Enable these APIs:
   - **Cloud Run API**
   - **Cloud Build API**
   - **Artifact Registry API** (for Docker images)

You can enable via:
- **GUI**: Go to [API Library](https://console.cloud.google.com/apis/library)
- **CLI**: `gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com`

## Step 3: Install Google Cloud CLI

Install `gcloud` CLI for your operating system:
- **macOS**: `brew install google-cloud-sdk`
- **Linux**: Follow [official guide](https://cloud.google.com/sdk/docs/install)
- **Windows**: Download installer from [official site](https://cloud.google.com/sdk/docs/install)

## Step 4: Set Default Project

```bash
# List all projects
gcloud projects list

# Set your project
gcloud config set project YOUR_PROJECT_ID
```

## Step 5: Prepare Environment Variables

### Create `.env` file (for local development):

```bash
cd backend
cp .env.example .env
```

Edit `.env` with your values:
```env
MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/sharemeal?retryWrites=true&w=majority
PORT=8000  # Local dev only (Cloud Run uses 8080 automatically)
```

**Note:** For Cloud Run, we'll set environment variables via GUI or `gcloud` command (see Step 9).

---

## Step 6: Create Artifact Registry Repository

We need a repository to store our Docker images.

### Option A: Using GUI (Recommended)
1. Go to [Artifact Registry](https://console.cloud.google.com/artifacts)
2. Click **"Create Repository"**
3. Fill in:
   - **Name**: `sharemeal-repo` (or your choice)
   - **Format**: Docker
   - **Location**: Choose region (e.g., `us-central1`, `asia-south1`)
   - **Description**: "Docker images for ShareMeal backend"
4. Click **"Create"**

### Option B: Using CLI

```bash
gcloud artifacts repositories create sharemeal-repo \
  --repository-format=docker \
  --location=us-central1 \
  --description="Docker images for ShareMeal backend" \
  --immutable-tags
```

**Note:** Replace `us-central1` with your preferred region.

---

## Step 7: Configure Docker Authentication

This allows pushing images without authenticating each time:

```bash
# Replace REGION_NAME with your Artifact Registry region
gcloud auth configure-docker REGION_NAME-docker.pkg.dev
```

Example:
```bash
gcloud auth configure-docker us-central1-docker.pkg.dev
```

---

## Step 8: Test Docker Build Locally (Optional)

```bash
cd backend

# Build Docker image
docker build -t sharemeal-backend .

# Test locally
docker run -p 8080:8080 \
  -e MONGODB_URL="your_mongodb_url" \
  -e PORT=8080 \
  sharemeal-backend

# Test health check
curl http://localhost:8080/health

# Access API documentation
# Swagger UI: http://localhost:8080/docs
# ReDoc: http://localhost:8080/redoc
```

---

## Testing the API

### Access Swagger Documentation

Once your server is running, visit:
- **Swagger UI**: http://localhost:8000/docs (or http://localhost:8080/docs if using Docker)
- **ReDoc**: http://localhost:8000/redoc

### Getting a Google OAuth Token for Testing

Since we use Google OAuth (no login endpoint), you need a Google ID token to test:

**Option 1: Use Google OAuth Playground**
gcloud auth print-identity-token



1. Go to https://developers.google.com/oauthplayground/
2. Select "Google OAuth2 API v2"
3. Check "https://www.googleapis.com/auth/userinfo.email" and "https://www.googleapis.com/auth/userinfo.profile"
4. Click "Authorize APIs"
5. Sign in with Google
6. Click "Exchange authorization code for tokens"
7. Copy the `id_token` value

**Option 2: Use Flutter App**
- Sign in with Google in your Flutter app
- Get the ID token: `await GoogleSignIn().signIn()` then get the ID token
- Use that token in the `Authorization: Bearer <token>` header

**Option 3: Test with curl**
```bash
# Replace YOUR_GOOGLE_ID_TOKEN with token from above
curl -H "Authorization: Bearer YOUR_GOOGLE_ID_TOKEN" \
  http://localhost:8000/user

# Or test food endpoint
curl -H "Authorization: Bearer YOUR_GOOGLE_ID_TOKEN" \
  http://localhost:8000/food
```

**Option 4: Use Swagger UI**
1. Go to http://localhost:8000/docs
2. Click the **"Authorize"** button (🔒 lock icon at top right)
3. In the "Value" field, enter **ONLY your token** (without "Bearer")
   - **Important:** Do NOT include "Bearer" - Swagger UI adds it automatically
   - Example: `eyJhbGciOiJSUzI1NiIsImtpZCI6IjkzYTkzNThjY2Y5OWYxYmIwNDBiYzYyMjFkNTQ5M2UxZmZkOGFkYTEiLCJ0eXAiOiJKV1QifQ...`
4. Click **"Authorize"**
5. Click **"Close"**
6. Now all requests will include the Authorization header automatically
7. Test endpoints by clicking "Try it out" → "Execute"

**Note:** If you see "Authorization header missing", make sure:
- You clicked the "Authorize" button (not just typed in a field)
- You did NOT include "Bearer" - just paste the token directly
- The token hasn't expired (Google tokens expire after 1 hour)
```

---

## Step 9: Create Service Account (If Not Exists)

```bash
# Create service account
gcloud iam service-accounts create sharemeal-backend \
  --display-name="ShareMeal Backend Service Account"

# Grant Cloud Run Invoker (if needed)
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:sharemeal-backend@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.invoker"
```

**Note:** If using FCM for push notifications, you may need Firebase Admin permissions:
```bash
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:sharemeal-backend@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/firebase.admin"
```
Otherwise, no special permissions needed for Google OAuth.

---

## Step 10: Build and Push Docker Image

**Important:** Make sure you're in the `backend` directory where `Dockerfile` is located.

```bash
cd backend

# Build and push to Artifact Registry
gcloud builds submit --tag REGION_NAME-docker.pkg.dev/PROJECT_ID/REPOSITORY_NAME/IMAGE_NAME:IMAGE_TAG
```

**Example:**
```bash
gcloud builds submit --tag us-central1-docker.pkg.dev/sharemeal-project/sharemeal-repo/sharemeal-backend:latest
```

### ⚠️ Common Error: Storage Permission Denied

If you see this error:
```
ERROR: (gcloud.builds.submit) INVALID_ARGUMENT: could not resolve source: 
googleapi: Error 403: ... does not have storage.objects.get access
```

**Fix:**
1. Go to [IAM & Admin](https://console.cloud.google.com/iam-admin/iam)
2. Find the principal named **"Default compute service account"** (ends with `@developer.gserviceaccount.com`)
3. Click **Edit** (pencil icon)
4. Add role: **Storage Object Viewer**
5. Click **Save**
6. Run the build command again

---

## Step 11: Deploy to Cloud Run

### Option A: Using GUI (Easier for first-time setup)

1. Go to [Cloud Run](https://console.cloud.google.com/run)
2. Click **"Create Service"**
3. Select **"Deploy one revision from an existing container image"**
4. Click **"Select"** next to container image
5. Choose your image from Artifact Registry
6. Configure settings:
   - **Service name**: `sharemeal-backend`
   - **Region**: Same as Artifact Registry region
   - **Authentication**: Allow unauthenticated invocations (for public API)
   - **Container**: 
     - **Container port**: `8000`
     - **CPU**: 1
     - **Memory**: 512Mi
     - **Min instances**: 1 (to avoid cold starts)
     - **Max instances**: 10
   - **Service account**: Select `sharemeal-backend@PROJECT_ID.iam.gserviceaccount.com`
7. Scroll to **"Environment Variables"** section
8. Click **"+ Add Variable"** and add:
   - `MONGODB_URL` = `your_mongodb_connection_string`
   - `GOOGLE_CLIENT_ID` = `your_google_oauth_client_id` (from Google Cloud Console → APIs & Services → Credentials)
9. Click **"Create"** or **"Deploy"**

### Option B: Using CLI

```bash
gcloud run deploy sharemeal-backend \
  --image REGION_NAME-docker.pkg.dev/PROJECT_ID/REPOSITORY_NAME/IMAGE_NAME:IMAGE_TAG \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --service-account sharemeal-backend@PROJECT_ID.iam.gserviceaccount.com \
  --set-env-vars MONGODB_URL="your_mongodb_url_here",GOOGLE_CLIENT_ID="your_google_client_id" \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300 \
  --min-instances 1 \
  --max-instances 10 \
  --port 8080
```

**Example:**
```bash
gcloud run deploy sharemeal-backend \
  --image us-central1-docker.pkg.dev/sharemeal-project/sharemeal-repo/sharemeal-backend:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --service-account sharemeal-backend@sharemeal-project.iam.gserviceaccount.com \
  --set-env-vars MONGODB_URL="mongodb+srv://user:pass@cluster.mongodb.net/sharemeal" \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300 \
  --min-instances 1 \
  --max-instances 10 \
  --port 8080
```

### Explanation of flags:
- `--allow-unauthenticated`: Makes service publicly accessible
- `--service-account`: Service account for Cloud Run (no special permissions needed for Google OAuth)
- `--set-env-vars`: Sets MongoDB connection string and Google OAuth Client ID
- `--memory 512Mi`: Allocates 512MB RAM
- `--cpu 1`: Allocates 1 vCPU
- `--timeout 300`: 5 minute timeout
- `--min-instances 1`: Keeps 1 instance warm (no cold starts)
- `--max-instances 10`: Scales up to 10 instances
- `--port 8080`: Cloud Run default port

---

## Step 12: Verify Deployment

```bash
# Get service URL
gcloud run services describe sharemeal-backend \
  --platform managed \
  --region us-central1 \
  --format 'value(status.url)'

# Test health check
curl https://YOUR_SERVICE_URL/health

# Test root endpoint
curl https://YOUR_SERVICE_URL/
```

---

## Step 13: Update Environment Variables (If Needed)

### Option A: Using GUI

1. Go to [Cloud Run](https://console.cloud.google.com/run)
2. Click on your **`sharemeal-backend`** service
3. Click **"Edit & Deploy New Revision"** button at the top
4. Scroll down to **"Containers, Volumes, Networking, Security"** and click to expand
5. Find **"Environment Variables"** section
6. Click **"+ Add Variable"** for each variable:
   - `MONGODB_URL` = `your_mongodb_connection_string`
7. Click **"Deploy"**

### Option B: Using CLI

```bash
# Update MongoDB URL
gcloud run services update sharemeal-backend \
  --update-env-vars MONGODB_URL="new_mongodb_url" \
  --region us-central1

# Add more environment variables
gcloud run services update sharemeal-backend \
  --update-env-vars KEY1=value1,KEY2=value2 \
  --region us-central1
```

---

## Step 14: View Logs

```bash
# Stream logs
gcloud run services logs read sharemeal-backend \
  --platform managed \
  --region us-central1 \
  --limit 50

# Or view in Cloud Console
# https://console.cloud.google.com/run
```

---

## Step 15: Update Flutter App

Update your Flutter `ApiService` baseUrl:

```dart
// Get your Cloud Run URL
const ApiService baseUrl = 'https://sharemeal-backend-xxxxx.run.app';
```

---

## Troubleshooting

### Issue: "Permission denied" errors
**Solution:** 
- For Google OAuth: No special permissions needed
- For FCM: Ensure service account has Firebase Admin SDK permissions:
```bash
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:sharemeal-backend@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/firebase.admin"
```

### Issue: Health check failing
**Solution:** Check logs:
```bash
gcloud run services logs read sharemeal-backend --region us-central1
```

### Issue: MongoDB connection errors
**Solution:** 
1. Verify MongoDB URL is correct
2. Check MongoDB Atlas IP whitelist (add Cloud Run IPs or allow all: `0.0.0.0/0`)
3. Verify MongoDB user has correct permissions

### Issue: Cold starts
**Solution:** Already set `--min-instances 1` to keep one instance warm

### Issue: Build fails
**Solution:** Check Dockerfile syntax and ensure all dependencies are in `requirements.txt`

---

## Cost Estimation

With `--min-instances 1`:
- **Always-on instance**: ~$10-15/month (512MB, 1 vCPU)
- **Request costs**: $0.40 per million requests
- **Total**: ~$10-20/month for low traffic

**Note:** You can set `--min-instances 0` to reduce costs, but will have cold starts.

---

## Quick Commands Reference

```bash
# Deploy
gcloud run deploy sharemeal-backend \
  --image gcr.io/YOUR_PROJECT_ID/sharemeal-backend \
  --region us-central1

# Update environment variables
gcloud run services update sharemeal-backend \
  --update-env-vars KEY=value \
  --region us-central1

# View logs
gcloud run services logs read sharemeal-backend --region us-central1

# Delete service
gcloud run services delete sharemeal-backend --region us-central1

# List services
gcloud run services list --region us-central1
```

---

## Security Best Practices

✅ **DO:**
- Use WIF (Workload Identity Federation) - already configured!
- Set `--min-instances 1` for production (no cold starts)
- Use environment variables for secrets
- Enable Cloud Armor for DDoS protection (optional)
- Monitor logs regularly

❌ **DON'T:**
- Commit `.env` files to git
- Use service account JSON keys in Cloud Run
- Expose sensitive data in logs
- Allow unauthenticated access if not needed (use `--no-allow-unauthenticated`)

---

## Next Steps

1. ✅ Set up CI/CD with Cloud Build (optional)
2. ✅ Configure custom domain (optional)
3. ✅ Set up monitoring and alerts
4. ✅ Configure auto-scaling policies
5. ✅ Set up backup strategies

