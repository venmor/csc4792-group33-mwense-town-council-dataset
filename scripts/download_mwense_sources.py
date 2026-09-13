"""Download the official Mwense Town Council source documents.

Skips files that are already present and up-to-date so that re-running the
notebook top-to-bottom does not waste time re-downloading the same PDFs.
Use --force to re-download everything regardless of local state.
"""

from pathlib import Path
import argparse
from typing import Optional
import requests
import urllib3

# Disable SSL warnings for this research dataset
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "raw_sources"

SOURCES = {
    "mwense-idp-2024-2034.pdf":
        "https://www.mwensecouncil.gov.zm/wp-content/uploads/2024/09/IDP-MWENSE.pdf",
    "mwense-2024-approved-cdf-projects.pdf":
        "https://www.mwensecouncil.gov.zm/wp-content/uploads/2025/06/LIST-OF-2024-APPROVED-CDF-PROJECTS.pdf",
    "mwense-2025-approved-projects.pdf":
        "https://www.mwensecouncil.gov.zm/wp-content/uploads/2025/06/LIST-OF-2025-APPROVED-PROJECTS.pdf",
    "cdf-guidelines-2022.pdf":
        "https://www.mwensecouncil.gov.zm/wp-content/uploads/2023/07/2022-CDF-GUIDELINES.pdf",
}


def get_remote_size(url: str, timeout: int = 20) -> Optional[int]:
    """Return remote Content-Length via HEAD, or None if unavailable."""
    headers = {"User-Agent": "CSC-4792-Group-33-research/1.0"}
    try:
        response = requests.head(
            url, headers=headers, timeout=timeout, verify=False,
            allow_redirects=True,
        )
        if response.status_code >= 400:
            return None
        length = response.headers.get("Content-Length")
        return int(length) if length is not None else None
    except Exception:
        return None


def download_file(filename: str, url: str, force: bool = False) -> tuple[Path, bool]:
    """Download one file, skipping if the local copy is already up-to-date.

    Returns (destination, skipped). Compares local size against remote
    Content-Length when available; otherwise skips any non-empty local file
    unless force=True.
    """
    destination = RAW_DIR / filename
    if destination.exists() and destination.stat().st_size > 0 and not force:
        local_size = destination.stat().st_size
        remote_size = get_remote_size(url)
        if remote_size is not None:
            if local_size == remote_size:
                print(f"Skipped {filename} (already present, {local_size:,} bytes, up-to-date)")
                return destination, True
            # Size mismatch -> stale/partial copy, fall through to re-download.
            print(f"Outdated {filename} (local {local_size:,} vs remote {remote_size:,} bytes), re-downloading...")
        else:
            # Remote size unknown (HEAD blocked) -> avoid wasting time/bandwidth.
            print(f"Skipped {filename} (already present, {local_size:,} bytes, remote size unknown)")
            return destination, True

    headers = {"User-Agent": "CSC-4792-Group-33-research/1.0"}
    response = requests.get(url, headers=headers, timeout=30, verify=False)
    response.raise_for_status()
    destination.write_bytes(response.content)
    return destination, False


def main(force: bool = False) -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    skipped = 0
    downloaded = 0
    for filename, url in SOURCES.items():
        destination, was_skipped = download_file(filename, url, force=force)
        if was_skipped:
            skipped += 1
        else:
            downloaded += 1
            print(f"Downloaded {filename} ({destination.stat().st_size:,} bytes)")
    print(f"Done: {downloaded} downloaded, {skipped} skipped (use --force to re-download all).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force", action="store_true",
        help="Re-download all files even if a local copy already exists.",
    )
    args = parser.parse_args()
    main(force=args.force)