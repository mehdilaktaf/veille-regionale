# Agent Guidance: veille-regionale

## Developer Commands
- Run GUI App: `python app.py`
- Run Analysis Script: `python analyse.py`
- Run PDF Fetcher (Standalone): `python fetch_and_merge_pdf.py`

## Dependencies & Setup
- Install requirements: `pip install -r requirements.txt`
- **Missing Dependencies**: `analyse.py` requires `pdfplumber` and `openpyxl`, which are not listed in `requirements.txt`.
- **Chrome Driver**: `app.py` uses `webdriver-manager` (automatic). `fetch_and_merge_pdf.py` expects a local driver at `chromedriver-win64/chromedriver`.

## Architecture & Flow
- `app.py`: Main entry point. GUI for selecting department/year/month to automate scraping and merging of PDFs.
- `fetch_and_merge_pdf.py`: Logic for scraping and merging (used as a reference or standalone).
- `analyse.py`: Extracts **bold text** from merged PDFs and searches for specific regional administrative keywords, exporting to Excel.

## Critical Quirks
- **Scraping**: Uses Selenium (headless). Handles cookie pop-ups specifically via `#tarteaucitronAllDenied2`.
- **Analysis Path**: `analyse.py:5` has a hardcoded Windows path to a PDF. This must be updated to a valid local path before running.
- **Timing**: Scripts include `time.sleep(10)` to handle slow-loading government portals.
