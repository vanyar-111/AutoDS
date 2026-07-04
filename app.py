"""
AutoDS — Automated Data Science Pipeline
Streamlit Dashboard (app.py)
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

from backend.profiler import profile_dataset, get_missing_summary, get_type_summary

# ──────────────────────────────────────────────
# Page Config
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="AutoDS — Automated Data Science",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────
# Custom CSS — Dark premium theme
# ──────────────────────────────────────────────
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ── Global ── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f0f1a 0%, #1a1a2e 100%);
    border-right: 1px solid rgba(99, 102, 241, 0.15);
}
section[data-testid="stSidebar"] .stMarkdown h1,
section[data-testid="stSidebar"] .stMarkdown h2,
section[data-testid="stSidebar"] .stMarkdown h3 {
    color: #a5b4fc;
}

/* ── Metric cards ── */
div[data-testid="stMetric"] {
    background: linear-gradient(135deg, rgba(99,102,241,0.08) 0%, rgba(139,92,246,0.06) 100%);
    border: 1px solid rgba(99, 102, 241, 0.2);
    border-radius: 12px;
    padding: 16px 20px;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
div[data-testid="stMetric"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(99, 102, 241, 0.15);
}
div[data-testid="stMetric"] label {
    color: #94a3b8 !important;
    font-weight: 500;
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
    color: #e2e8f0 !important;
    font-weight: 700;
}

/* ── Tabs ── */
button[data-baseweb="tab"] {
    font-family: 'Inter', sans-serif;
    font-weight: 600;
    font-size: 0.85rem;
    letter-spacing: 0.02em;
}

/* ── DataFrames ── */
.stDataFrame {
    border-radius: 10px;
    overflow: hidden;
}

/* ── Expander ── */
details[data-testid="stExpander"] {
    border: 1px solid rgba(99, 102, 241, 0.2) !important;
    border-radius: 10px !important;
    background: rgba(99, 102, 241, 0.03);
}

/* ── File uploader ── */
section[data-testid="stFileUploader"] {
    border: 2px dashed rgba(99, 102, 241, 0.35);
    border-radius: 14px;
    padding: 10px;
    transition: border-color 0.3s ease;
}
section[data-testid="stFileUploader"]:hover {
    border-color: rgba(99, 102, 241, 0.7);
}

/* ── Success / Info / Warning boxes ── */
div[data-testid="stAlert"] {
    border-radius: 10px;
}

/* ── Hero gradient text ── */
.hero-title {
    background: linear-gradient(135deg, #818cf8 0%, #a78bfa 40%, #c084fc 70%, #f472b6 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-size: 2.8rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    line-height: 1.1;
    margin-bottom: 0.2rem;
}
.hero-subtitle {
    color: #94a3b8;
    font-size: 1.05rem;
    font-weight: 400;
    margin-bottom: 1.5rem;
}

/* ── Section headers ── */
.section-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 1.5rem 0 0.8rem 0;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid rgba(99, 102, 241, 0.15);
}
.section-header h2 {
    margin: 0;
    font-size: 1.35rem;
    font-weight: 700;
    color: #c7d2fe;
}

/* ── Status badge ── */
.badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.badge-classification {
    background: rgba(34, 197, 94, 0.12);
    color: #4ade80;
    border: 1px solid rgba(34, 197, 94, 0.3);
}
.badge-regression {
    background: rgba(59, 130, 246, 0.12);
    color: #60a5fa;
    border: 1px solid rgba(59, 130, 246, 0.3);
}

/* ── Pipeline tracker ── */
.pipeline-step {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 14px;
    margin: 4px 0;
    border-radius: 8px;
    font-size: 0.85rem;
    font-weight: 500;
    transition: background 0.2s ease;
}
.pipeline-step.active {
    background: rgba(99, 102, 241, 0.15);
    color: #a5b4fc;
    border-left: 3px solid #818cf8;
}
.pipeline-step.done {
    color: #4ade80;
}
.pipeline-step.pending {
    color: #64748b;
}
</style>
""",
    unsafe_allow_html=True,
)


