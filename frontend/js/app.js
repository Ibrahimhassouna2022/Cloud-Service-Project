const API_URL = "http://localhost:8000";

async function uploadFile() {
    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0];
    if (!file) return alert("Please select a file!");

    const formData = new FormData();
    formData.append("file", file);

    try {
        const response = await fetch(`${API_URL}/files/upload`, {
            method: 'POST',
            body: formData
        });
        const result = await response.json();
        alert(result.message);
        loadFiles();
    } catch (error) {
        console.error("Error uploading file:", error);
        alert("Upload failed.");
    }
}

async function loadFiles() {
    try {
        const response = await fetch(`${API_URL}/files/`);
        const files = await response.json();
        const select = document.getElementById('fileSelect');
        select.innerHTML = '<option value="">Select a file...</option>';
        files.forEach(f => {
            const option = document.createElement('option');
            option.value = f.filename;
            option.textContent = `${f.filename} (${f.size} bytes)`;
            select.appendChild(option);
        });
    } catch (error) {
        console.error("Error loading files:", error);
    }
}

async function submitJob(mode = 'single') {
    const filename = document.getElementById('fileSelect').value;
    const jobType = document.getElementById('jobType').value;

    if (!filename || !jobType) return alert("Please select a file and job type!");

    let params = {};
    if (jobType === 'ml') {
        const algo = document.getElementById('mlAlgo').value;
        const target = document.getElementById('targetCol').value;
        params = { algorithm: algo, target_col: target };
    }

    // Reset UI
    document.getElementById('benchmarkResults').style.display = 'none';
    document.getElementById('resultsArea').innerHTML = '';
    document.getElementById('downloadLink').style.display = 'none';

    try {
        const response = await fetch(`${API_URL}/jobs/submit`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                filename: filename,
                job_type: jobType,
                params: params,
                mode: mode
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || "Submission failed");
        }

        const result = await response.json();
        monitorJob(result.job_id);
    } catch (error) {
        console.error("Error submitting job:", error);
        alert(`Error: ${error.message}`);
    }
}

function monitorJob(jobId) {
    const statusDiv = document.getElementById('status-log');
    statusDiv.innerHTML = `Job ${jobId} submitted. <br>`;

    const interval = setInterval(async () => {
        try {
            const response = await fetch(`${API_URL}/jobs/${jobId}`);
            const status = await response.json();
            
            if (status) {
                // If there's a specific 'current_run' message (e.g. from benchmark), show it
                if (status.current_run) {
                     statusDiv.innerHTML = `Job ${jobId}: ${status.status}<br><b>${status.current_run}</b>`;
                } else {
                     statusDiv.innerHTML = `Job ${jobId}: ${status.status}`;
                }

                if (status.status === 'COMPLETED') {
                    clearInterval(interval);
                    showResults(jobId);
                } else if (status.status === 'FAILED') {
                    clearInterval(interval);
                    statusDiv.innerHTML += `<br><span style="color:red">Job FAILED. ${status.error || ''}</span>`;
                }
            }
        } catch (error) {
            clearInterval(interval);
        }
    }, 2000);
}

async function showResults(jobId) {
    try {
        const response = await fetch(`${API_URL}/jobs/${jobId}/results`);
        const result = await response.json();

        const resultsDiv = document.getElementById('resultsArea');
        resultsDiv.innerHTML = "<h3>Results Output</h3>";

        // Setup Download Link
        const downloadLink = document.getElementById('downloadLink');
        const listStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(result, null, 2));
        downloadLink.setAttribute("href", listStr);
        downloadLink.setAttribute("download", `results_${jobId}.json`);
        downloadLink.style.display = 'inline-block';
        downloadLink.textContent = "Download Results JSON";

        // Check if it's benchmark result
        if (result.speedup && result.efficiency) {
            document.getElementById('benchmarkResults').style.display = 'block';
            const tbody = document.getElementById('benchmarkBody');
            tbody.innerHTML = '';
            
            [1, 2, 4, 8].forEach(core => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${core}</td>
                    <td>${result[`cores_${core}`] || '-'}</td>
                    <td>${result.speedup[core]}</td>
                    <td>${result.efficiency[core]}</td>
                `;
                tbody.appendChild(tr);
            });
            
            // Also show raw JSON
            const pre = document.createElement('pre');
            pre.textContent = JSON.stringify(result, null, 2);
            resultsDiv.appendChild(pre);
            
        } else {
            // Normal Result
            const pre = document.createElement('pre');
            pre.textContent = JSON.stringify(result, null, 2);
            resultsDiv.appendChild(pre);
        }

    } catch (error) {
        console.error("Error fetching results:", error);
    }
}

// Initial load
window.onload = loadFiles;
