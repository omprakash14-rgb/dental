#!/usr/bin/env bash
# =============================================================================
# DentalAI — Firebase Deployment Script
# Compiles frontend and deploys to Firebase Hosting with Cloud Run integration
# =============================================================================

set -euo pipefail

echo "================================================================="
echo "DentalAI — Firebase Deployment Utility"
echo "================================================================="

# 1. Determine Firebase CLI command
if command -v firebase >/dev/null 2>&1; then
    FIREBASE_CMD="firebase"
else
    echo "[INFO] Global firebase CLI not found. Using 'npx --yes firebase-tools'..."
    FIREBASE_CMD="npx --yes firebase-tools"
fi

# 2. Check Authentication
echo "[INFO] Checking Firebase Authentication..."
if ! ${FIREBASE_CMD} login:list 2>/dev/null | grep -q "@"; then
    echo "[ACTION REQUIRED] Logging in to Firebase..."
    ${FIREBASE_CMD} login
fi

# 3. Build Frontend
echo "[INFO] Compiling React frontend with Vite..."
(cd frontend && npm run build)

# 4. Optional Project Selection
if [ -n "${1:-}" ]; then
    PROJECT_ID="$1"
    echo "[INFO] Using target project: ${PROJECT_ID}"
    ${FIREBASE_CMD} use "${PROJECT_ID}"
fi

# 5. Deploy to Firebase Hosting
echo "[INFO] Deploying static bundle and security headers to Firebase Hosting..."
${FIREBASE_CMD} deploy --only hosting

echo "================================================================="
echo "✓ Frontend successfully deployed to Firebase Hosting!"
echo "================================================================="
echo "Note: If your backend is running on Google Cloud Run, verify that"
echo "the service name in 'firebase.json' matches your Cloud Run service:"
echo "  serviceId: 'dentalai-backend'"
echo "  region:    'us-central1'"
echo "================================================================="
