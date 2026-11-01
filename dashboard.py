from __future__ import annotations
import os
from pathlib import Path
from urllib.parse import urlsplit
import pandas as pd
import plotly.express as px
import streamlit as st


PROJECT_DIR = Path(__file__).resolve().parent
DEFAULT_CSV = PROJECT_DIR / "data" / "ai_policy_activity_candidates.csv"
CSV_PATH = Path(os.getenv("DASHBOARD_CSV_PATH", str(DEFAULT_CSV))).expanduser()
PAGE_SIZE_DEFAULT = 12

st.set_page_config(page_title="India AI Policy Activity Tracker",page_icon="🇮🇳",layout="wide",initial_sidebar_state="expanded",)


NAVY = "#172B4D"
BLUE = "#2563EB"
PALETTE = ["#2563EB", "#0F766E", "#7C3AED", "#D97706", "#0891B2", "#DB2777", "#475569"]

COLUMN_ALIASES = {
    "state": ["state", "state_name", "region"],
    "headline": ["headline", "title", "news_title"],
    "date": ["date", "published_date", "publication_date", "published_at"],
    "source_name": ["source_name", "source", "publisher", "news_source"],
    "source_url": ["source_url", "url", "article_url", "link"],
    "summary": ["summary", "description", "snippet", "article_summary"],
    "activity_type": ["activity_type", "category", "policy_category"],
    "activity_types": ["activity_types", "categories"],
    "policy_stage": ["policy_stage", "stage", "implementation_stage"],
    "screening_decision": ["screening_decision", "decision"],
    "screening_confidence": ["screening_confidence", "confidence"],
    "manual_review_status": ["manual_review_status", "review_status"],
    "relevance_reason": ["relevance_reason", "classification_reason"],
    "ev_excerpt": ["ev_excerpt", "ev", "matched_text"],
    "ai_ev_terms": ["ai_ev_terms"],
    "government_ev_terms": ["government_ev_terms"],
    "activity_ev_terms": ["activity_ev_terms"],
    "also_reported_by": ["also_reported_by", "other_sources"],}

def safe_http_url(value: object) -> str:
    """Only return well-formed HTTP(S) URLs; all other values are non-clickable."""
    raw = str(value or "").strip()
    try:
        parsed = urlsplit(raw)
        if parsed.scheme.lower() in {"http", "https"} and parsed.netloc and " " not in raw:
            return raw
    except ValueError:
        pass
    return ""

def first_existing_column(columns: list[str], candidates: list[str]) -> str | None:
    lookup = {str(col).strip().lower(): str(col) for col in columns}
    for candidate in candidates:
        if candidate.lower() in lookup:
            return lookup[candidate.lower()]
    return None


@st.cache_data(show_spinner=False)
def load_dataset(path_string: str, modified_time: float) -> tuple[pd.DataFrame, list[str]]:
    """Load CSV and map notebook column names to the dashboard's canonical schema."""
    del modified_time  # included in the cache key so changed files are reloaded
    path = Path(path_string)
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")

    try:
        raw = pd.read_csv(path, dtype=str, encoding="utf-8-sig", keep_default_na=False, on_bad_lines="warn")
    except UnicodeDecodeError:
        raw = pd.read_csv(path, dtype=str, encoding="utf-8", keep_default_na=False, on_bad_lines="warn")

    if raw.empty:
        raise ValueError("The CSV contains a header but no data records.")

    mapped = pd.DataFrame(index=raw.index)
    missing_optional: list[str] = []
    for canonical, aliases in COLUMN_ALIASES.items():
        source = first_existing_column(list(raw.columns), aliases)
        if source is not None:
            mapped[canonical] = raw[source].astype(str).str.strip()
        else:
            mapped[canonical] = ""
            if canonical in {"state", "headline", "date", "source_name", "source_url", "summary", "activity_type"}:
                missing_optional.append(canonical)

    # Preserve every original field for exports and auditability.
    for col in raw.columns:
        if col not in mapped.columns:
            mapped[col] = raw[col].astype(str)

    mapped["state"] = mapped["state"].replace("", "State not specified")
    mapped["headline"] = mapped["headline"].replace("", "Untitled announcement")
    mapped["source_name"] = mapped["source_name"].replace("", "Source not specified")
    mapped["activity_type"] = mapped["activity_type"].replace("", "Not classified")
    mapped["policy_stage"] = mapped["policy_stage"].replace("", "Stage not specified")
    mapped["summary"] = mapped["summary"].replace("", "No summary was provided in the feed.")
    mapped["date_prs"] = pd.to_datetime(mapped["date"], errors="coerce", utc=True).dt.tz_convert(None)
    mapped["date_display"] = mapped["date_prs"].dt.strftime("%d %b %Y")
    mapped["date_display"] = mapped["date_display"].fillna("Date unavailable")
    mapped["safe_url"] = mapped["source_url"].map(safe_http_url)
    mapped["search_blob"] = (
        mapped["headline"].fillna("") + " " + mapped["summary"].fillna("") + " "
        + mapped["relevance_reason"].fillna("") + " " + mapped["ev_excerpt"].fillna("")
    ).str.casefold()
    return mapped.reset_index(drop=True), missing_optional


