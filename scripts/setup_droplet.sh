#!/bin/bash

# ========================================================
# Cloud Deployment Script for DigitalOcean (Ubuntu 22.04+)
# ========================================================

echo ">>> Starting Cloud Environment Setup..."

# 1. Update System
echo ">>> Updating System Packages..."
sudo apt-get update && sudo apt-get upgrade -y

# 2. Install Python 3 & Pip
echo ">>> Installing Python..."
sudo apt-get install -y python3 python3-pip python3-venv

# 3. Install Java (Runtime for Apache Spark)
echo ">>> Installing Java (OpenJDK 11)..."
sudo apt-get install -y openjdk-11-jdk
java -version

# 4. Install Apache Spark
# Downloading Spark 3.5.0 (Adjust version if needed)
SPARK_VERSION="3.5.0"
if [ ! -d "/opt/spark" ]; then
    echo ">>> Downloading Apache Spark $SPARK_VERSION..."
    wget -q https://archive.apache.org/dist/spark/spark-$SPARK_VERSION/spark-$SPARK_VERSION-bin-hadoop3.tgz
    
    echo ">>> Extracting Spark..."
    tar xf spark-$SPARK_VERSION-bin-hadoop3.tgz
    sudo mv spark-$SPARK_VERSION-bin-hadoop3 /opt/spark
    rm spark-$SPARK_VERSION-bin-hadoop3.tgz
    
    echo ">>> Configuring Spark Environment..."
    echo 'export SPARK_HOME=/opt/spark' >> ~/.bashrc
    echo 'export PATH=$PATH:$SPARK_HOME/bin' >> ~/.bashrc
    source ~/.bashrc
else
    echo ">>> Spark already installed."
fi

# 5. Project Setup
echo ">>> Setting up Project Dependencies..."
# Navigate to project root (assuming this script is run from project root or inside scripts/)
# We try to find requirements.txt
if [ -f "backend/requirements.txt" ]; then
    cd backend
    pip3 install -r requirements.txt
    cd ..
elif [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt
else
    echo "WARNING: requirements.txt not found!"
fi

echo ">>> Cloud Environment Setup Complete!"
echo ">>> To run the server, use: ./scripts/run_cloud.sh"
