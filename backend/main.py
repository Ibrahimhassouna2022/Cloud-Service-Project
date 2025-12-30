from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import files, jobs

app = FastAPI(title="Cloud Service Spark Platform")

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(files.router)
app.include_router(jobs.router)

@app.get("/")
def read_root():
    return {"message": "Cloud Service API is running"}
