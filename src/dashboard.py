import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Creator Analytics Dashboard", layout="wide")
st.title("📊 Creator Content Performance Dashboard")

db_path = "data/creator_warehouse.duckdb"

try:
    con = duckdb.connect(db_path, read_only=True)
    df = con.execute("SELECT * FROM mart_video_performance").df()
    con.close()
except Exception as exc:
    st.error(
        f"Could not load 'mart_video_performance' from '{db_path}'. "
        "Run `python src/extract.py` and `python src/transform.py` first."
    )
    st.exception(exc)
    st.stop()

if df.empty:
    st.warning("No video records found in 'mart_video_performance'.")
    st.stop()

df["published_at"] = pd.to_datetime(df["published_at"])

# Sidebar filters
st.sidebar.header("Filters")
search_query = st.sidebar.text_input("Search video title", "").strip()

min_date = df["published_at"].min().date()
max_date = df["published_at"].max().date()
date_range = st.sidebar.date_input(
    "Published date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

filtered_df = df.copy()
if search_query:
    filtered_df = filtered_df[
        filtered_df["title"].str.contains(search_query, case=False, na=False)
    ]

if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
    filtered_df = filtered_df[
        (filtered_df["published_at"].dt.date >= start_date)
        & (filtered_df["published_at"].dt.date <= end_date)
    ]

if filtered_df.empty:
    st.info("No videos match the current filter criteria.")
    st.stop()

# KPI Row
col1, col2, col3, col4 = st.columns(4)
col1.metric("Videos Analyzed", f"{len(filtered_df):,}")
col2.metric("Avg Views per Video", f"{filtered_df['view_count'].mean():,.0f}")
col3.metric("Avg Like-to-View Ratio", f"{filtered_df['like_rate_pct'].mean():.2f}%")
col4.metric(
    "Avg Comment Rate", f"{filtered_df['comment_rate_pct'].mean():.4f}%"
)

st.divider()

# Charts
left, right = st.columns(2)

with left:
    st.subheader("Views Over Time")
    fig_views = px.line(
        filtered_df.sort_values("published_at"),
        x="published_at",
        y="view_count",
        hover_data=["title", "like_rate_pct"],
        markers=True,
        labels={"published_at": "Published Date", "view_count": "Views"},
    )
    st.plotly_chart(fig_views, use_container_width=True)

with right:
    st.subheader("Title Length vs. Views")
    fig_title = px.scatter(
        filtered_df,
        x="title_length",
        y="view_count",
        size="like_rate_pct",
        hover_data=["title"],
        labels={
            "title_length": "Title Length (Characters)",
            "view_count": "Views",
            "like_rate_pct": "Like Rate (%)",
        },
    )
    st.plotly_chart(fig_title, use_container_width=True)

st.subheader("Video Performance Breakdown")
st.dataframe(
    filtered_df[[
        "title",
        "published_at",
        "view_count",
        "like_count",
        "comment_count",
        "like_rate_pct",
        "comment_rate_pct",
    ]],
    use_container_width=True,
)
