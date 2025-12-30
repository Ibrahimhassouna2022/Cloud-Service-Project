from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.spark_manager import SparkManager
from services.storage import file_exists

router = APIRouter(prefix="/jobs", tags=["Jobs"])

class JobRequest(BaseModel):
    filename: str
    job_type: str  # 'stats' or 'ml'
    params: dict = {}
    mode: str = "single" # 'single' or 'benchmark'

@router.post("/submit")
def submit_job(request: JobRequest):
    if not file_exists(request.filename):
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        if request.mode == "benchmark":
            job_id = SparkManager.submit_benchmark(request.job_type, request.filename, request.params)
        else:
            job_id = SparkManager.submit_job(request.job_type, request.filename, request.params)
            
        return {"job_id": job_id, "status": "SUBMITTED"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{job_id}")
def get_status(job_id: str):
    status = SparkManager.get_job_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"job_id": job_id, "status": status}

@router.get("/{job_id}/results")
def get_results(job_id: str):
    result = SparkManager.get_job_result(job_id)
    if result is None:
        status = SparkManager.get_job_status(job_id)
        if status == "FAILED":
             raise HTTPException(status_code=500, detail="Job failed")
        elif status == "RUNNING":
             raise HTTPException(status_code=202, detail="Job is still running")
        else:
             raise HTTPException(status_code=404, detail="Results not found")
    return result
