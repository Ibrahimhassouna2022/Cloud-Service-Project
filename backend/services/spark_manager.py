import subprocess
import os
import json
import uuid
import time
import threading
from config import STORAGE_PATH, SPARK_MASTER

# Map job types to script paths
JOB_SCRIPTS = {
    "stats": "jobs/stats_job.py",
    "ml": "jobs/ml_job.py"
}

JOBS = {}  # In-memory job store (Use DB in prod)

class SparkManager:
    @staticmethod
    def submit_job(job_type: str, filename: str, params: dict = {}):
        job_id = str(uuid.uuid4())
        script = JOB_SCRIPTS.get(job_type)
        
        if not script:
            raise ValueError(f"Unknown job type: {job_type}")

        # Construct absolute paths
        input_path = os.path.join(STORAGE_PATH, filename)
        output_path = os.path.join(STORAGE_PATH, f"{job_id}_results.json")
        
        args = [
            "spark-submit",
            "--master", SPARK_MASTER,
            script,
            "--input", input_path,
            "--output", output_path,
            "--params", json.dumps(params)
        ]
        
        try:
            # Running asynchronously
            process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            JOBS[job_id] = {
                "status": "RUNNING", 
                "process": process, 
                "output_path": output_path,
                "type": job_type,
                "mode": "single"
            }
            return job_id
        except Exception as e:
            print(f"Failed to submit spark job: {e}")
            raise e

    @staticmethod
    def submit_benchmark(job_type: str, filename: str, params: dict = {}):
        """
        Runs the job 4 times sequentially on 1, 2, 4, 8 cores and records time.
        Note: We use local[N] to simulate N Nodes/Machines in a pseudo-distributed mode.
        """
        job_id = str(uuid.uuid4())
        script = JOB_SCRIPTS.get(job_type)
        
        if not script:
            raise ValueError(f"Unknown job type: {job_type}")
        
        JOBS[job_id] = {
            "status": "RUNNING",
            "type": job_type,
            "mode": "benchmark",
            "results": {
                "cores_1": None,
                "cores_2": None,
                "cores_4": None,
                "cores_8": None,
                "speedup": {},
                "efficiency": {}
            }
        }

        def run_benchmark_thread(jid, script_path, fname, prms):
            input_path = os.path.join(STORAGE_PATH, fname)
            base_output_path = os.path.join(STORAGE_PATH, jid)
            
            # Simulate cluster of 1, 2, 4, 8 machines using cores
            cores_list = [1, 2, 4, 8]
            times = {}
            
            try:
                for cores in cores_list:
                    # Update status
                    JOBS[jid]["current_run"] = f"Simulating Cluster with {cores} Machine(s)..."
                    
                    # distinct output for each run
                    run_output = f"{base_output_path}_mnt_{cores}.json"
                    
                    start_time = time.time()
                    
                    cmd = [
                        "spark-submit",
                        "--master", f"local[{cores}]", # Simulating N workers
                        script_path,
                        "--input", input_path,
                        "--output", run_output,
                        "--params", json.dumps(prms)
                    ]
                    
                    # Run blocking (wait for finish) to measure time accurately
                    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    
                    end_time = time.time()
                    duration = end_time - start_time
                    
                    if proc.returncode != 0:
                        raise Exception(f"Run failed on {cores} cores: {proc.stderr.decode()}")
                        
                    times[cores] = round(duration, 2)
                    JOBS[jid]["results"][f"cores_{cores}"] = times[cores]

                # Calculate Speedup and Efficiency
                # Speedup(N) = Time(1) / Time(N)
                # Efficiency(N) = Speedup(N) / N
                t1 = times[1]
                speedups = {}
                efficiencies = {}
                
                for c in cores_list:
                    su = t1 / times[c] if times[c] > 0 else 0
                    eff = su / c
                    speedups[c] = round(su, 2)
                    efficiencies[c] = round(eff, 2)
                
                JOBS[jid]["results"]["speedup"] = speedups
                JOBS[jid]["results"]["efficiency"] = efficiencies
                JOBS[jid]["status"] = "COMPLETED"
                JOBS[jid]["current_run"] = "Done"
                
                # Save final benchmark result to file
                final_res_path = f"../storage/{jid}_benchmark.json"
                with open(final_res_path, "w") as f:
                    json.dump(JOBS[jid]["results"], f)
                JOBS[jid]["output_path"] = final_res_path

            except Exception as e:
                print(f"Benchmark failed: {e}")
                JOBS[jid]["status"] = "FAILED"
                JOBS[jid]["error"] = str(e)

        # Start thread
        thread = threading.Thread(target=run_benchmark_thread, args=(job_id, script, filename, params))
        thread.start()
        
        return job_id

    @staticmethod
    def get_job_status(job_id: str):
        job = JOBS.get(job_id)
        if not job:
            return None
        
        if job["mode"] == "single":
            proc = job.get("process")
            if proc.poll() is None:
                return "RUNNING"
            else:
                if proc.returncode == 0:
                    job["status"] = "COMPLETED"
                else:
                    job["status"] = "FAILED"
                return job["status"]
        else:
            # Benchmark mode is updated by the thread
            return job["status"]

    @staticmethod
    def get_job_result(job_id: str):
        job = JOBS.get(job_id)
        if not job or job["status"] != "COMPLETED":
            return None
            
        output_path = job["output_path"]
        if os.path.exists(output_path):
            with open(output_path, "r") as f:
                return json.load(f)
        return None