def pretty_count(value: int) -> str:
    return f"{value:,}"

if not CSV_PATH.is_absolute():
    CSV_PATH = (PROJECT_DIR / CSV_PATH).resolve()

if not CSV_PATH.exists():
    st.error(
        f"Could not find the dashboard dataset at `{CSV_PATH}`. "
        "Run `./run_pipeline.sh` (or `./run.ps1` on Windows) to execute the notebook and copy its CSV."
    )
    st.stop()

try:
    DATA, MISSING_FIELDS = load_dataset(str(CSV_PATH), CSV_PATH.stat().st_mtime)
except Exception as exc:  # show a useful UI error instead of a Python traceback
    st.error(f"Unable to load the dataset: {exc}")
    st.stop()

st.markdown(
    """
    <style>
      .block-container {padding-top: 1.7rem; padding-bottom: 2.5rem; max-width: 1500px;}
      h1, h2, h3 {color: #172B4D; letter-spacing: -0.02em;}
      [data-testid="stMetric"] {background: #F7FAFF; border: 1px solid #E4EAF4; padding: 14px 16px; border-radius: 12px;}
      [data-testid="stMetricl"] {color: #53657D;}
      div[data-testid="stExpander"] {border: 1px solid #E4EAF4; border-radius: 10px;}
      .small-muted {color: #64748B; font-size: 0.88rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("India AI Policy Activity Tracker")
st.caption("A news-based view of AI policy announcements, public-sector deployments, partnerships and related state activity.")

file_time = pd.Timestamp(CSV_PATH.stat().st_mtime, unit="s")
col_file, col_total, col_review = st.columns([2, 2, 3])
with col_file:
    st.caption(f"Dataset file updated: **{file_time.strftime('%d %b %Y, %I:%M %p')}**")
with col_total:
    st.caption(f"Loaded source records: **{pretty_count(len(DATA))}**")
with col_review:
    st.caption("Screening output: **candidates awaiting human verification**")

st.warning(
    "Interpretation note: these are machine-screened news candidates, not a verified inventory of state policies. "
    "Open the original article and confirm the state-government actor, activity and policy stage before citing a record."
)
if MISSING_FIELDS:
    st.info("Some expected columns were absent and have been left blank: " + ", ".join(MISSING_FIELDS))





st.sidebar.header("Explore the dataset")
search_text = st.sidebar.text_input("Search headlines, summaries or ev", placeholder="e.g. AI centre, agriculture, MoU")

states = sorted(DATA["state"].dropna().unique().tolist())
categories = sorted(DATA["activity_type"].dropna().unique().tolist())
stages = sorted(DATA["policy_stage"].dropna().unique().tolist())
sources = sorted(DATA["source_name"].dropna().unique().tolist())

selected_states = st.sidebar.multiselect("State", states, default=[])
selected_categories = st.sidebar.multiselect("Activity category", categories, default=[])
selected_stages = st.sidebar.multiselect("Policy stage", stages, default=[])
selected_sources = st.sidebar.multiselect("Publisher", sources, default=[])

valid_dates = DATA["date_prs"].dropna()
s_d_r = None
if not valid_dates.empty:
    min_date = valid_dates.min().date()
    max_date = valid_dates.max().date()
    s_d_r = st.sidebar.date_input("Publication date range",value=(min_date, max_date),min_value=min_date,max_value=max_date,)

sort_order = st.sidebar.radio("Sort records", ["Newest first", "Oldest first"], horizontal=False)
if st.sidebar.button("Reset all filters", use_container_width=True):
    st.rerun()

flt = DATA.copy()
if search_text.strip():
    flt = flt[flt["search_blob"].str.contains(search_text.strip().casefold(), regex=False, na=False)]
if selected_states:
    flt = flt[flt["state"].isin(selected_states)]
if selected_categories:
    flt = flt[flt["activity_type"].isin(selected_categories)]
if selected_stages:
    flt = flt[flt["policy_stage"].isin(selected_stages)]
if selected_sources:
    flt = flt[flt["source_name"].isin(selected_sources)]
if isinstance(s_d_r, (tuple, list)) and len(s_d_r) == 2:
    start_date, end_date = s_d_r
    flt = flt[
        flt["date_prs"].notna()
        & (flt["date_prs"].dt.date >= start_date)
        & (flt["date_prs"].dt.date <= end_date)
    ]

ascending = sort_order == "Oldest first"
flt = flt.sort_values("date_prs", ascending=ascending, na_position="last", kind="stable")



def unique_count(series: pd.Series) -> int:
    values = series.astype(str).str.strip()
    return int(values[~values.isin(["", "State not specified", "Source not specified", "Not classified"])].nunique())


latest_date = flt["date_prs"].max() if not flt["date_prs"].dropna().empty else pd.NaT
pending = int(
    flt.get("manual_review_status", pd.Series(index=flt.index, dtype=str))
    .astype(str).str.contains("pending|review|verify", case=False, regex=True).sum()
)




st.subheader("Policy activity analytics")
if flt.empty:
    st.info("No records match the selected filters. Reset or broaden the filters to see the dataset.")
else:
    left, right = st.columns(2)
    with left:
        state_counts = flt.groupby("state").size().reset_index(name="records").sort_values("records", ascending=True)
        fig_state = px.bar(
            state_counts.tail(18), x="records", y="state", orientation="h",
            title="Candidate records by state", text="records",
            color_discrete_sequence=[BLUE],
        )
        fig_state.update_layout(height=500, margin=dict(l=8, r=12, t=55, b=10), xaxis_title="Records", yaxis_title="")
        fig_state.update_traces(textposition="outside", cliponaxis=False)
        st.plotly_chart(fig_state, use_container_width=True)

    with right:
        category_counts = flt.groupby("activity_type").size().reset_index(name="records").sort_values("records", ascending=False)
        fig_category = px.pie(
            category_counts, names="activity_type", values="records", hole=0.58,
            title="Activity category mix", color_discrete_sequence=PALETTE,
        )
        fig_category.update_traces(textposition="inside", textinfo="percent+value", hovertemplate="%{l}<br>%{value} records<br>%{percent}<extra></extra>")
        fig_category.update_layout(height=500, margin=dict(l=8, r=8, t=55, b=8), legend_title_text="Activity type")
        st.plotly_chart(fig_category, use_container_width=True)

    left, right = st.columns(2)
    with left:
        dated = flt.dropna(subset=["date_prs"]).copy()
        aggregation = st.radio("Timeline grouping", ["Weekly", "Monthly"], horizontal=True, key="timeline_group")
        if dated.empty:
            st.info("No valid publication dates to display in the timeline.")
        else:
            freq = "W-MON" if aggregation == "Weekly" else "MS"
            dated["period"] = dated["date_prs"].dt.to_period("W-MON" if aggregation == "Weekly" else "M").dt.start_time
            timeline = dated.groupby("period").size().reset_index(name="records").sort_values("period")
            fig_timeline = px.area(timeline, x="period", y="records", title=f"Publication timeline ({aggregation.lower()})", markers=True, color_discrete_sequence=[BLUE])
            fig_timeline.update_layout(height=360, margin=dict(l=8, r=8, t=55, b=8), xaxis_title="Publication period", yaxis_title="Records")
            st.plotly_chart(fig_timeline, use_container_width=True)

    with right:
        stage_counts = flt.groupby("policy_stage").size().reset_index(name="records").sort_values("records", ascending=True)
        fig_stage = px.bar(stage_counts, x="records", y="policy_stage", orientation="h", title="Reported policy stage", text="records", color_discrete_sequence=["#0F766E"])
        fig_stage.update_layout(height=360, margin=dict(l=8, r=12, t=55, b=8), xaxis_title="Records", yaxis_title="")
        fig_stage.update_traces(textposition="outside", cliponaxis=False)
        st.plotly_chart(fig_stage, use_container_width=True)

    source_counts = flt.groupby("source_name").size().reset_index(name="records").sort_values("records", ascending=False).head(12)
    fig_sources = px.bar(source_counts.sort_values("records", ascending=True), x="records", y="source_name", orientation="h", title="Top publishers in the current selection", text="records", color_discrete_sequence=["#7C3AED"])
    fig_sources.update_layout(height=390, margin=dict(l=8, r=12, t=55, b=8), xaxis_title="Records", yaxis_title="")
    fig_sources.update_traces(textposition="outside", cliponaxis=False)
    st.plotly_chart(fig_sources, use_container_width=True)



st.divider()
st.subheader("News and policy activity explorer")
explorer_col, export_all_col, export_flt_col = st.columns([2, 1, 1])
with explorer_col:
    st.caption(f"Showing **{pretty_count(len(flt))}** flt records from **{pretty_count(len(DATA))}** loaded records.")
with export_all_col:
    st.download_button(
        "Download full CSV",
        data=DATA.drop(columns=["date_prs", "date_display", "safe_url", "search_blob"], errors="ignore").to_csv(index=False).encode("utf-8-sig"),
        file_name="ai_policy_activity_candidates_full.csv",
        mime="text/csv",
        use_container_width=True,
    )
with export_flt_col:
    st.download_button(
        "Download flt CSV",
        data=flt.drop(columns=["date_prs", "date_display", "safe_url", "search_blob"], errors="ignore").to_csv(index=False).encode("utf-8-sig"),
        file_name="ai_policy_activity_candidates_flt.csv",
        mime="text/csv",
        use_container_width=True,
    )

if not flt.empty:
    page_size = st.selectbox("Records per page", [12, 24, 48], index=0)
    page_count = max(1, (len(flt) + page_size - 1) // page_size)
    page = st.number_input("Page", min_value=1, max_value=page_count, value=1, step=1)
    start = (int(page) - 1) * page_size
    page_rows = flt.iloc[start:start + page_size]
    st.caption(f"Page {page} of {page_count} · Records {start + 1}–{start + len(page_rows)}")

    for _, row in page_rows.iterrows():
        headline = str(row.get("headline", "Untitled announcement"))
        state = str(row.get("state", "State not specified"))
        category = str(row.get("activity_type", "Not classified"))
        date_text = str(row.get("date_display", "Date unavailable"))
        with st.expander(f"{headline}  ·  {state}  ·  {date_text}"):
            meta1, meta2, meta3 = st.columns(3)
            meta1.markdown(f"**State**  \n{state}")
            meta2.markdown(f"**Activity type**  \n{category}")
            meta3.markdown(f"**Publisher / date**  \n{row.get('source_name', 'Source not specified')} · {date_text}")
            st.write(row.get("summary", "No summary was provided in the feed."))

            stage = str(row.get("policy_stage", "Stage not specified"))
            decision = str(row.get("screening_decision", "Not supplied"))
            status = str(row.get("manual_review_status", "Not supplied"))
            st.markdown(f"**Reported stage:** {stage}  \n**Screening decision:** {decision}  \n**Human review:** {status}")

            reason = str(row.get("relevance_reason", "")).strip()
            ev = str(row.get("ev_excerpt", "")).strip()
            if reason:
                st.markdown(f"**Why it was flagged:** {reason}")
            if ev:
                st.markdown(f"**ev excerpt:** {ev}")

            ai_terms = str(row.get("ai_ev_terms", "")).strip()
            govt_terms = str(row.get("government_ev_terms", "")).strip()
            action_terms = str(row.get("activity_ev_terms", "")).strip()
            if any([ai_terms, govt_terms, action_terms]):
                with st.container(border=True):
                    st.caption("Screening ev")
                    if ai_terms:
                        st.write(f"AI terms: {ai_terms}")
                    if govt_terms:
                        st.write(f"Government terms: {govt_terms}")
                    if action_terms:
                        st.write(f"Activity terms: {action_terms}")

            link = str(row.get("safe_url", ""))
            if link:
                st.link_button("Open original article", link)
            else:
                st.caption("No valid HTTP/HTTPS article link was supplied for this record.")
else:
    st.info("There are no records to display. Change the filters or reset them.")

with st.expander("Screening method and interpretation"):
    st.markdown(
        """
        The notebook searches state-specific AI-policy news feeds and applies an explainable keyword screen to the headline and RSS summary. Its candidate export is intended to prioritize stories for human verification; it does not establish that an announcement was approved, funded or implemented.

        **In-scope activity:** state AI policies or missions; AI task forces and centres of excellence; AI deployment in public services; government-linked AI MoUs and partnerships; AI-specific public funding; AI regulation, ethics and governance; and government-backed AI infrastructure.

        **Out of scope:** private AI product announcements without a state-government role, generic technology events, and digitisation stories without an explicit AI connection. Borderline cases should be checked against the original article and documented before submission.

        Collection coverage is not uniform across states. The record count must not be treated as a ranking of state policy effort.
        """
    )

st.caption("Source attribution is retained in each record. Check the publisher's article for full context before using a record as ev.")