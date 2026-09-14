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

The repo opens with blank outputs. Work through it in this order:

1. Open the badge link. If Colab asks, allow third-party cookies so the file list loads.
2. Install dependencies once at the top: `%pip install -q pandas requests beautifulsoup4 pypdf matplotlib seaborn`, then Runtime > Restart runtime so the new packages load.
3. Clone the repo inside Colab (the badge alone gives you the notebook without `scripts/` and `clean_data/`, which the notebook needs):
```python
!git clone https://github.com/venmor/csc4792-group33-mwense-town-council-dataset.git
%cd csc4792-group33-mwense-town-council-dataset
```
4. First run only: set `RUN_SITE_CRAWL = True`, `RUN_SOURCE_DOWNLOAD = True`, `RUN_PDF_EXTRACTION = True` in the two acquisition cells, then Runtime > Run all. Later runs can leave them `False` to reuse files.
5. Watch for these progress signals as cells execute (numbers in `[ ]` fill in as each cell finishes):
   - Download cell prints one line per PDF (`Downloaded ... (10,061,548 bytes)` or `Skipped ... up-to-date`) plus `Done: N downloaded, M skipped`.
   - Extraction cell prints one line per PDF plus `Done: N extracted, M skipped`, with a `WARNING` on the 2024 scan (expected).
   - Listing cell prints the 4 PDFs and 4 text files with byte sizes.
   - Build and cleaning cells print `Loaded 56 verified project records`, `Dataset now contains 59`, sector list, and the QA missingness table.
   - Analysis cells render HTML tables (category, sector, finance by constituency, IDP types) and two figures.
   - Export cell prints the three `outputs/db-unza26-csc4792-*.csv` paths plus `Separator: pipe (|)`.
6. Confirm success: `outputs/` holds the 3 CSVs (59/47/6 rows) and `figures/` holds 2 PNGs. If any cell shows `[*]` for minutes, Runtime > Interrupt and rerun that cell; council downloads can be slow.
7. Save results before the runtime recycles: open the Files pane, right-click `outputs/` > Download, or mount Drive with `from google.colab import drive; drive.mount('/content/drive')` and copy `outputs/` there. Expect 12 old `content-*` category URLs to report 404 in the manifest; the homepage `200` plus the 4 core PDFs are what the dataset uses.

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
* Members: Musonda Katongo 2020583969, Charles Hangoma 2021414469, Nosiku Mukuka 2022030346, Aaron Simfukwe 2021376079 and Clement Nkhoma 2020044153
