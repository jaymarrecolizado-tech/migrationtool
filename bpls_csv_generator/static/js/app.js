// BPLS CSV Generator - Frontend JavaScript

const dropZone = document.getElementById("dropZone");
const fileInput = document.getElementById("fileInput");
const processBtn = document.getElementById("processBtn");
const progressSection = document.getElementById("progressSection");
const resultsSection = document.getElementById("resultsSection");
const errorSection = document.getElementById("errorSection");
const resetBtn = document.getElementById("resetBtn");
const retryBtn = document.getElementById("retryBtn");

let selectedFile = null;

// Drag and drop handlers
dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("drag-over");
});

dropZone.addEventListener("dragleave", () => {
    dropZone.classList.remove("drag-over");
});

dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("drag-over");

    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFileSelect(files[0]);
    }
});

// Click to upload
dropZone.addEventListener("click", () => {
    fileInput.click();
});

fileInput.addEventListener("change", (e) => {
    if (e.target.files.length > 0) {
        handleFileSelect(e.target.files[0]);
    }
});

function handleFileSelect(file) {
    const validExtension =
        file.name.endsWith(".xlsx") || file.name.endsWith(".xls") || file.name.endsWith(".csv");

    if (!validExtension) {
        alert("Please upload a valid Excel or CSV file (.xlsx, .xls, or .csv)");
        return;
    }

    selectedFile = file;
    processBtn.disabled = false;

    // Update UI to show selected file
    const isCsv = file.name.endsWith(".csv");
    dropZone.querySelector("h2").textContent = file.name;
    dropZone.querySelector(".upload-icon").textContent = isCsv ? "📊" : "✅";
    dropZone.querySelector("p").textContent = formatFileSize(file.size) + (isCsv ? " (CSV - auto-detect schema)" : "");
}

function formatFileSize(bytes) {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + " " + sizes[i];
}

// Process button handler
processBtn.addEventListener("click", async () => {
    if (!selectedFile) return;

    const autoCorrect = document.getElementById("autoCorrect").checked;

    // Show progress
    progressSection.style.display = "block";
    resultsSection.style.display = "none";
    errorSection.style.display = "none";

    // Animate progress steps
    animateProgress();

    const formData = new FormData();
    formData.append("file", selectedFile);
    formData.append("auto_correct", autoCorrect);

    try {
        const response = await fetch("/api/upload", {
            method: "POST",
            body: formData,
        });

        const data = await response.json();

        if (response.ok && data.success) {
            showResults(data);
        } else {
            showError(data.error || "An error occurred during processing");
        }
    } catch (error) {
        showError("Failed to process file: " + error.message);
    }
});

function animateProgress() {
    const steps = document.querySelectorAll(".progress-step");
    let currentStep = 0;

    const interval = setInterval(() => {
        if (currentStep > 0) {
            steps[currentStep - 1].classList.remove("active");
            steps[currentStep - 1].classList.add("completed");
        }

        if (currentStep < steps.length) {
            steps[currentStep].classList.add("active");
            currentStep++;
        } else {
            clearInterval(interval);
        }
    }, 800);
}

function showResults(data) {
    // Hide progress, show results
    progressSection.style.display = "none";
    resultsSection.style.display = "block";

    // Update summary stats
    document.getElementById("totalRows").textContent =
        data.summary.total_rows.toLocaleString();
    document.getElementById("sheetsProcessed").textContent =
        data.summary.sheets_processed.length;
    document.getElementById("totalErrors").textContent =
        data.summary.total_errors;
    document.getElementById("totalCorrections").textContent =
        data.summary.total_corrections;

    // Show schema detection info (for CSV files)
    const detectionInfo = document.getElementById("detectionInfo");
    const detectionDetails = document.getElementById("detectionDetails");

    if (data.summary.detected_schema) {
        detectionInfo.style.display = "block";
        const confidence = (data.summary.detection_confidence * 100).toFixed(0);
        detectionDetails.innerHTML = `
            <div class="detection-item">
                <strong>Detected Schema:</strong> ${data.summary.detected_schema}
            </div>
            <div class="detection-item">
                <strong>Confidence:</strong> ${confidence}%
            </div>
        `;
    } else {
        detectionInfo.style.display = "none";
    }

    // Populate file list
    const fileList = document.getElementById("fileList");
    fileList.innerHTML = "";

    data.files.forEach((file) => {
        const fileItem = document.createElement("div");
        fileItem.className = "file-item";

        const icon = file.name.includes("_validated.csv")
            ? "📄"
            : file.name.includes("_errors.csv")
              ? "⚠️"
              : file.name.includes("transformation_log.csv")
                ? "📝"
                : "📊";

        fileItem.innerHTML = `
            <div class="file-info">
                <span class="file-icon">${icon}</span>
                <div>
                    <div class="file-name">${file.name}</div>
                    <div class="file-size">${formatFileSize(file.size)}</div>
                </div>
            </div>
            <a href="${file.url}" class="download-link" download>Download</a>
        `;

        fileList.appendChild(fileItem);
    });

    // Show sheet validation results (if available)
    const sheetResults = document.getElementById("sheetResults");
    sheetResults.innerHTML = "";

    if (data.summary.sheets) {
        Object.entries(data.summary.sheets).forEach(
            ([sheetName, stats]) => {
                const sheetDiv = document.createElement("div");
                sheetDiv.className = "sheet-result";
                sheetDiv.innerHTML = `
                    <div class="sheet-header">
                        <span class="sheet-name">${sheetName}</span>
                        <div class="sheet-stats">
                            <div class="sheet-stat">
                                <span class="stat-pass">${stats.passed} passed</span>
                            </div>
                            ${stats.errors > 0 ? `<div class="sheet-stat"><span class="stat-error">${stats.errors} errors</span></div>` : ""}
                            ${stats.warnings > 0 ? `<div class="sheet-stat"><span class="stat-warning">${stats.warnings} warnings</span></div>` : ""}
                        </div>
                    </div>
                `;
                sheetResults.appendChild(sheetDiv);
            }
        );
    }
}

function showError(message) {
    progressSection.style.display = "none";
    errorSection.style.display = "block";
    document.getElementById("errorMessage").textContent = message;
}

// Reset handlers
resetBtn.addEventListener("click", resetForm);
retryBtn.addEventListener("click", resetForm);

function resetForm() {
    selectedFile = null;
    processBtn.disabled = true;
    progressSection.style.display = "none";
    resultsSection.style.display = "none";
    errorSection.style.display = "none";

    // Reset upload area
    dropZone.querySelector("h2").textContent = "Upload Excel or CSV File";
    dropZone.querySelector(".upload-icon").textContent = "📁";
    dropZone.querySelector("p").textContent =
        "Drag & drop your migration data file here";

    // Reset file input
    fileInput.value = "";

    // Reset progress steps
    document.querySelectorAll(".progress-step").forEach((step) => {
        step.classList.remove("active", "completed");
    });

    // Hide detection info
    document.getElementById("detectionInfo").style.display = "none";
}

// Check API status on load
window.addEventListener("load", async () => {
    try {
        const response = await fetch("/api/status");
        if (response.ok) {
            console.log("API is ready");
        }
    } catch (error) {
        console.warn("API not reachable:", error);
    }
});
