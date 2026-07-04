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

    const sidebarInfo = $("#sidebar-info");
    const sidebarFilename = $("#sidebar-filename");
    const sidebarShape = $("#sidebar-shape");

    let currentStage = 0;

    // ── Pipeline step tracker ──
    function setStage(stage) {
        currentStage = stage;
        $$(".pipeline-step").forEach((el) => {
            const s = parseInt(el.dataset.step);
            el.classList.remove("active", "done");
            if (s < stage) el.classList.add("done");
            else if (s === stage) el.classList.add("active");
        });
    }

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
        let html = "<thead><tr>";
        headers.forEach((h) => (html += `<th>${h}</th>`));
        html += "</tr></thead><tbody>";
        rows.forEach((row) => {
            html += "<tr>";
            headers.forEach((h) => {
                let val = row[h];
                if (val === null || val === undefined) val = "";
                html += `<td>${val}</td>`;
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
            if (data.preview.length) {
                const headers = Object.keys(data.preview[0]);
                previewTable.innerHTML = buildTable(headers, data.preview);
            }

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

            // Sidebar
            sidebarFilename.textContent = data.filename;
            sidebarShape.textContent = `${formatNum(data.rows)} x ${data.columns}`;
            show(sidebarInfo);

            setStage(1);
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
            setStage(2);
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