# ──────────────────────────────────────────────
# Session State Initialization
# ──────────────────────────────────────────────
def init_state():
    defaults = {
        "df": None,
        "profile": None,
        "target_col": None,
        "filename": None,
        "pipeline_stage": 0,  # 0=upload, 1=profiled, 2=cleaned, ...
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_state()

# ──────────────────────────────────────────────
# Sidebar — Pipeline Tracker
# ──────────────────────────────────────────────
with st.sidebar:
    st.markdown('<p class="hero-title" style="font-size:1.6rem;">🧪 AutoDS</p>', unsafe_allow_html=True)
    st.caption("Automated Data Science Pipeline")
    st.markdown("---")

    steps = [
        ("📂", "Upload Dataset"),
        ("🔍", "Dataset Profile"),
        ("🧹", "Cleaning"),
        ("⚙️", "Feature Engineering"),
        ("🤖", "Model Training"),
        ("🎯", "Hyperparameter Tuning"),
        ("📊", "Model Comparison"),
        ("💡", "Explainability"),
        ("📄", "Report"),
    ]

    for i, (icon, label) in enumerate(steps):
        if i < st.session_state.pipeline_stage:
            css = "done"
            symbol = "✓"
        elif i == st.session_state.pipeline_stage:
            css = "active"
            symbol = "►"
        else:
            css = "pending"
            symbol = "○"
        st.markdown(
            f'<div class="pipeline-step {css}">{symbol}&nbsp;&nbsp;{icon} {label}</div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")
    if st.session_state.df is not None:
        st.markdown(f"**Dataset:** `{st.session_state.filename}`")
        st.markdown(f"**Shape:** {st.session_state.df.shape[0]:,} × {st.session_state.df.shape[1]}")

# ──────────────────────────────────────────────
# Main Content
# ──────────────────────────────────────────────

# Hero
st.markdown('<h1 class="hero-title">AutoDS</h1>', unsafe_allow_html=True)
st.markdown(
    '<p class="hero-subtitle">Upload a CSV → get a full ML pipeline with profiling, cleaning, '
    "training, tuning, explainability, and a downloadable report.</p>",
    unsafe_allow_html=True,
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 1 — CSV Upload
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown(
    '<div class="section-header"><h2>📂 Upload Dataset</h2></div>',
    unsafe_allow_html=True,
)

uploaded = st.file_uploader(
    "Drop your CSV file here",
    type=["csv"],
    help="Upload a .csv file to begin the automated ML pipeline.",
)

if uploaded is not None:
    # Only re-read if the file changed
    if st.session_state.filename != uploaded.name:
        df = pd.read_csv(uploaded)
        st.session_state.df = df
        st.session_state.filename = uploaded.name
        st.session_state.profile = None  # reset downstream
        st.session_state.pipeline_stage = 0

    df = st.session_state.df

    st.success(f"✅  **Dataset Loaded Successfully** — `{uploaded.name}`")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Rows", f"{df.shape[0]:,}")
    col2.metric("Columns", f"{df.shape[1]}")
    col3.metric("Total Cells", f"{df.shape[0] * df.shape[1]:,}")
    col4.metric("Memory", f"{df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")

    with st.expander("👀 Preview Data (first 10 rows)", expanded=True):
        st.dataframe(df.head(10), use_container_width=True)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # STEP 2 — Dataset Profiling
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    st.markdown(
        '<div class="section-header"><h2>🔍 Dataset Profile</h2></div>',
        unsafe_allow_html=True,
    )

    # Target column selector
    target_col = st.selectbox(
        "Select Target Column",
        options=df.columns.tolist(),
        index=len(df.columns) - 1,
        help="The column you want to predict. Defaults to the last column.",
    )

    if st.button("🚀 Run Profiler", type="primary", use_container_width=True):
        with st.spinner("Profiling dataset..."):
            report = profile_dataset(df, target_col=target_col)
            st.session_state.profile = report
            st.session_state.target_col = target_col
            st.session_state.pipeline_stage = max(st.session_state.pipeline_stage, 1)

    # ── Display profile results ──
    if st.session_state.profile is not None:
        report = st.session_state.profile

        # Task badge
        badge_css = "badge-classification" if report.task_type == "Classification" else "badge-regression"
        st.markdown(
            f'<span class="badge {badge_css}">● {report.task_type}</span> &nbsp; '
            f'Target: <code>{report.target_column}</code>',
            unsafe_allow_html=True,
        )

        st.markdown("")

        # Overview metrics
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Rows", f"{report.n_rows:,}")
        m2.metric("Columns", report.n_cols)
        m3.metric("Numeric", len(report.numeric_columns))
        m4.metric("Categorical", len(report.categorical_columns))
        m5.metric("Duplicates", f"{report.duplicate_rows:,}")

        # Tabs for detailed views
        tab_missing, tab_types, tab_stats, tab_corr, tab_dist, tab_balance = st.tabs(
            ["🔴 Missing Values", "📋 Data Types", "📈 Statistics", "🔗 Correlations", "📊 Distributions", "⚖️ Class Balance"]
        )

        # ── Missing Values ──
        with tab_missing:
            if report.missing_counts:
                st.warning(
                    f"⚠️ **{len(report.missing_counts)} column(s)** have missing values "
                    f"({report.total_missing:,} total cells)"
                )
                missing_df = pd.DataFrame(get_missing_summary(report))
                st.dataframe(missing_df, use_container_width=True, hide_index=True)

                # Missing values bar chart
                fig = px.bar(
                    missing_df,
                    x="Column",
                    y="Percent (%)",
                    color="Percent (%)",
                    color_continuous_scale=["#818cf8", "#f472b6"],
                    title="Missing Values by Column",
                )
                fig.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#94a3b8",
                    title_font_color="#c7d2fe",
                    xaxis=dict(gridcolor="rgba(99,102,241,0.08)"),
                    yaxis=dict(gridcolor="rgba(99,102,241,0.08)"),
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.success("✅ No missing values — the dataset is complete!")

        # ── Data Types ──
        with tab_types:
            type_df = pd.DataFrame(get_type_summary(report))
            st.dataframe(type_df, use_container_width=True, hide_index=True)

            if report.constant_columns:
                st.warning(
                    f"⚠️ **Constant columns detected:** {', '.join(report.constant_columns)} "
                    "(only 1 unique value — consider removing)"
                )
            if report.high_cardinality_columns:
                st.info(
                    f"ℹ️ **High cardinality:** {', '.join(report.high_cardinality_columns)} "
                    "(>50 unique values — encoding may create many features)"
                )

        # ── Statistics ──
        with tab_stats:
            if report.numeric_stats is not None:
                st.dataframe(report.numeric_stats, use_container_width=True)

                # Skewness table
                if report.skewness:
                    st.markdown("**Skewness & Kurtosis**")
                    sk_df = pd.DataFrame(
                        {
                            "Column": list(report.skewness.keys()),
                            "Skewness": list(report.skewness.values()),
                            "Kurtosis": [report.kurtosis.get(c, None) for c in report.skewness],
                        }
                    )
                    st.dataframe(sk_df, use_container_width=True, hide_index=True)
            else:
                st.info("No numeric columns found.")

        # ── Correlations ──
        with tab_corr:
            if report.correlation_matrix is not None:
                fig = px.imshow(
                    report.correlation_matrix,
                    text_auto=".2f",
                    color_continuous_scale=["#312e81", "#818cf8", "#fef3c7", "#f472b6", "#831843"],
                    aspect="auto",
                    title="Feature Correlation Matrix",
                )
                fig.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#94a3b8",
                    title_font_color="#c7d2fe",
                    height=500,
                )
                st.plotly_chart(fig, use_container_width=True)

                # Highly correlated pairs
                corr = report.correlation_matrix
                pairs = []
                for i in range(len(corr.columns)):
                    for j in range(i + 1, len(corr.columns)):
                        val = corr.iloc[i, j]
                        if abs(val) > 0.7:
                            pairs.append(
                                {
                                    "Feature A": corr.columns[i],
                                    "Feature B": corr.columns[j],
                                    "Correlation": val,
                                }
                            )
                if pairs:
                    st.markdown("**🔗 Highly Correlated Pairs (|r| > 0.7)**")
                    st.dataframe(pd.DataFrame(pairs), use_container_width=True, hide_index=True)
            else:
                st.info("Need at least 2 numeric columns for correlation analysis.")

        # ── Distributions ──
        with tab_dist:
            if report.numeric_columns:
                selected_col = st.selectbox(
                    "Select column",
                    options=report.numeric_columns,
                    key="dist_col",
                )
                fig = px.histogram(
                    df,
                    x=selected_col,
                    nbins=40,
                    marginal="box",
                    color_discrete_sequence=["#818cf8"],
                    title=f"Distribution of {selected_col}",
                )
                fig.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#94a3b8",
                    title_font_color="#c7d2fe",
                    xaxis=dict(gridcolor="rgba(99,102,241,0.08)"),
                    yaxis=dict(gridcolor="rgba(99,102,241,0.08)"),
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No numeric columns to plot.")

        # ── Class Balance ──
        with tab_balance:
            if report.task_type == "Classification" and report.class_balance:
                labels = list(report.class_balance.keys())
                values = list(report.class_balance.values())

                fig = go.Figure(
                    data=[
                        go.Pie(
                            labels=labels,
                            values=values,
                            hole=0.5,
                            marker_colors=["#818cf8", "#f472b6", "#4ade80", "#fbbf24", "#60a5fa"][:len(labels)],
                            textinfo="label+percent",
                            textfont_size=13,
                        )
                    ]
                )
                fig.update_layout(
                    title=f"Class Balance — {report.target_column}",
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#94a3b8",
                    title_font_color="#c7d2fe",
                    height=400,
                )
                st.plotly_chart(fig, use_container_width=True)

                # Imbalance warning
                max_v = max(values)
                min_v = min(values)
                if max_v / max(min_v, 1) > 3:
                    st.warning(
                        "⚠️ **Class imbalance detected** — the majority class is >3× the minority. "
                        "Consider SMOTE or class weights during training."
                    )
            else:
                st.info("Class balance is only shown for Classification tasks.")

        # Profiling done separator
        st.markdown("---")
        st.success("✅ **Profiling complete.** Proceed to the Cleaning step next.")

else:
    # No file uploaded — show landing state
    st.markdown("")
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        st.markdown(
            """
            <div style="text-align:center; padding: 3rem 1rem; border: 2px dashed rgba(99,102,241,0.25);
                        border-radius: 16px; background: rgba(99,102,241,0.03);">
                <p style="font-size: 3rem; margin-bottom: 0.5rem;">📁</p>
                <p style="color: #94a3b8; font-size: 1rem;">
                    Upload a <strong>.csv</strong> file to get started.
                </p>
                <p style="color: #64748b; font-size: 0.8rem; margin-top: 0.5rem;">
                    Supported: any tabular dataset with a target column
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("")
    st.markdown("### 🗺️ Pipeline Overview")
    st.markdown(
        """
| Step | Module | Description |
|------|--------|-------------|
| 1 | **Upload** | Load your CSV dataset |
| 2 | **Profile** | Shape, types, missing values, correlations, class balance |
| 3 | **Clean** | Handle missing data, encode, scale, remove outliers |
| 4 | **Engineer** | Create features, rank importance, drop useless columns |
| 5 | **Train** | Auto-detect task → train multiple models |
| 6 | **Tune** | Optuna hyperparameter optimization (30 trials) |
| 7 | **Compare** | Side-by-side model metrics dashboard |
| 8 | **Explain** | SHAP global + local explanations |
| 9 | **Report** | Download HTML/PDF report |
"""
    )
