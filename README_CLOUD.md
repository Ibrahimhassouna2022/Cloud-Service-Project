# Cloud Service Project - DigitalOcean Deployment Guide

This project is designed to run on a Cloud VM (DigitalOcean Droplet).
Follow these instructions to deploy and run the distributed data processing service.

## 1. Prerequisites
- A DigitalOcean Droplet (Ubuntu 22.04 or 24.04 recommended).
- At least 4GB RAM (8GB recommended for Spark jobs).
- SSH Access to the Droplet.

## 2. Uploading Code to Cloud
You can use `scp` or `git` to transfer files.
```bash
# Example using SCP
scp -r "Cloud Service Project" root@YOUR_DROPLET_IP:/root/
```

## 3. Installation
SSH into your Droplet and run the setup script:
```bash
cd "Cloud Service Project"
chmod +x scripts/setup_droplet.sh
./scripts/setup_droplet.sh
```
*This script will install Java (OpenJDK 11), Apache Spark, Python 3, and all dependencies.*

## 4. Running the Service
Start the server in "Cloud Mode" (Exposed on 0.0.0.0):
```bash
chmod +x scripts/run_cloud.sh
./scripts/run_cloud.sh
```

## 5. Accessing the Interface
Open your web browser and navigate to:
`http://YOUR_DROPLET_IP:8000`

## 6. Cloud Features & Scalability
- **Storage**: By default, the system uses the Droplet's Block Storage (`backend/storage/`).
  - To use **DigitalOcean Spaces (S3)**, edit `backend/config.py` and update `STORAGE_PATH`.
- **Scalability Testing**: The "Run Scalability Test" button in the UI executes the Spark simulation on 1, 2, 4, and 8 cores (simulating cloud nodes) directly on the VM.
- **Reporting**: The benchmark results table (Speedup/Efficiency) is generated and displayed for your report.

## 7. Structure
- `backend/`: FastAPI Application & Spark Jobs
- `frontend/`: HTML5/JS Interface (Served statically by FastAPI)
- `storage/`: Data storage directory (Simulated Cloud Bucket)
- `scripts/`: Deployment scripts
