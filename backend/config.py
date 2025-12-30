import os

# ==========================================
# Cloud & Storage Configuration
# ==========================================

# Cloud Storage Configuration
# ==========================================

# Base Directory of the Backend
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# STORAGE_PATH defines where datasets and results are stored.
# Option A: DigitalOcean Block Storage / Local (Default)
STORAGE_PATH = os.path.abspath(os.path.join(BASE_DIR, "../storage"))

# Option B: DigitalOcean Spaces (S3 Compatible)
# To use Spaces, uncomment and configure below:
# STORAGE_PATH = "s3a://your-space-name/datasets/"
# os.environ['AWS_ACCESS_KEY_ID'] = 'DO_ACCESS_KEY'
# os.environ['AWS_SECRET_ACCESS_KEY'] = 'DO_SECRET_KEY'
# os.environ['AWS_ENDPOINT'] = 'https://nyc3.digitaloceanspaces.com'

# Ensure storage directory exists (only works for local filesystem)
if not STORAGE_PATH.startswith("s3"):
    os.makedirs(STORAGE_PATH, exist_ok=True)

# ==========================================
# Spark Cluster Configuration
# ==========================================

# Spark Master URL
# - "local[*]": Uses all available cores on the single VM (Vertical Scaling).
# - "spark://MASTER_IP:7077": Connects to a real Standalone Spark Cluster (Horizontal Scaling).
# - "yarn": Connects to a YARN cluster (e.g., AWS EMR).
# For this project assignment, we default to local simulation.
SPARK_MASTER = "local[*]"

# App Name
APP_NAME = "CloudServiceSparkPlatform"
