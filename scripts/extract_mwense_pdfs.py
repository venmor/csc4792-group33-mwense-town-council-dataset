"""Extract searchable text from downloaded Mwense Town Council PDFs.

Skips PDFs whose extracted .txt is already newer than the source PDF so that
re-running the notebook top-to-bottom is fast. Use --force to re-extract all.
"""

import argparse
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "raw_sources"
EXTRACTED_DIR = RAW_DIR / "extracted_text"


def extract_pdf(pdf_path: Path, force: bool = False) -> tuple[Path, bool]:
    output_path = EXTRACTED_DIR / f"{pdf_path.stem}.txt"
    if output_path.exists() and not force:
        try:
            if output_path.stat().st_mtime >= pdf_path.stat().st_mtime and output_path.stat().st_size > 0:
                print(f"Skipped {pdf_path.name} (extracted text up-to-date)")
                return output_path, True
        except FileNotFoundError:
            pass
    try:
        from pypdf import PdfReader
    except ImportError as error:
        raise SystemExit(
            "Missing dependency: install pypdf with 'python -m pip install pypdf'."
        ) from error

    reader = PdfReader(str(pdf_path))
    pages = []
    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        pages.append(f"\n--- Page {page_number} ---\n{text}")

    output_path.write_text("".join(pages), encoding="utf-8")
    if output_path.stat().st_size < 100:
        print(f"WARNING: {pdf_path.name} yielded {output_path.stat().st_size} bytes - likely scanned image, see notebook Section 3.2")
    return output_path, False


def main(force: bool = False) -> None:
    EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)
    pdf_files = sorted(RAW_DIR.glob("*.pdf"))
    if not pdf_files:
        raise SystemExit("No PDF files found in raw_sources/. Run download_mwense_sources.py first.")

    skipped = 0
    extracted = 0
    for pdf_path in pdf_files:
        output_path, was_skipped = extract_pdf(pdf_path, force=force)
        if was_skipped:
            skipped += 1
        else:
            extracted += 1
            print(f"Extracted {pdf_path.name} -> {output_path.relative_to(PROJECT_ROOT)}")
    print(f"Done: {extracted} extracted, {skipped} skipped (use --force to re-extract all).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="Re-extract all PDFs even if .txt is up-to-date.")
    args = parser.parse_args()
    main(force=args.force)