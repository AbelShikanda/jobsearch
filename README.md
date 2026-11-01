# jobsearch

Python job-scraping pipeline that aggregates Kenyan job listings from multiple sources,
deduplicates them, scores/qualifies them against a resume profile, writes BI
recommendations per organization, and persists results to SQLite.

## Stack
- Python 3.14
- Playwright (headless Chromium scraping)
- pydantic (data models)
- python-dotenv (config)
- beautifulsoup4 / lxml (parsing)
- httpx / requests (HTTP clients)
- pdfplumber / pdfminer.six / python-docx (resume parsing)
- SQLite (storage)

## Quick start
```bash
python -m venv venv
.\venv\Scripts\Activate.ps1   # Windows
pip install -r requirements.txt

cp .env.example .env
# edit .env and add your SERPER_API_KEY / BRIGHTDATA_API_KEY
python main.py
```

## Pipeline stages
1. **Fetch** — BrightData Maps + Serper API collectors; Kenyan job boards via Playwright
2. **Dedupe** — fingerprint-based dedup against previously seen jobs
3. **Filter** — hard Kenya / on-site filter
4. **Score & qualify** — score against resume profile; apply threshold
5. **BI memos** — per-organization recommendations for real orgs (BrightData source)
6. **Persist & report** — save to SQLite; send report

## Config
Copy `.env.example` to `.env` and fill in your API keys. Never commit `.env`.
