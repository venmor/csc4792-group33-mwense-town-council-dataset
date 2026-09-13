# CSC 4792 Group 33 - Mwense Town Council Dataset

**Course:** CSC 4792 Data Mining and Warehousing | **Group:** 33
**Council:** Mwense Town Council — https://www.mwensecouncil.gov.zm/
**Deadline:** 14 September 2026

Public council PDFs and web pages consolidated into a traceable table. Running the notebook top to bottom reproduces pipe-separated Kaggle files in `outputs/`.

## Repository layout

```
mwense-town-council-data-analysis.ipynb  Main workflow: fetch, build, clean, analyse, export
scripts/crawl_mwense_sources.py          Site manifest (needs --insecure here)
scripts/download_mwense_sources.py       4 core PDFs into raw_sources/ (skips up-to-date; --force refreshes)
scripts/extract_mwense_pdfs.py           PDF text into raw_sources/extracted_text/ (skips newer txt; --force re-extracts)
scripts/clean_project_data.py            Reusable project cleaning module
scripts/timeout_handler.py               Retry/timeout helpers
clean_data/raw_*.csv                     Parsed IDP/project sources committed (no generator script; notebook IDP cell loads one)
requirements.txt                         Python dependencies
outputs/  figures/  raw_sources/         Generated on run; ignored by git
```

## Run locally (conda)

```bash
conda create -n csc4792 python=3.14 -y && conda activate csc4792
pip install -r requirements.txt  # includes pypdf
python -m jupyter nbconvert --to notebook --execute mwense-town-council-data-analysis.ipynb --output /tmp/test.ipynb --allow-errors
```

Or open `jupyter notebook` / `jupyter lab` and Run All. `RUN_SITE_CRAWL`, `RUN_SOURCE_DOWNLOAD`, `RUN_PDF_EXTRACTION` default to `False` to reuse local files; set `True` to refetch. Expect ~59 records, 2 figure PNGs, 3 CSVs.

## Run in Google Colab

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/venmor/csc4792-group33-mwense-town-council-dataset/blob/main/mwense-town-council-data-analysis.ipynb)

1. Open the badge link, Runtime > Run all.
2. If dependencies are missing, run first: `%pip install -q pandas requests beautifulsoup4 pypdf matplotlib seaborn`.
3. The notebook downloads ~29MB of PDFs, extracts text, builds the table, and writes `outputs/`. Colab runtimes are ephemeral — download CSVs from the Files pane before disconnecting, or persist via `from google.colab import drive; drive.mount('/content/drive')` and copy `outputs/` to Drive.

## Dataset outputs

All files use `|` separator and `db-unza26-csc4792-[description].csv` naming.

| File | Rows | Columns | Purpose |
|---|---|---|---|
| `outputs/db-unza26-csc4792-mwense-town-council-records.csv` | 59 | 25 | Primary Kaggle table: 47 CDF + 9 capital + 3 IDP/admin |
| `outputs/db-unza26-csc4792-mwense-town-council-cdf-projects.csv` | 47 | 25 | CDF-only subset, same schema |
| `outputs/db-unza26-csc4792-mwense-town-council-sources.csv` | 6 | 8 | Source inventory SRC001–SRC006 |

Full column definitions are in notebook Section 8. Missing means absent from the source, never zero-filled.

## Sources

SRC001 council website, SRC002 approved-projects page, SRC003 IDP 2024–2034, SRC004 2024 CDF approvals, SRC005 2025 capital/CDF approvals, SRC006 CDF Guidelines 2022. Each row links via `source_id`/`source_url` with wording in `raw_text` and notes in `extraction_notes`.

## Known limitations

2024 approval PDF is a scanned image (text extraction yields headers only; values manually transcribed and flagged). Ward missing on 38/59 rows; community, institution, beneficiary, date, disbursed, and spent fields fully absent; funding source absent on 50 rows; all statuses `Approved`; 12 legacy `content-*` section URLs return 404; 2025 lists publish no monetary amounts; LGEF figures absent from inventoried sources.

## Links and members

* Kaggle dataset: _to be added_
* Data in Brief paper: _to be added_
* Members: _to be added_
