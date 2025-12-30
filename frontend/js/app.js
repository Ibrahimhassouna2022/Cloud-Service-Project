// Detect environment: If running from file system (local), use localhost.
// If running from a server (Cloud/DigitalOcean), use relative path.
const API_URL = window.location.protocol === 'file:' ? 'http://localhost:8000' : '';

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

        // 1. Benchmark Results (Scalability)
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
        } 
        
        // 2. Descriptive Statistics
        if (result.rows && result.columns) {
            let html = `
                <div class="stat-box">
                    <p><strong>Total Rows:</strong> ${result.rows}</p>
                    <p><strong>Total Columns:</strong> ${result.columns}</p>
                </div>
                <h4>Column Data Types</h4>
                ${createTableFromObject(result.column_types, "Column", "Type")}
                
                <h4>Null Value Counts</h4>
                ${createTableFromObject(result.null_counts, "Column", "Null Count")}
            `;

            if (result.statistics) {
                html += `<h4>Basic Statistics (Numeric Columns)</h4>`;
                html += `<table class="styled-table"><thead><tr><th>Column</th><th>Min</th><th>Max</th><th>Mean</th></tr></thead><tbody>`;
                for (const [col, stats] of Object.entries(result.statistics)) {
                    html += `<tr>
                        <td>${col}</td>
                        <td>${stats.min}</td>
                        <td>${stats.max}</td>
                        <td>${parseFloat(stats.mean).toFixed(4)}</td>
                    </tr>`;
                }
                html += `</tbody></table>`;
            }
            resultsDiv.innerHTML += html;
            return;
        }

        // 3. Machine Learning - Linear Regression
        if (result.algorithm === "linear_regression") {
            let html = `<h4>Linear Regression Results</h4>
            <ul>
                <li><strong>RMSE:</strong> ${result.rmse}</li>
                <li><strong>R2 (R-Squared):</strong> ${result.r2}</li>
                <li><strong>Intercept:</strong> ${result.intercept}</li>
                <li><strong>Coefficients:</strong> ${result.coefficients}</li>
            </ul>`;
            resultsDiv.innerHTML += html;
            return;
        }

        // 4. Machine Learning - Logistic Regression
        if (result.algorithm === "logistic_regression") {
             let html = `<h4>Logistic Regression Results</h4>
            <ul>
                <li><strong>Accuracy:</strong> ${result.accuracy}</li>
                <li><strong>Area Under ROC:</strong> ${result.areaUnderROC}</li>
            </ul>`;
            resultsDiv.innerHTML += html;
            return;
        }

        // 5. Machine Learning - KMeans
        if (result.algorithm === "kmeans") {
            let html = `<h4>KMeans Clustering Results</h4>`;
            if (result.cluster_centers) {
                html += `<h5>Cluster Centers</h5>`;
                result.cluster_centers.forEach((center, idx) => {
                    html += `<p><strong>Cluster ${idx}:</strong> [${center.map(v => v.toFixed(4)).join(", ")}]</p>`;
                });
            }
            resultsDiv.innerHTML += html;
            return;
        }

        // 6. Machine Learning - FPGrowth
        if (result.algorithm === "fpgrowth") {
            let html = `<h4>FPGrowth Association Rules</h4>`;
            
            if (result.frequent_items) {
                html += `<h5>Top Frequent Items</h5>`;
                html += `<table class="styled-table"><thead><tr><th>Items</th><th>Freq</th></tr></thead><tbody>`;
                result.frequent_items.forEach(item => {
                     html += `<tr><td>${item.items.join(", ")}</td><td>${item.freq}</td></tr>`;
                });
                html += `</tbody></table>`;
            }

            if (result.association_rules) {
                html += `<h5>Top Association Rules</h5>`;
                html += `<table class="styled-table"><thead><tr><th>Antecedent</th><th>Consequent</th><th>Confidence</th><th>Lift</th></tr></thead><tbody>`;
                result.association_rules.forEach(rule => {
                     html += `<tr>
                        <td>${rule.antecedent.join(", ")}</td>
                        <td>${rule.consequent.join(", ")}</td>
                        <td>${parseFloat(rule.confidence).toFixed(4)}</td>
                        <td>${parseFloat(rule.lift).toFixed(4)}</td>
                     </tr>`;
                });
                html += `</tbody></table>`;
            }
            resultsDiv.innerHTML += html;
            return;
        }

        // Fallback for errors or unknown
        const pre = document.createElement('pre');
        pre.textContent = JSON.stringify(result, null, 2);
        resultsDiv.appendChild(pre);

    } catch (error) {
        console.error("Error fetching results:", error);
    }
}

function createTableFromObject(obj, headerKey, headerVal) {
    let html = `<table class="styled-table"><thead><tr><th>${headerKey}</th><th>${headerVal}</th></tr></thead><tbody>`;
    for (const [key, value] of Object.entries(obj)) {
        html += `<tr><td>${key}</td><td>${value}</td></tr>`;
    }
    html += `</tbody></table>`;
    return html;
}

// Initial load
window.onload = loadFiles;
