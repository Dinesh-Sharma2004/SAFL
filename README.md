# India AI Policy Activity Tracker

A small end-to-end pipeline and dashboard for collecting and exploring news about AI-related policy activity across Indian states. The dashboard reads the candidate CSV produced by the supplied notebook; it does not scrape news itself or reclassify/deduplicate records in the browser.

## What is included

- `notebook/AI_Related_State_Policy_Activity_Pipeline.ipynb` — the supplied notebook, retained as the collection and screening pipeline.
- `run_pipeline.sh` — Bash runner for Linux/macOS/Git Bash.
- `run.ps1` — native Windows PowerShell runner.
- `scripts/validate_and_copy.py` — verifies the notebook's candidate CSV and copies it into the dashboard data folder.
- `dashboard.py` — Streamlit dashboard, with filters, charts, article links, pagination and CSV downloads.
- `data/ai_policy_activity_candidates.csv` — the candidate CSV supplied with this project, so the dashboard can be tried without an immediate RSS refresh.

## How the pipeline works

1. Create a local Python virtual environment.
2. Install the dashboard and notebook dependencies.
3. Execute the existing notebook with `jupyter nbconvert --execute`.
4. The notebook writes `state_news_output/ai_policy_activity_candidates.csv` by default.
5. Validate required columns and ensure at least one record exists.
6. Copy the CSV to `data/ai_policy_activity_candidates.csv`.
7. Launch the Streamlit dashboard at `http://localhost:8501`.

The notebook remains the source of truth for collection, screening, deduplication and export. All candidate records are still awaiting human verification; charts should be interpreted as a news-monitoring sample, not a definitive ranking of state policy activity.

## Windows — run everything

Open PowerShell in this project folder:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\run.ps1
```

The first run creates `.venv`, installs dependencies, executes the notebook, validates/copies the CSV, then starts the dashboard. Stop the dashboard with `Ctrl+C`.

### Windows — use the supplied CSV without rerunning RSS collection

```powershell
.\run.ps1 -SkipNotebook
```

### Windows — dashboard only (after the environment is installed)

```powershell
.\start_dashboard.ps1
```

## Linux/macOS/Git Bash — run everything

```bash
chmod +x ./run_pipeline.sh
./run_pipeline.sh
```

### Reuse the supplied/previously generated CSV

```bash
./run_pipeline.sh --skip-notebook
```

### Dashboard only

```bash
./start_dashboard.sh
```

## Configuration

The main settings are at the top of `run_pipeline.sh` and `run.ps1`. They can also be overridden with environment variables:

| Variable | Default | Purpose |
|---|---|---|
| `PYTHON_BIN` | `python3` (Bash) / `py` (PowerShell) | Python launcher |
| `VENV_DIR` | `.venv` | Virtual environment location |
| `NOTEBOOK_PATH` | `notebook/AI_Related_State_Policy_Activity_Pipeline.ipynb` | Notebook to execute |
| `STATE_NEWS_OUTPUT_DIR` | `state_news_output/` | Notebook export directory |
| `OUTPUT_CSV_PATH` | `state_news_output/ai_policy_activity_candidates.csv` | Candidate CSV path used after notebook execution |
| `DASHBOARD_CSV_PATH` | `data/ai_policy_activity_candidates.csv` | CSV read by dashboard |
| `PORT` | `8501` | Dashboard port |

The notebook itself writes a fixed filename, `ai_policy_activity_candidates.csv`, under `STATE_NEWS_OUTPUT_DIR`. If `OUTPUT_CSV_PATH` points elsewhere, the runner copies the notebook's generated file there before validation. The dashboard always uses `DASHBOARD_CSV_PATH`.

Example PowerShell override:

```powershell
$env:STATE_NEWS_OUTPUT_DIR = 'D:\AI-Policy\processed'
$env:PORT = '8502'
.\run.ps1
```

Example Bash override:

```bash
STATE_NEWS_OUTPUT_DIR="$PWD/processed" PORT=8502 ./run_pipeline.sh
```

## Dashboard features

- KPIs for flt records, states, activity categories, publishers and pending review.
- Filters for keyword search, state, activity type, policy stage, publisher and publication date.
- State distribution, activity-category mix, publication timeline, reported policy stage and publisher charts.
- Sort newest/oldest and paginate article records.
- ev terms, screening rationale and policy-stage fields shown with each record.
- Original article links are clickable only when they are valid HTTP/HTTPS URLs.
- Download all candidate records or only the flt records as CSV.

The app maps the notebook's actual columns (`headline`, `source_name`, `source_url`, `activity_type`, `policy_stage`, etc.) and accepts common aliases. Missing optional fields are displayed as unavailable rather than fabricated.

## Data and screening rationale

The notebook uses state-specific AI-policy RSS discovery and a transparent keyword screen. Candidate rows are not a fact-checked policy inventory. Review each original story and confirm (a) the state government actor, (b) a concrete AI action, (c) the activity type, (d) its date and (e) whether the action is proposed, announced, approved, funded, signed or operational. The dashboard deliberately surfaces the notebook's `manual_review_status`, `screening_decision`, `relevance_reason` and ev fields to make this review visible.

Coverage and source volume are not uniform across states. A state with fewer hits must not be interpreted as having less AI policy activity.

## Troubleshooting

- **Notebook execution fails:** check the first failing cell in the nbconvert output. The pipeline requires working internet access for RSS requests. The original notebook can also run in Colab.
- **No candidate CSV:** inspect `state_news_output/` and the notebook execution output. The runner will stop rather than create an empty fallback dataset.
- **CSV has no records:** the runner intentionally fails validation and does not overwrite the dashboard CSV.
- **Port in use:** set `PORT=8502` (Bash) or `$env:PORT='8502'` (PowerShell).
- **Python launcher not found:** install Python 3.10+ and set `PYTHON_BIN` to the relevant executable/launcher.

## Git repository and hosting

Initialize a repository and make incremental commits as you work:

```bash
git init
git add README.md requirements.txt dashboard.py run_pipeline.sh run.ps1 scripts notebook
 git commit -m "Add AI policy collection pipeline and dashboard scaffold"
git add data/ai_policy_activity_candidates.csv
git commit -m "Add screened state AI policy candidate dataset"
```

For a static host such as Netlify or Vercel, this Streamlit app cannot be deployed as a static HTML-only site. Deploy it to a Streamlit-compatible Python host, or convert the frontend to a static React app. The CSV can be committed under `data/` or supplied as a hosted static asset, subject to publisher/source terms and your assessment's data-sharing rules.
