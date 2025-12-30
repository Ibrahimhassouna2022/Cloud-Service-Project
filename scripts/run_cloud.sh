#!/bin/bash

# ========================================================
# Run Application in Cloud Mode
# ========================================================

# Ensure we are in the project root
cd "$(dirname "$0")/.."

echo ">>> Starting Cloud Service..."

# Run Uvicorn on 0.0.0.0 to expose it to the public internet
# Port 8000
echo ">>> Server accessible at http://YOUR_DROPLET_IP:8000"

cd backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
