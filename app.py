
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


# ============================================================
# 1. PROJECT CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data" / "processed"

MANAGEMENT_REPORT = DATA_DIR / "management_report.json"
PRIORITY_REPORT = DATA_DIR / "management_exception_priorities.csv"
INVESTIGATION_LOG = DATA_DIR / "exception_investigation_log.csv"


# ============================================================
# 2. PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="FinRecon | Financial Operations",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# 3. CUSTOM CSS
# ============================================================

st.markdown("""
<style>

/* Main application */
.stApp {
    background-color: #F4F7FB;
}

/* Hide Streamlit default header and footer */
header[data-testid="stHeader"] {
    background-color: transparent;
}

footer {
    visibility: hidden;
}

#MainMenu {
    visibility: hidden;
}

/* Main content spacing */
.block-container {
    padding-top: 1.5rem;
    padding-bottom: 1rem;
    max-width: 1600px;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #101C35;
    min-width: 245px;
    max-width: 245px;
}

section[data-testid="stSidebar"] * {
    color: #E8EEF9;
}

/* Sidebar buttons */
section[data-testid="stSidebar"] .stButton button {
    width: 100%;
    text-align: left;
    border: none;
    border-radius: 9px;
    padding: 12px 15px;
    background-color: transparent;
    color: #D4DEEF;
    font-weight: 500;
    transition: 0.2s;
}

section[data-testid="stSidebar"] .stButton button:hover {
    background-color: #233B68;
    color: white;
    border: none;
}

section[data-testid="stSidebar"] .stButton button[kind="primary"] {
    background-color: #2563EB;
    color: white;
}

/* Titles */
h1 {
    color: #17243D;
    font-weight: 750;
    letter-spacing: -0.8px;
}

h2, h3 {
    color: #1E2B45;
    font-weight: 650;
}

/* Metric cards */
div[data-testid="stMetric"] {
    background-color: white;
    border: 1px solid #E5EAF2;
    border-radius: 12px;
    padding: 17px 18px;
    box-shadow: 0 2px 8px rgba(20, 40, 80, 0.04);
}

div[data-testid="stMetricLabel"] {
    color: #64748B;
    font-size: 13px;
}

div[data-testid="stMetricValue"] {
    color: #17243D;
    font-weight: 750;
}

/* Dataframes */
div[data-testid="stDataFrame"] {
    border: 1px solid #E5EAF2;
    border-radius: 10px;
    overflow: hidden;
}

/* Inputs */
div[data-baseweb="select"] > div,
div[data-baseweb="input"] > div,
div[data-baseweb="textarea"] {
    border-radius: 8px;
}

/* Main buttons */
.stButton button,
.stFormSubmitButton button {
    border-radius: 8px;
    font-weight: 600;
}

/* Dividers */
hr {
    border-color: #E5EAF2;
}

/* Information cards */
.info-card {
    background: white;
    border: 1px solid #E5EAF2;
    border-radius: 12px;
    padding: 18px;
    margin-bottom: 12px;
    box-shadow: 0 2px 8px rgba(20, 40, 80, 0.03);
}

.small-label {
    color: #64748B;
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.small-value {
    color: #17243D;
    font-size: 23px;
    font-weight: 750;
    margin-top: 5px;
}

/* Sidebar brand */
.brand {
    font-size: 25px;
    font-weight: 800;
    color: white;
    padding: 8px 5px 4px 5px;
}

.brand-subtitle {
    color: #94A9CA;
    font-size: 11px;
    padding-left: 5px;
    margin-bottom: 25px;
}

.section-caption {
    color: #7D91B2;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.2px;
    margin: 18px 0 8px 5px;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# 4. LOAD DATA
# ============================================================

def load_json_report():

    if not MANAGEMENT_REPORT.exists():
        return {}

    try:
        with open(MANAGEMENT_REPORT, "r", encoding="utf-8") as file:
            return json.load(file)

    except (json.JSONDecodeError, OSError):
        return {}


def load_exceptions():

    if not PRIORITY_REPORT.exists():
        return pd.DataFrame()

    try:
        return pd.read_csv(PRIORITY_REPORT)

    except (OSError, pd.errors.ParserError):
        return pd.DataFrame()


def load_investigations():

    if not INVESTIGATION_LOG.exists():
        return pd.DataFrame()

    try:
        return pd.read_csv(INVESTIGATION_LOG)

    except (OSError, pd.errors.ParserError):
        return pd.DataFrame()


report = load_json_report()
exceptions = load_exceptions()
investigations = load_investigations()

reconciliation = report.get("reconciliation", {})
outstanding = report.get("outstanding_exceptions", {})
financial = report.get("financial_exposure_php", {})
analyst = report.get("analyst_review", {})

recommendations = report.get("management_recommendations", [])


# ============================================================
# 5. NAVIGATION STATE
# ============================================================

if "page" not in st.session_state:
    st.session_state.page = "Overview"


def navigate(page):
    st.session_state.page = page


# ============================================================
# 6. SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        '<div class="brand">◈ FinRecon</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="brand-subtitle">FINANCIAL OPERATIONS PLATFORM</div>',
        unsafe_allow_html=True
    )

    st.markdown('<div class="section-caption">WORKSPACE</div>',
                unsafe_allow_html=True)

    pages = [
        ("▦", "Overview"),
        ("⇄", "Reconciliation"),
        ("⚑", "Exception Queue"),
        ("✓", "Investigation"),
        ("▤", "Management Reports"),
        ("◷", "Audit History")
    ]

    for symbol, page in pages:

        label = f"{symbol}   {page}"

        st.button(
            label,
            key=f"nav_{page}",
            type="primary" if st.session_state.page == page else "secondary",
            use_container_width=True,
            on_click=navigate,
            args=(page,)
        )

    st.markdown("---")

    st.markdown(
        '<div class="section-caption">SYSTEM STATUS</div>',
        unsafe_allow_html=True
    )

    st.markdown("🟢 Reconciliation engine")

    st.markdown("🟢 Management reporting")

    st.markdown("🟢 Exception monitoring")

    st.markdown("---")

    st.caption("FinRecon Platform v1.0")
    st.caption("Financial data operations")


# ============================================================
# 7. REUSABLE COMPONENTS
# ============================================================

def page_header(title, subtitle):

    st.title(title)
    st.caption(subtitle)
    st.divider()


def money(value):

    try:
        return f"₱{float(value):,.2f}"

    except (ValueError, TypeError):
        return "₱0.00"


def show_kpis(items):

    columns = st.columns(len(items))

    for column, (label, value, help_text) in zip(columns, items):

        with column:
            st.metric(
                label=label,
                value=value,
                help=help_text
            )


def get_exception_id(row):

    for field in [
        "transaction_id_bank",
        "transaction_id_gateway",
        "transaction_id"
    ]:

        value = row.get(field)

        if pd.notna(value) and str(value).strip():
            return str(value)

    return "Unknown transaction"


# ============================================================
# 8. OVERVIEW PAGE
# ============================================================

def overview_page():

    page_header(
        "Financial Operations Overview",
        "Monitor reconciliation performance and financial exceptions."
    )

    if not report:
        st.error("Management report not found. Generate it first.")
        return

    show_kpis([
        (
            "Total Output Records",
            f"{reconciliation.get('total_output_records', 0):,}",
            "Total rows in the reconciled output."
        ),
        (
            "Matched Pairs",
            f"{reconciliation.get('total_matched_pairs', 0):,}",
            "Exact and approved fuzzy matches."
        ),
        (
            "Outstanding Exceptions",
            f"{sum([
                outstanding.get('missing_in_gateway', 0),
                outstanding.get('missing_in_bank', 0),
                outstanding.get('amount_mismatches', 0),
                outstanding.get('date_mismatches', 0),
                outstanding.get('combined_mismatches', 0),
                outstanding.get('duplicates', 0)
            ]):,}",
            "Exceptions requiring attention."
        ),
        (
            "Output-row Match Rate",
            f"{reconciliation.get('output_row_match_rate_percent', 0):.2f}%",
            "Matched pairs divided by output rows."
        )
    ])

    st.write("")

    left, right = st.columns([1.5, 1])

    with left:

        st.subheader("Exception Distribution")

        chart_data = pd.DataFrame({
            "Exception": [
                "Missing in Gateway",
                "Missing in Bank",
                "Amount Mismatch",
                "Date Mismatch",
                "Combined Mismatch",
                "Duplicates"
            ],
            "Count": [
                outstanding.get("missing_in_gateway", 0),
                outstanding.get("missing_in_bank", 0),
                outstanding.get("amount_mismatches", 0),
                outstanding.get("date_mismatches", 0),
                outstanding.get("combined_mismatches", 0),
                outstanding.get("duplicates", 0)
            ]
        })

        fig = px.bar(
            chart_data,
            x="Exception",
            y="Count",
            color="Count",
            color_continuous_scale=["#BFDBFE", "#2563EB"],
            text="Count"
        )

        fig.update_layout(
            height=330,
            showlegend=False,
            coloraxis_showscale=False,
            plot_bgcolor="white",
            paper_bgcolor="white",
            margin=dict(l=10, r=10, t=15, b=10),
            xaxis_title="",
            yaxis_title="Number of records"
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
            config={"displayModeBar": False}
        )

    with right:

        st.subheader("Financial Investigation Exposure")

        exposure_data = pd.DataFrame({
            "Category": [
                "Amount Mismatches",
                "Missing in Gateway",
                "Missing in Bank"
            ],
            "Amount": [
                financial.get("amount_mismatch_exposure", 0),
                financial.get("missing_gateway_value", 0),
                financial.get("missing_bank_value", 0)
            ]
        })

        fig = px.pie(
            exposure_data,
            names="Category",
            values="Amount",
            hole=0.62,
            color_discrete_sequence=[
                "#2563EB",
                "#F59E0B",
                "#14B8A6"
            ]
        )

        fig.update_layout(
            height=330,
            paper_bgcolor="white",
            margin=dict(l=5, r=5, t=15, b=5),
            legend=dict(orientation="h", y=-0.08)
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
            config={"displayModeBar": False}
        )

    st.subheader("Analyst Review Performance")

    show_kpis([
        (
            "Candidates Reviewed",
            f"{analyst.get('candidates_reviewed', 0):,}",
            "Candidates reviewed by analysts."
        ),
        (
            "Approved",
            f"{analyst.get('approved', 0):,}",
            "Fuzzy candidates approved."
        ),
        (
            "Rejected",
            f"{analyst.get('rejected', 0):,}",
            "Fuzzy candidates rejected."
        ),
        (
            "Acceptance Rate",
            f"{analyst.get('acceptance_rate_percent', 0):.2f}%",
            "Share of latest decisions approved."
        )
    ])

    st.caption(
        "Financial investigation exposure is not confirmed financial loss."
    )


# ============================================================
# 9. RECONCILIATION PAGE
# ============================================================

def reconciliation_page():

    page_header(
        "Reconciliation",
        "Review the results of exact and fuzzy transaction matching."
    )

    show_kpis([
        (
            "Exact Matches",
            f"{reconciliation.get('exact_matches', 0):,}",
            "Exact transaction matches."
        ),
        (
            "Fuzzy Matches",
            f"{reconciliation.get('approved_fuzzy_matches', 0):,}",
            "Human-approved fuzzy matches."
        ),
        (
            "Total Matched",
            f"{reconciliation.get('total_matched_pairs', 0):,}",
            "Combined exact and fuzzy matches."
        ),
        (
            "Match Rate",
            f"{reconciliation.get('output_row_match_rate_percent', 0):.2f}%",
            "Output-row match rate."
        )
    ])

    st.subheader("Outstanding Exception Counts")

    data = pd.DataFrame({
        "Exception Type": [
            "Missing in Gateway",
            "Missing in Bank",
            "Amount Mismatch",
            "Date Mismatch",
            "Combined Mismatch",
            "Duplicates"
        ],
        "Records": [
            outstanding.get("missing_in_gateway", 0),
            outstanding.get("missing_in_bank", 0),
            outstanding.get("amount_mismatches", 0),
            outstanding.get("date_mismatches", 0),
            outstanding.get("combined_mismatches", 0),
            outstanding.get("duplicates", 0)
        ]
    })

    st.dataframe(
        data,
        use_container_width=True,
        hide_index=True,
        height=300
    )


# ============================================================
# 10. EXCEPTION QUEUE PAGE
# ============================================================

def exception_queue_page():

    page_header(
        "Exception Queue",
        "Review and prioritize transactions that need attention."
    )

    if exceptions.empty:
        st.success("No exception records available.")
        return

    high_count = (
        int((exceptions["priority"] == "HIGH").sum())
        if "priority" in exceptions.columns else 0
    )

    normal_count = (
        int((exceptions["priority"] == "NORMAL").sum())
        if "priority" in exceptions.columns else 0
    )

    total_value = pd.to_numeric(
        exceptions.get(
            "investigation_value",
            pd.Series(dtype=float)
        ),
        errors="coerce"
    ).fillna(0).sum()

    show_kpis([
        ("Total Exceptions", f"{len(exceptions):,}", "All outstanding exceptions."),
        ("Investigation Amount", money(total_value), "Indicative investigation value."),
        ("High Priority", f"{high_count:,}", "Exceptions above the priority threshold."),
        ("Normal Priority", f"{normal_count:,}", "Other exceptions.")
    ])

    st.write("")

    filter1, filter2 = st.columns([1, 2])

    with filter1:

        priority = st.selectbox(
            "Priority",
            ["ALL", "HIGH", "NORMAL"]
        )

    with filter2:

        search = st.text_input(
            "Search transaction",
            placeholder="Enter a bank or gateway transaction ID..."
        )

    filtered = exceptions.copy()

    if priority != "ALL" and "priority" in filtered.columns:

        filtered = filtered[
            filtered["priority"] == priority
        ]

    search_fields = [
        column for column in [
            "transaction_id_bank",
            "transaction_id_gateway",
            "transaction_id"
        ]
        if column in filtered.columns
    ]

    if search and search_fields:

        mask = pd.Series(False, index=filtered.index)

        for field in search_fields:

            mask |= (
                filtered[field]
                .astype(str)
                .str.contains(search, case=False, na=False)
            )

        filtered = filtered[mask]

    st.subheader(f"{len(filtered):,} Exceptions")

    preferred_columns = [
        "priority",
        "transaction_date",
        "transaction_id_bank",
        "transaction_id_gateway",
        "amount_bank",
        "amount_gateway",
        "variance",
        "investigation_value",
        "status",
        "exception_reason"
    ]

    display_columns = [
        column for column in preferred_columns
        if column in filtered.columns
    ]

    st.dataframe(
        filtered[display_columns],
        use_container_width=True,
        hide_index=True,
        height=390
    )

    if not filtered.empty:

        selected_index = st.selectbox(
            "Select exception for investigation",
            filtered.index.tolist(),
            format_func=lambda idx: (
                f"{get_exception_id(filtered.loc[idx])} "
                f"| {filtered.loc[idx].get('priority', 'N/A')}"
            )
        )

        if st.button("Open Investigation", type="primary"):
            st.session_state.selected_exception = selected_index
            navigate("Investigation")
            st.rerun()


# ============================================================
# 11. INVESTIGATION PAGE
# ============================================================

def investigation_page():

    page_header(
        "Exception Investigation",
        "Examine transaction details and document investigation decisions."
    )

    if exceptions.empty:
        st.info("There are no exceptions to investigate.")
        return

    if "selected_exception" in st.session_state:

        selected_index = st.session_state.selected_exception

        if selected_index in exceptions.index:
            selected = exceptions.loc[selected_index]
        else:
            selected = exceptions.iloc[0]

    else:
        selected = None

    if selected is None:

        selected_index = st.selectbox(
            "Choose an exception",
            exceptions.index.tolist(),
            format_func=lambda idx: get_exception_id(exceptions.loc[idx])
        )

        selected = exceptions.loc[selected_index]

    st.subheader("Transaction Information")

    left, right = st.columns(2)

    with left:

        st.markdown("#### Bank Record")

        st.metric(
            "Bank Amount",
            money(selected.get("amount_bank", 0))
        )

        st.write(
            "**Bank Transaction ID:**",
            selected.get("transaction_id_bank", "N/A")
        )

    with right:

        st.markdown("#### Gateway Record")

        st.metric(
            "Gateway Amount",
            money(selected.get("amount_gateway", 0))
        )

        st.write(
            "**Gateway Transaction ID:**",
            selected.get("transaction_id_gateway", "N/A")
        )

    st.divider()

    st.markdown("#### Exception Analysis")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Priority",
        str(selected.get("priority", "N/A"))
    )

    col2.metric(
        "Variance",
        money(selected.get("variance", 0))
    )

    col3.metric(
        "Investigation Value",
        money(selected.get("investigation_value", 0))
    )

    st.info(
        str(selected.get("exception_reason", "No exception reason available."))
    )

    st.divider()

    st.markdown("#### Investigation Form")

    with st.form("investigation_form"):

        reviewer = st.text_input("Analyst / Reviewer")

        action = st.selectbox(
            "Investigation Status",
            [
                "UNDER_INVESTIGATION",
                "RESOLVED",
                "ESCALATED",
                "PENDING_INFORMATION"
            ]
        )

        resolution_code = st.selectbox(
            "Resolution Code",
            [
                "NOT_YET_DETERMINED",
                "BANK_POSTING_DELAY",
                "GATEWAY_SETTLEMENT_DELAY",
                "INCORRECT_AMOUNT",
                "INCORRECT_TRANSACTION_DATE",
                "DUPLICATE_TRANSACTION",
                "OTHER"
            ]
        )

        notes = st.text_area(
            "Investigation Notes",
            placeholder="Describe the evidence, findings, and action taken..."
        )

        submitted = st.form_submit_button(
            "Save Investigation",
            type="primary"
        )

        if submitted:

            if not reviewer.strip() or not notes.strip():

                st.error(
                    "Analyst name and investigation notes are required."
                )

            else:

                record = {
                    "investigation_id": str(uuid.uuid4()),
                    "investigated_at": datetime.now(
                        timezone.utc
                    ).isoformat(),
                    "transaction_id": get_exception_id(selected),
                    "reviewer": reviewer,
                    "action": action,
                    "resolution_code": resolution_code,
                    "notes": notes,
                    "investigation_value": selected.get(
                        "investigation_value", 0
                    )
                }

                pd.DataFrame([record]).to_csv(
                    INVESTIGATION_LOG,
                    mode="a",
                    header=not INVESTIGATION_LOG.exists(),
                    index=False
                )

                st.success("Investigation saved successfully.")

                st.rerun()


# ============================================================
# 12. MANAGEMENT REPORTS PAGE
# ============================================================

def management_reports_page():

    page_header(
        "Management Reports",
        "Financial exposure, analyst performance, and recommended actions."
    )

    st.subheader("Financial Investigation Exposure")

    show_kpis([
        (
            "Amount Mismatch",
            money(financial.get("amount_mismatch_exposure", 0)),
            "Amount discrepancy exposure."
        ),
        (
            "Missing in Gateway",
            money(financial.get("missing_gateway_value", 0)),
            "Bank-side transactions absent from gateway."
        ),
        (
            "Missing in Bank",
            money(financial.get("missing_bank_value", 0)),
            "Gateway-side transactions absent from bank."
        ),
        (
            "Gross Investigation",
            money(financial.get("gross_investigation_amount", 0)),
            "Gross amount requiring investigation."
        )
    ])

    st.divider()

    st.subheader("Management Recommendations")

    if recommendations:

        for index, recommendation in enumerate(recommendations, 1):

            st.markdown(
                f"""
                <div class="info-card">
                    <span class="small-label">ACTION {index}</span>
                    <div style="color:#17243D; font-weight:600; margin-top:7px;">
                        {recommendation}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

    else:
        st.info("No recommendations available.")

    st.divider()

    if report:

        st.download_button(
            "Download Management Report (JSON)",
            data=json.dumps(report, indent=4),
            file_name="management_report.json",
            mime="application/json",
            use_container_width=False
        )

    if not exceptions.empty:

        st.download_button(
            "Download Exception Report (CSV)",
            data=exceptions.to_csv(index=False),
            file_name="management_exception_priorities.csv",
            mime="text/csv"
        )

    st.caption(
        "Investigation exposure is not confirmed financial loss."
    )


# ============================================================
# 13. AUDIT HISTORY PAGE
# ============================================================

def audit_history_page():

    page_header(
        "Investigation History",
        "Review investigation records submitted by analysts."
    )

    if investigations.empty:

        st.info(
            "No investigation records have been submitted yet."
        )

        return

    show_kpis([
        (
            "Total Investigations",
            f"{len(investigations):,}",
            "Saved investigation records."
        ),
        (
            "Resolved",
            f"{(investigations['action'] == 'RESOLVED').sum():,}"
            if "action" in investigations.columns else "0",
            "Investigations marked resolved."
        ),
        (
            "Escalated",
            f"{(investigations['action'] == 'ESCALATED').sum():,}"
            if "action" in investigations.columns else "0",
            "Investigations escalated."
        ),
        (
            "Pending",
            f"{(investigations['action'] == 'PENDING_INFORMATION').sum():,}"
            if "action" in investigations.columns else "0",
            "Investigations waiting for information."
        )
    ])

    st.subheader("Investigation Records")

    st.dataframe(
        investigations,
        use_container_width=True,
        hide_index=True,
        height=400
    )

    st.download_button(
        "Export Investigation History",
        data=investigations.to_csv(index=False),
        file_name="investigation_history.csv",
        mime="text/csv"
    )


# ============================================================
# 14. ROUTE SELECTED PAGE
# ============================================================

selected_page = st.session_state.page

if selected_page == "Overview":
    overview_page()

elif selected_page == "Reconciliation":
    reconciliation_page()

elif selected_page == "Exception Queue":
    exception_queue_page()

elif selected_page == "Investigation":
    investigation_page()

elif selected_page == "Management Reports":
    management_reports_page()

elif selected_page == "Audit History":
    audit_history_page()


# ============================================================
# 15. FOOTER
# ============================================================

st.divider()

st.caption(
    "FinRecon | Financial Reconciliation & Exception Management Platform"
)
