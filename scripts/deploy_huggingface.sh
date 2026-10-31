#!/usr/bin/env bash
# =============================================================================
# DentalAI — Hugging Face Spaces 100% Free Cloud Deployment Script
# =============================================================================

set -euo pipefail

HF_REPO_URL="${1:-}"

echo "================================================================="
echo "DentalAI — Hugging Face Free Cloud Backend Deployer"
echo "================================================================="

if [ -z "${HF_REPO_URL}" ]; then
    echo "Usage: $0 <HUGGINGFACE_SPACE_GIT_URL>"
    echo ""
    echo "Steps to get your free Space Git URL:"
    echo "1. Go to https://huggingface.co/new-space (free signup, no card)"
    echo "2. Space name: dentalai-backend (or any name)"
    echo "3. License: mit"
    echo "4. Select SDK: Docker (Blank)"
    echo "5. Space hardware: Free (CPU basic • 2 vCPU • 16 GB RAM)"
    echo "6. Click 'Create Space'"
    echo "7. Copy the Git URL (e.g., https://huggingface.co/spaces/YOUR_USER/dentalai-backend)"
    echo ""
    echo "Then re-run:"
    echo "  $0 https://huggingface.co/spaces/YOUR_USER/dentalai-backend"
    exit 1
fi

echo "[INFO] Preparing backend repository for Hugging Face Spaces..."
cd backend

# Initialize git in backend folder if needed
if [ ! -d ".git" ]; then
    git init -b main
    echo "[INFO] Git repository initialized in ./backend"
fi

# Configure remote
if git remote | grep -q "^hf$"; then
    git remote set-url hf "${HF_REPO_URL}"
else
    git remote add hf "${HF_REPO_URL}"
fi

echo "[INFO] Staging model weights, FastAPI app, and Docker configuration..."
git add -A
git commit -m "Deploy DentalAI ResNet-50 Backend to Hugging Face Spaces" || echo "[INFO] No changes to commit"

echo "[INFO] Pushing backend to Hugging Face (this uploads the 93MB ResNet-50 model)..."
git push -u hf main --force

echo "================================================================="
echo "✓ Backend successfully pushed to Hugging Face Spaces!"
echo "================================================================="
echo "Hugging Face is now building your Docker container (takes ~2 minutes)."
echo ""
echo "Once the Space status is 'Running', your permanent Free API URL is:"
# Derive public domain from repo URL
SPACE_PATH=$(echo "${HF_REPO_URL}" | sed -E 's|https://huggingface.co/spaces/||' | sed 's|\.git$||')
USER_PART=$(echo "${SPACE_PATH}" | cut -d'/' -f1)
NAME_PART=$(echo "${SPACE_PATH}" | cut -d'/' -f2)
HF_API_URL="https://${USER_PART}-${NAME_PART}.hf.space"

echo "  -> ${HF_API_URL}"
echo ""
echo "Next step: Link your live Firebase website to this free backend:"
echo "1. Put this URL in frontend/.env.production:"
echo "   echo \"VITE_API_URL=${HF_API_URL}\" > ../frontend/.env.production"
echo ""
echo "2. Re-deploy the frontend to Firebase:"
echo "   cd ../frontend && npm run build && cd .. && firebase deploy --only hosting"
echo "================================================================="

