<img width="1376" height="768" alt="creator-analytics-pipeline" src="https://github.com/user-attachments/assets/b382c141-18bf-4dc2-b2f6-dd0b30789bd5" />

[creator_analytics_pipeline_readme.md](https://github.com/user-attachments/files/35228289/creator_analytics_pipeline_readme.md)

# Creator Analytics Pipeline

An end-to-end local batch analytics pipeline modeled after modern creator data engineering and BI workflows—built in **WSL (Ubuntu)** using **Python**, **YouTube Data API v3**, **DuckDB**, **Pandas**, **Plotly**, and **Streamlit**, and version-controlled with **Git / GitHub**.

## What Was Built

1. **Environment & Credentials Setup**: Configured an isolated Python virtual environment (`.venv`) inside WSL and wired `.env` to authenticate against the **YouTube Data API v3** with a target `CHANNEL_ID`.
2. **Ingestion Layer (`src/extract.py`)**: Queries the channel's uploads playlist and video endpoints to pull `snippet`, `statistics`, and `contentDetails`, saving immutable timestamped snapshots (`videos_YYYYMMDD_HHMMSS.json`) under `data/raw/`.
3. **Warehousing & SQL Transformation Layer (`src/transform.py`)**: Reads the latest raw JSON snapshot via **Pandas**, loads a staging table (`stg_videos`) into **DuckDB** (`data/creator_warehouse.duckdb`), and runs SQL transformations to build `mart_video_performance` with parsed timestamps, publish day-of-week, title character length, like-to-view rate (`like_rate_pct`), and comment rate (`comment_rate_pct`).
4. **BI Dashboard Layer (`src/dashboard.py`)**: Queries `mart_video_performance` in `read_only=True` mode using **DuckDB** and renders KPI cards, title/date filters, **Plotly** visualizations (*Views Over Time* and *Title Length vs. Views*), and a sortable data table in **Streamlit** (`http://localhost:8501`).

## Architecture & Data Flow

```text
YouTube Data API v3
        │
        ▼
[src/extract.py] ──► data/raw/videos_*.json        (Raw Ingestion Snapshot)
        │
        ▼
[src/transform.py] ──► data/creator_warehouse.duckdb (stg_videos → mart_video_performance)
        │
        ▼
[src/dashboard.py] ──► Streamlit + Plotly UI       (http://localhost:8501)
```

### How the Pipeline Works Step by Step

1. **Ingestion (`src/extract.py`)**:
   * Reads `YOUTUBE_API_KEY` and `CHANNEL_ID` from `.env`.
   * Fetches the channel's `uploads` playlist ID from the `channels` endpoint.
   * Pulls recent video IDs via `playlistItems` and retrieves video metadata/statistics via `videos`.
   * Writes raw JSON snapshots (`data/raw/videos_YYYYMMDD_HHMMSS.json`) so source payloads remain immutable.
2. **Warehouse & SQL Transform (`src/transform.py`)**:
   * Locates the newest JSON file in `data/raw/`.
   * Flattens nested `snippet` and `statistics` fields into a tabular `pandas.DataFrame`.
   * Materializes `stg_videos` inside `data/creator_warehouse.duckdb` and executes DuckDB SQL to create `mart_video_performance` with typed timestamps and calculated engagement metrics (`like_rate_pct`, `comment_rate_pct`).
3. **BI & Visualization (`src/dashboard.py`)**:
   * Connects to `data/creator_warehouse.duckdb` with `read_only=True` to avoid database write locks.
   * Provides sidebar filters for title keyword search and publish date range.
   * Displays top-line KPIs, interactive Plotly charts, and a performance breakdown table on `http://localhost:8501`.

## Tech Stack, Languages & Tools

* **Languages**: Python (`3.x`), SQL (DuckDB SQL dialect), Bash
* **Data Extraction & Config**: `google-api-python-client` (YouTube Data API v3), `python-dotenv` (`.env`)
* **Data Processing & Warehousing**: `pandas`, `duckdb` (embedded analytical OLAP database)
* **Visualization & BI**: `streamlit`, `plotly` (`plotly.express`)
* **Environment & Version Control**: Windows Subsystem for Linux (WSL 2 / Ubuntu), Python `venv`, `git`, GitHub

## Project Structure

```text
creator-analytics-pipeline/
├── data/
│   ├── raw/                        # Timestamped raw JSON snapshots (gitignored)
│   └── creator_warehouse.duckdb    # Local DuckDB warehouse (gitignored)
├── src/
│   ├── extract.py                  # Step 1: API ingestion to raw JSON
│   ├── transform.py                # Step 2: Staging & SQL mart modeling in DuckDB
│   └── dashboard.py                # Step 3: Interactive Streamlit + Plotly dashboard
├── .env                            # Local API key & channel ID (gitignored)
├── .env.example                    # Template for required environment variables
├── .gitignore                      # Excludes secrets, venv, and local data artifacts
├── requirements.txt                # Python dependencies
└── README.md
```

## How to Run Locally (WSL)

1. **Activate virtual environment & install dependencies**
   ```bash
   cd ~/creator-analytics-pipeline
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and set YOUTUBE_API_KEY and CHANNEL_ID
   ```

3. **Run the pipeline in sequence**
   ```bash
   python src/extract.py
   python src/transform.py
   streamlit run src/dashboard.py
   ```
   Open **http://localhost:8501** in your Windows browser to explore the dashboard.

## Notes on Local Execution, Security & Automation

* **Dormant vs. Active State**: `extract.py` and `transform.py` run on demand when executed; `dashboard.py` serves on `localhost:8501` while the Streamlit process is running in WSL.
* **Automation**: Recurring refreshes can be scheduled locally via `cron` in WSL or automated remotely with GitHub Actions.
* **Ignored Artifacts**: `.env`, `data/raw/*.json`, and `data/*.duckdb` are excluded via `.gitignore` so API keys and local data snapshots are never pushed to GitHub.
