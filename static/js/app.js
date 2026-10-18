/**
 * AutoDS -- Frontend Logic
 * Handles CSV upload, profiling, and rendering results.
 */

(function () {
    "use strict";

    // ── DOM refs ──
    const $ = (sel) => document.querySelector(sel);
    const $$ = (sel) => document.querySelectorAll(sel);

    const uploadArea = $("#upload-area");
    const fileInput = $("#file-input");
    const uploadError = $("#upload-error");

    const sectionUploadResult = $("#section-upload-result");
    const uploadSuccess = $("#upload-success");
    const uploadMetrics = $("#upload-metrics");
    const previewTable = $("#preview-table");

    const sectionProfiler = $("#section-profiler");
    const targetSelect = $("#target-select");
    const btnProfile = $("#btn-profile");

    const sectionProfileResults = $("#section-profile-results");
    const profileMetrics = $("#profile-metrics");

    let currentStage = 0;


    // ── Helpers ──
    function show(el) { el.classList.remove("hidden"); }
    function hide(el) { el.classList.add("hidden"); }

    function showError(msg) {
        uploadError.textContent = msg;
        show(uploadError);
    }

    function formatNum(n) {
        return Number(n).toLocaleString();
    }

    function makeMetricHTML(label, value) {
        return `<div class="metric-card"><div class="label">${label}</div><div class="value">${value}</div></div>`;
    }

    
    function buildTable(headers, rows) {
        if (!Array.isArray(headers) || !Array.isArray(rows)) {
            console.error("buildTable expected arrays:", { headers, rows });
            return '<tbody><tr><td>Unable to render table data.</td></tr></tbody>';
        }
        let html = "<thead><tr>";
        headers.forEach((header) => {
            html += `<th>${header}</th>`;
        });
        html += "</tr></thead><tbody>";
        rows.forEach((row) => {
            html += "<tr>";
            headers.forEach((header) => {
                let value = row[header];
                if (value === null || value === undefined) {
                    value = "";
                }
                html += `<td>${value}</td>`;
            });
            html += "</tr>";
        });
        html += "</tbody>";
        return html;
    }

    // ── Upload: drag & drop + click ──
    uploadArea.addEventListener("click", () => fileInput.click());

    uploadArea.addEventListener("dragover", (e) => {
        e.preventDefault();
        uploadArea.classList.add("drag-over");
    });

    uploadArea.addEventListener("dragleave", () => {
        uploadArea.classList.remove("drag-over");
    });

    uploadArea.addEventListener("drop", (e) => {
        e.preventDefault();
        uploadArea.classList.remove("drag-over");
        if (e.dataTransfer.files.length) {
            fileInput.files = e.dataTransfer.files;
            handleUpload(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener("change", () => {
        if (fileInput.files.length) handleUpload(fileInput.files[0]);
    });

    // ── Upload handler ──
    async function handleUpload(file) {
        hide(uploadError);
        hide(sectionUploadResult);
        hide(sectionProfiler);
        hide(sectionProfileResults);
        hide(cleaningSection);
        hide(mlSection);
        anomalyMetrics.innerHTML = "";
        anomalyTable.innerHTML = "";
        anomalyStatus.textContent = "";
        hide(reportSection);
        reportStatus.textContent = "";
        downloadReportButton.disabled = true;
        hide(reportSection);
        downloadReportButton.disabled = true;
        reportStatus.textContent = "";
        show(reportSection);

        const formData = new FormData();
        formData.append("file", file);

        try {
            const res = await fetch("/api/upload", { method: "POST", body: formData });
            const data = await res.json();

            if (!res.ok) {
                showError(data.error || "Upload failed");
                return;
            }

            // Success
            uploadSuccess.textContent = `Dataset loaded: ${data.filename}`;
            show(sectionUploadResult);

            // Metrics
            uploadMetrics.innerHTML =
                makeMetricHTML("Rows", formatNum(data.rows)) +
                makeMetricHTML("Columns", data.columns) +
                makeMetricHTML("Total Cells", formatNum(data.rows * data.columns)) +
                makeMetricHTML("Memory", data.memory_mb + " MB");

            // Preview table
            previewTable.innerHTML = buildTable(
                data.column_names,
                data.preview
            );


            // Target select
            targetSelect.innerHTML = "";
            data.column_names.forEach((col, i) => {
                const opt = document.createElement("option");
                opt.value = col;
                opt.textContent = col;
                if (i === data.column_names.length - 1) opt.selected = true;
                targetSelect.appendChild(opt);
            });

            show(sectionProfiler);
        } catch (err) {
            showError("Network error: " + err.message);
        }
    }

    // ── Run Profiler ──
    btnProfile.addEventListener("click", async () => {
        btnProfile.disabled = true;
        btnProfile.innerHTML = '<span class="spinner"></span> Running...';

        try {
            const res = await fetch("/api/profile", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ target_column: targetSelect.value }),
            });
            const data = await res.json();

            if (!res.ok) {
                showError(data.error || "Profiling failed");
                return;
            }

            renderProfile(data);
            show(sectionProfileResults);
        } catch (err) {
            showError("Network error: " + err.message);
        } finally {
            btnProfile.disabled = false;
            btnProfile.textContent = "Run Profiler";
        }
    });

    // ── Render profile results ──
    function renderProfile(data) {
        // Task badge
        const badge = $("#task-badge");
        badge.textContent = data.task_type;
        badge.className = "badge " + (data.task_type === "Classification" ? "badge-classification" : "badge-regression");
        $("#target-name").textContent = data.target_column;

        // Metrics
        profileMetrics.innerHTML =
            makeMetricHTML("Rows", formatNum(data.rows)) +
            makeMetricHTML("Columns", data.columns) +
            makeMetricHTML("Numeric", data.numeric_count) +
            makeMetricHTML("Categorical", data.categorical_count) +
            makeMetricHTML("Duplicates", formatNum(data.duplicate_rows));

        // Tab: Missing
        renderMissing(data);

        // Tab: Types
        renderTypes(data);

        // Tab: Stats
        renderStats(data);

        // Tab: Correlations
        renderCorrelations(data);

        // Tab: Class Balance
        renderClassBalance(data);
    }

    // ── Tab: Missing Values ──
    function renderMissing(data) {
        const panel = $("#tab-missing");
        if (!data.missing.length) {
            panel.innerHTML = '<div class="alert alert-success">No missing values -- the dataset is complete.</div>';
            return;
        }

        let html = `<div class="alert alert-warning">${data.missing.length} column(s) have missing values (${formatNum(data.total_missing)} total cells)</div>`;

        // Table
        html += '<div class="table-wrap"><table>';
        html += "<thead><tr><th>Column</th><th>Missing</th><th>Percent (%)</th></tr></thead><tbody>";
        data.missing.forEach((m) => {
            html += `<tr><td>${m.Column}</td><td>${formatNum(m.Missing)}</td><td>${m["Percent (%)"]}</td></tr>`;
        });
        html += "</tbody></table></div>";

        // Bar chart
        const maxPct = Math.max(...data.missing.map((m) => m["Percent (%)"]));
        html += '<div class="bar-chart">';
        data.missing.forEach((m) => {
            const w = (m["Percent (%)"] / maxPct) * 100;
            html += `
                <div class="bar-row">
                    <span class="bar-label">${m.Column}</span>
                    <div class="bar-track"><div class="bar-fill" style="width:${w}%"></div></div>
                    <span class="bar-value">${m["Percent (%)"]}%</span>
                </div>`;
        });
        html += "</div>";

        panel.innerHTML = html;
    }

    // ── Tab: Data Types ──
    function renderTypes(data) {
        const panel = $("#tab-types");
        let html = "";

        html += '<div class="table-wrap"><table>';
        html += "<thead><tr><th>Column</th><th>Type</th><th>Unique Values</th></tr></thead><tbody>";
        data.types.forEach((t) => {
            html += `<tr><td>${t.Column}</td><td>${t.Type}</td><td>${t["Unique Values"]}</td></tr>`;
        });
        html += "</tbody></table></div>";

        if (data.constant_columns.length) {
            html += `<div class="alert alert-warning" style="margin-top:10px">Constant columns detected: ${data.constant_columns.join(", ")} (only 1 unique value)</div>`;
        }
        if (data.high_cardinality.length) {
            html += `<div class="alert alert-info" style="margin-top:10px">High cardinality: ${data.high_cardinality.join(", ")} (>50 unique values)</div>`;
        }

        panel.innerHTML = html;
    }

    // ── Tab: Statistics ──
    function renderStats(data) {
        const panel = $("#tab-stats");

        if (!data.numeric_stats) {
            panel.innerHTML = '<div class="alert alert-info">No numeric columns found.</div>';
            return;
        }

        // numeric_stats is { "count": { "col1": val, ... }, "mean": { ... }, ... }
        const statKeys = Object.keys(data.numeric_stats);
        const cols = Object.keys(data.numeric_stats[statKeys[0]]);

        let html = '<div class="table-wrap"><table>';
        html += "<thead><tr><th></th>";
        cols.forEach((c) => (html += `<th>${c}</th>`));
        html += "</tr></thead><tbody>";
        statKeys.forEach((stat) => {
            html += `<tr><td><strong>${stat}</strong></td>`;
            cols.forEach((c) => {
                const v = data.numeric_stats[stat][c];
                html += `<td>${v !== null && v !== undefined ? v : ""}</td>`;
            });
            html += "</tr>";
        });
        html += "</tbody></table></div>";

        // Skewness & Kurtosis
        if (Object.keys(data.skewness).length) {
            html += '<h3 style="font-size:0.85rem; font-weight:600; margin:16px 0 8px">Skewness and Kurtosis</h3>';
            html += '<div class="table-wrap"><table>';
            html += "<thead><tr><th>Column</th><th>Skewness</th><th>Kurtosis</th></tr></thead><tbody>";
            Object.keys(data.skewness).forEach((col) => {
                html += `<tr><td>${col}</td><td>${data.skewness[col]}</td><td>${data.kurtosis[col] ?? ""}</td></tr>`;
            });
            html += "</tbody></table></div>";
        }

        panel.innerHTML = html;
    }

    // ── Tab: Correlations ──
    function renderCorrelations(data) {
        const panel = $("#tab-corr");

        if (!data.correlation) {
            panel.innerHTML = '<div class="alert alert-info">Need at least 2 numeric columns for correlation analysis.</div>';
            return;
        }

        const cols = data.correlation.columns;
        const vals = data.correlation.values;

        let html = '<div class="corr-grid"><div class="table-wrap"><table>';
        html += "<thead><tr><th></th>";
        cols.forEach((c) => (html += `<th>${c}</th>`));
        html += "</tr></thead><tbody>";
        vals.forEach((row, i) => {
            html += `<tr><td><strong>${cols[i]}</strong></td>`;
            row.forEach((v) => {
                const abs = Math.abs(v);
                let bg = "transparent";
                if (abs > 0.7) bg = "rgba(108,114,203,0.25)";
                else if (abs > 0.4) bg = "rgba(108,114,203,0.1)";
                html += `<td style="background:${bg}">${v.toFixed(2)}</td>`;
            });
            html += "</tr>";
        });
        html += "</tbody></table></div></div>";

        // Highly correlated pairs
        if (data.corr_pairs.length) {
            html += '<h3 style="font-size:0.85rem; font-weight:600; margin:16px 0 8px">Highly Correlated Pairs (|r| > 0.7)</h3>';
            html += '<div class="table-wrap"><table>';
            html += "<thead><tr><th>Feature A</th><th>Feature B</th><th>Correlation</th></tr></thead><tbody>";
            data.corr_pairs.forEach((p) => {
                html += `<tr><td>${p.a}</td><td>${p.b}</td><td>${p.r}</td></tr>`;
            });
            html += "</tbody></table></div>";
        }

        panel.innerHTML = html;
    }

    // ── Tab: Class Balance ──
    function renderClassBalance(data) {
        const panel = $("#tab-balance");

        if (data.task_type !== "Classification" || !data.class_balance) {
            panel.innerHTML = '<div class="alert alert-info">Class balance is only shown for Classification tasks.</div>';
            return;
        }

        const labels = Object.keys(data.class_balance);
        const values = Object.values(data.class_balance);
        const total = values.reduce((a, b) => a + b, 0);
        const maxVal = Math.max(...values);

        let html = '<div class="table-wrap"><table>';
        html += "<thead><tr><th>Class</th><th>Count</th><th>Percent (%)</th></tr></thead><tbody>";
        labels.forEach((label, i) => {
            const pct = ((values[i] / total) * 100).toFixed(1);
            html += `<tr><td>${label}</td><td>${formatNum(values[i])}</td><td>${pct}</td></tr>`;
        });
        html += "</tbody></table></div>";

        // Bar chart
        html += '<div class="bar-chart" style="margin-top:12px">';
        labels.forEach((label, i) => {
            const w = (values[i] / maxVal) * 100;
            const pct = ((values[i] / total) * 100).toFixed(1);
            html += `
                <div class="bar-row">
                    <span class="bar-label">${label}</span>
                    <div class="bar-track"><div class="bar-fill" style="width:${w}%"></div></div>
                    <span class="bar-value">${pct}%</span>
                </div>`;
        });
        html += "</div>";

        // Imbalance warning
        const minVal = Math.min(...values);
        if (maxVal / Math.max(minVal, 1) > 3) {
            html += '<div class="alert alert-warning" style="margin-top:10px">Class imbalance detected -- the majority class is >3x the minority. Consider SMOTE or class weights during training.</div>';
        }

        panel.innerHTML = html;
    }
    
    // ── Cleaning interface ──
    const cleaningSection = document.createElement("section");
    cleaningSection.id = "section-cleaning";
    cleaningSection.className = "hidden";
    cleaningSection.style.cssText =
        "margin-top:24px;padding:24px;border:1px solid #343747;" +
        "border-radius:12px;background:#171923;color:#f1f2f7;";

    cleaningSection.innerHTML = `
        <h2 style="margin:0 0 8px;font-size:1.25rem;">Data Cleaning</h2>
        <p style="color:#a5a8b8;margin:0 0 20px;">
            Handle missing values and duplicate rows in your dataset.
        </p>

        <div style="display:flex;flex-wrap:wrap;gap:20px;align-items:end;">
            <label style="display:flex;flex-direction:column;gap:8px;">
                Missing-value strategy
                <select id="clean-strategy"
                    style="padding:10px;border-radius:6px;background:#252837;
                    color:#fff;border:1px solid #484c60;">
                    <option value="auto">Automatic (median / mode)</option>
                    <option value="mean">Mean (numeric columns only)</option>
                    <option value="median">Median (numeric columns only)</option>
                    <option value="mode">Mode (all columns)</option>
                    <option value="none">Leave missing values unchanged</option>
                </select>
            </label>

            <label style="display:flex;gap:8px;align-items:center;">
                <input type="checkbox" id="clean-duplicates" checked>
                Remove duplicate rows
            </label>

            <button id="btn-clean"
                style="padding:11px 18px;border:0;border-radius:6px;
                background:#7775e8;color:white;cursor:pointer;">
                Run Cleaning
            </button>

            <button id="btn-download-cleaned" disabled
                style="padding:11px 18px;border:0;border-radius:6px;
                background:#277b61;color:white;cursor:pointer;">
                Download Cleaned CSV
            </button>
        </div>

        <div id="clean-status" role="status" aria-live="polite"
            style="margin-top:16px;"></div>

        <div id="clean-metrics"
            style="display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));
            gap:12px;margin-top:16px;"></div>

        <h3 style="margin-top:24px;font-size:1rem;">Cleaned Dataset Preview</h3>
        <div id="clean-preview" class="table-wrap"
            style="overflow-x:auto;margin-top:12px;"></div>
    `;

    // Place the cleaning section after the profile results.
    sectionProfileResults.insertAdjacentElement(
        "afterend",
        cleaningSection
    );
    
    // ── ML Insights interface ──
    const mlSection = document.createElement("section");
    mlSection.id = "section-ml-insights";
    mlSection.className = "hidden section";

    mlSection.innerHTML = `
        <h2 class="section-title">ML Insights — Anomaly Detection</h2>
        <p style="color:var(--text-muted);margin-bottom:16px;">
            Identify potentially unusual records using Isolation Forest.
            Results indicate potential anomalies, not confirmed errors.
        </p>

        <button class="btn btn-primary" id="btn-anomalies">
            Detect Anomalies
        </button>

        <div id="anomaly-status" role="status"
             aria-live="polite" style="margin-top:16px;"></div>

        <div id="anomaly-metrics" class="metrics"></div>

        <h3 style="margin-top:24px;">Flagged Records</h3>
        <div id="anomaly-table" class="table-wrap"
             style="margin-top:12px;"></div>
    `;

    cleaningSection.insertAdjacentElement("afterend", mlSection);

    
    // ── Report generation interface ──
    const reportSection = document.createElement("section");
    reportSection.id = "section-report";
    reportSection.className = "section hidden";
    reportSection.style.cssText =
        "margin-top:24px;padding:24px;border:1px solid #343747;" +
        "border-radius:12px;background:#171923;color:#f1f2f7;";

    reportSection.innerHTML = `
        <h2 style="margin:0 0 8px;font-size:1.25rem;">
            Generate Report
        </h2>
        <p style="color:#a5a8b8;margin:0 0 16px;">
            Generate a downloadable HTML report containing dataset statistics,
            cleaning results, and anomaly-detection results.
        </p>

        <div style="display:flex;gap:12px;flex-wrap:wrap;">
            <button id="btn-generate-report"
                style="padding:11px 18px;border:0;border-radius:6px;
                background:#7775e8;color:white;cursor:pointer;">
                Generate Report
            </button>

            <button id="btn-download-report" disabled
                style="padding:11px 18px;border:0;border-radius:6px;
                background:#277b61;color:white;cursor:pointer;">
                Download HTML Report
            </button>
        </div>

        <div id="report-status" role="status" aria-live="polite"
             style="margin-top:16px;"></div>
    `;

    mlSection.insertAdjacentElement("afterend", reportSection);

    const generateReportButton = $("#btn-generate-report");
    const downloadReportButton = $("#btn-download-report");
    const reportStatus = $("#report-status");
    
    // ── Generate report and open it in a new tab ──
    generateReportButton.addEventListener("click", async () => {
        // Open the tab immediately so the browser doesn't block it.
        const reportTab = window.open("about:blank", "_blank");

        if (!reportTab) {
            reportStatus.textContent =
                "The report tab was blocked. Allow pop-ups for this site and try again.";
            reportStatus.style.color = "#ff9999";
            return;
        }

        generateReportButton.disabled = true;
        generateReportButton.textContent = "Generating...";
        downloadReportButton.disabled = true;
        reportStatus.textContent = "Generating report...";

        try {
            const response = await fetch("/api/report", {
                method: "POST"
            });
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || "Report generation failed.");
            }

            reportStatus.textContent =
                `${data.message} Report contains ${data.rows} rows and ` +
                `${data.columns} columns.`;
            reportStatus.style.color = "#7ee0ad";
            downloadReportButton.disabled = false;

            // Display the generated HTML in the new tab.
            reportTab.location.href = "/api/report-preview";

        } catch (error) {
            reportTab.close();
            reportStatus.textContent = error.message;
            reportStatus.style.color = "#ff9999";
        } finally {
            generateReportButton.disabled = false;
            generateReportButton.textContent = "Generate Report";
        }
    });


    // ── Download report ──
    downloadReportButton.addEventListener("click", async () => {
        downloadReportButton.disabled = true;
        reportStatus.textContent = "Preparing report download...";

        try {
            const response = await fetch("/api/download-report");

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.error || "Report download failed.");
            }

            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            const link = document.createElement("a");

            link.href = url;
            link.download = "autods_report.html";
            document.body.appendChild(link);
            link.click();
            link.remove();
            URL.revokeObjectURL(url);

            reportStatus.textContent = "Report downloaded successfully.";
            reportStatus.style.color = "#7ee0ad";

        } catch (error) {
            reportStatus.textContent = error.message;
            reportStatus.style.color = "#ff9999";
        } finally {
            downloadReportButton.disabled = false;
        }
    });


    const anomalyButton = $("#btn-anomalies");
    const anomalyStatus = $("#anomaly-status");
    const anomalyMetrics = $("#anomaly-metrics");
    const anomalyTable = $("#anomaly-table");

    // ── Run anomaly detection ──
    anomalyButton.addEventListener("click", async () => {
        anomalyButton.disabled = true;
        anomalyButton.textContent = "Detecting...";
        anomalyStatus.textContent = "Analyzing dataset...";
        anomalyMetrics.innerHTML = "";
        anomalyTable.innerHTML = "";

        try {
            const response = await fetch("/api/anomalies", {
                method: "POST"
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(
                    data.error || "Anomaly detection failed."
                );
            }

            anomalyStatus.textContent = data.message;
            anomalyStatus.style.color = "#7ee0ad";

            anomalyMetrics.innerHTML =
                makeMetricHTML("Rows analyzed", data.rows_analyzed) +
                makeMetricHTML("Potential anomalies", data.anomalies_detected) +
                makeMetricHTML(
                    "Anomaly percentage",
                    data.anomaly_percentage + "%"
                );

            anomalyMetrics.innerHTML += makeMetricHTML(
                "Numeric columns used",
                data.numeric_columns_used.length
            );

            const columns = data.anomalies.length
                ? Object.keys(data.anomalies[0])
                : [];

            if (data.anomalies.length && columns.length) {
                anomalyTable.innerHTML =
                    "<table>" +
                    buildTable(columns, data.anomalies) +
                    "</table>";
            } else {
                anomalyTable.innerHTML =
                    '<div class="alert alert-info">' +
                    'No potential anomalies were flagged.' +
                    '</div>';
            }

        } catch (error) {
            anomalyStatus.textContent = error.message;
            anomalyStatus.style.color = "#ff9999";
        } finally {
            anomalyButton.disabled = false;
            anomalyButton.textContent = "Detect Anomalies";
        }
    });


    const cleanButton = $("#btn-clean");
    const downloadCleanButton = $("#btn-download-cleaned");
    const cleanStatus = $("#clean-status");
    const cleanMetrics = $("#clean-metrics");
    const cleanPreview = $("#clean-preview");

    // Reveal cleaning only after profiling has completed.
    const originalRenderProfile = renderProfile;
    renderProfile = function (data) {
        originalRenderProfile(data);
        show(cleaningSection);
    };

    // ── Run cleaning ──
    cleanButton.addEventListener("click", async () => {
        cleanButton.disabled = true;
        cleanButton.textContent = "Cleaning...";
        cleanStatus.textContent = "Processing dataset...";
        cleanMetrics.innerHTML = "";
        cleanPreview.innerHTML = "";
        downloadCleanButton.disabled = true;

        try {
            const response = await fetch("/api/clean", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    missing_strategy: $("#clean-strategy").value,
                    remove_duplicates: $("#clean-duplicates").checked
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || "Cleaning failed.");
            }

            const summary = data.summary;

            cleanStatus.textContent = data.message;
            cleanStatus.style.color = "#7ee0ad";

            cleanMetrics.innerHTML =
                makeMetricHTML("Rows before", summary.rows_before) +
                makeMetricHTML("Rows after", summary.rows_after) +
                makeMetricHTML(
                    "Duplicates removed",
                    summary.duplicates_removed
                ) +
                makeMetricHTML(
                    "Missing values before",
                    summary.missing_before
                ) +
                makeMetricHTML(
                    "Missing values after",
                    summary.missing_after
                );

            
            if (data.preview.length) {
                const headers = data.columns;
                const rows = data.preview;
                let html = '<table class="data-table"><thead><tr>';
                headers.forEach((header) => {
                    html += `<th>${header}</th>`;
                });
                html += '</tr></thead><tbody>';
                rows.forEach((row) => {
                    html += '<tr>';
                    headers.forEach((header) => {
                        const value = row[header] ?? '';
                        html += `<td>${value}</td>`;
                    });
                    html += '</tr>';
                });
                html += '</tbody></table>';
                cleanPreview.innerHTML = html;
            }


            downloadCleanButton.disabled = false;
            show(mlSection);

        } catch (error) {
            cleanStatus.textContent = error.message;
            cleanStatus.style.color = "#ff9999";
        } finally {
            cleanButton.disabled = false;
            cleanButton.textContent = "Run Cleaning";
        }
    });

    // ── Download cleaned CSV ──
    downloadCleanButton.addEventListener("click", async () => {
        downloadCleanButton.disabled = true;
        cleanStatus.textContent = "Preparing download...";

        try {
            const response = await fetch("/api/download-cleaned");

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(
                    errorData.error || "Download failed."
                );
            }

            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            const link = document.createElement("a");

            link.href = url;
            link.download = "cleaned_dataset.csv";
            document.body.appendChild(link);
            link.click();
            link.remove();
            URL.revokeObjectURL(url);

            cleanStatus.textContent = "Cleaned CSV downloaded.";
            cleanStatus.style.color = "#7ee0ad";

        } catch (error) {
            cleanStatus.textContent = error.message;
            cleanStatus.style.color = "#ff9999";
        } finally {
            downloadCleanButton.disabled = false;
        }
    });


    // ── Tab switching ──
    $$(".tab-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            $$(".tab-btn").forEach((b) => b.classList.remove("active"));
            $$(".tab-panel").forEach((p) => p.classList.remove("active"));
            btn.classList.add("active");
            $(`#${btn.dataset.tab}`).classList.add("active");
        });
    });

})();
