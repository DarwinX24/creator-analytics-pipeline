import glob
import json
import os
import duckdb
import pandas as pd


def run_transformations():
    # 1. Locate the latest raw JSON file
    files = sorted(glob.glob("data/raw/videos_*.json"))
    if not files:
        raise FileNotFoundError(
            "No raw data found in data/raw/. Run src/extract.py first."
        )

    latest_file = files[-1]
    with open(latest_file, "r", encoding="utf-8") as f:
        raw_items = json.load(f)

    if not raw_items:
        raise ValueError(f"Raw file {latest_file} contains no video records.")

    # 2. Flatten nested JSON into structured records
    records = []
    for item in raw_items:
        snippet = item.get("snippet", {})
        stats = item.get("statistics", {})
        records.append({
            "video_id": item.get("id"),
            "title": snippet.get("title"),
            "published_at": snippet.get("publishedAt"),
            "view_count": int(stats.get("viewCount", 0) or 0),
            "like_count": int(stats.get("likeCount", 0) or 0),
            "comment_count": int(stats.get("commentCount", 0) or 0),
        })

    df = pd.DataFrame(records)

    # 3. Load staging & build analytical mart in DuckDB
    os.makedirs("data", exist_ok=True)
    db_path = "data/creator_warehouse.duckdb"
    con = duckdb.connect(db_path)

    con.execute("CREATE OR REPLACE TABLE stg_videos AS SELECT * FROM df")

    con.execute("""
        CREATE OR REPLACE TABLE mart_video_performance AS
        SELECT
            video_id,
            title,
            CAST(published_at AS TIMESTAMP) AS published_at,
            EXTRACT(DOW FROM CAST(published_at AS TIMESTAMP)) AS publish_day_of_week,
            LENGTH(title) AS title_length,
            view_count,
            like_count,
            comment_count,
            ROUND((like_count::DOUBLE / NULLIF(view_count, 0)) * 100, 2) AS like_rate_pct,
            ROUND((comment_count::DOUBLE / NULLIF(view_count, 0)) * 100, 4) AS comment_rate_pct
        FROM stg_videos
        ORDER BY published_at DESC
    """)

    row_count = con.execute(
        "SELECT COUNT(*) FROM mart_video_performance"
    ).fetchone()[0]
    con.close()

    print(
        f"Transformed {latest_file} -> {row_count} rows in {db_path} "
        "(table: mart_video_performance)"
    )


if __name__ == "__main__":
    run_transformations()
