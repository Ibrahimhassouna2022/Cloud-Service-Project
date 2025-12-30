from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from routers import files, jobs
import os

# Ensure storage directory exists
os.makedirs("../storage", exist_ok=True)

app = FastAPI(title="Cloud Service Spark Platform")

# Allow CORS for frontend (useful if accessing via file:// locally)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(files.router)
app.include_router(jobs.router)

# ==========================================
# Cloud UI Serving
# ==========================================
# Serve Frontend Static Files (CSS/JS)
# This allows accessing the app via http://YOUR_DROPLET_IP:8000/
# instead of opening the HTML file locally.

frontend_path = "../frontend"
if os.path.exists(frontend_path):
    app.mount("/css", StaticFiles(directory=f"{frontend_path}/css"), name="css")
    app.mount("/js", StaticFiles(directory=f"{frontend_path}/js"), name="js")

    @app.get("/")
    async def read_index():
        return FileResponse(f"{frontend_path}/index.html")
else:
    print("Warning: Frontend directory not found. UI serving disabled.")

@app.get("/health")
def health_check():
    return {"status": "ok", "platform": "DigitalOcean Ready"}
