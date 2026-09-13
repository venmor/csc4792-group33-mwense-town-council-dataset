"""Catalogue and download public Mwense Town Council source material.

The crawler is deliberately bounded: it starts from the council homepage and
the assignment-relevant category URLs, follows same-domain links only, and
records both successful and failed requests in a manifest.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
import ssl
from collections import deque
from pathlib import Path
from urllib.parse import urldefrag, urljoin, urlparse
from urllib.request import Request, urlopen

try:
    from bs4 import BeautifulSoup
except ImportError as error:
    raise SystemExit("Install beautifulsoup4 before running this script.") from error


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "raw_sources" / "site_catalogue"
MANIFEST_PATH = PROJECT_ROOT / "outputs" / "db-unza26-csc4792-mwense-site-manifest.csv"
BASE_URL = "https://www.mwensecouncil.gov.zm/"

CATEGORY_URLS = {
    "home": BASE_URL,
    "minutes": f"{BASE_URL}content-78ef8f46aa6b5090d303",
    "financial_statements": f"{BASE_URL}content-6facca86aa6b5090d303",
    "budgets": f"{BASE_URL}content-91901f06aa6b5090d303",
    "projects": f"{BASE_URL}content-349aa156aa6b5090d303",
    "engagement_plans": f"{BASE_URL}content-783a0ac6aa6b5090d303",
    "newsletter": f"{BASE_URL}content-cf4b1ff6aa6b5090d303",
    "idps": f"{BASE_URL}content-2193e326aa6b5090d303",
    "press_statements": f"{BASE_URL}content-d0330da6aa6b5090d303",
    "service_delivery_charter": f"{BASE_URL}content-3c3b1da6aa6b5090d303",
    "acts_and_policies": f"{BASE_URL}content-98cb5dd6aa6b5090d303",
    "adverts": f"{BASE_URL}content-b96c5216aa6b5090d303",
    "cdf_catalogue": f"{BASE_URL}content-69538df6aa6b5090d303",
}

CATEGORY_KEYWORDS = {
    "minutes": ("minute", "meeting", "council resolution"),
    "financial_statements": ("financial", "statement", "audit"),
    "budgets": ("budget", "budget estimates"),
    "projects": ("project", "approved", "capital"),
    "engagement_plans": ("engagement", "participation"),
    "newsletter": ("newsletter", "bulletin"),
    "idps": ("idp", "integrated development"),
    "press_statements": ("press", "statement"),
    "service_delivery_charter": ("service delivery", "charter"),
    "acts_and_policies": ("act", "policy", "guideline"),
    "adverts": ("advert", "tender", "notice"),
    "cdf_catalogue": ("cdf", "catalogue"),
}


def safe_name(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-")
    return value[:100] or "unnamed"


def local_name(url: str, content_type: str) -> str:
    parsed = urlparse(url)
    stem = Path(parsed.path).stem or "home"
    suffix = Path(parsed.path).suffix
    if not suffix and "pdf" in content_type.lower():
        suffix = ".pdf"
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:10]
    return f"{safe_name(stem)}-{digest}{suffix}"


def fetch(url: str, insecure: bool) -> tuple[int, str, bytes, str]:
    request = Request(url, headers={"User-Agent": "CSC-4792-Group-33-research/1.0"})
    context = ssl._create_unverified_context() if insecure else None
    with urlopen(request, timeout=30, context=context) as response:
        return response.status, response.headers.get("Content-Type", ""), response.read(), response.geturl()


def extract_links(html: bytes, page_url: str) -> list[tuple[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for anchor in soup.find_all("a", href=True):
        href = urljoin(page_url, anchor["href"])
        href = urldefrag(href)[0]
        if urlparse(href).scheme in {"http", "https"}:
            label = anchor.get_text(" ", strip=True)
            links.append((href, label))
    return list(dict.fromkeys(links))


def infer_category(label: str, url: str, fallback: str) -> str:
    searchable = f"{label} {url}".lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in searchable for keyword in keywords):
            return category
    return fallback


def crawl(max_pages: int, insecure: bool) -> list[dict[str, str]]:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    (PROJECT_ROOT / "outputs").mkdir(parents=True, exist_ok=True)
    domain = urlparse(BASE_URL).netloc
    queue = deque((url, category, BASE_URL) for category, url in CATEGORY_URLS.items())
    seen = set()
    manifest = []

    while queue and len(seen) < max_pages:
        url, category, discovered_from = queue.popleft()
        if url in seen:
            continue
        seen.add(url)
        row = {
            "category": category,
            "discovery_url": discovered_from,
            "url": url,
            "final_url": "",
            "status": "",
            "content_type": "",
            "title": "",
            "local_path": "",
            "error": "",
        }
        try:
            status, content_type, body, final_url = fetch(url, insecure)
            row["status"] = str(status)
            row["content_type"] = content_type
            row["final_url"] = final_url
            if final_url != url:
                row["url"] = final_url
            filename = local_name(final_url, content_type)
            is_pdf = "pdf" in content_type.lower() or final_url.lower().endswith(".pdf")
            if is_pdf:
                destination = RAW_DIR / filename
                destination.write_bytes(body)
                row["local_path"] = str(destination.relative_to(PROJECT_ROOT))
            else:
                soup = BeautifulSoup(body, "html.parser")
                row["title"] = soup.title.get_text(" ", strip=True) if soup.title else ""
                destination = RAW_DIR / f"{Path(filename).stem}.txt"
                destination.write_text(soup.get_text("\n", strip=True), encoding="utf-8")
                row["local_path"] = str(destination.relative_to(PROJECT_ROOT))
                for link, label in extract_links(body, final_url):
                    if urlparse(link).netloc != domain or link in seen:
                        continue
                    link_category = infer_category(label, link, category)
                    queue.append((link, link_category, final_url))
        except Exception as error:  # Record inaccessible sources rather than stopping the audit.
            row["status"] = "error"
            row["error"] = f"{type(error).__name__}: {error}"
        manifest.append(row)

    with MANIFEST_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=manifest[0].keys() if manifest else ["url"], delimiter="|")
        writer.writeheader()
        writer.writerows(manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-pages", type=int, default=100)
    parser.add_argument("--insecure", action="store_true", help="Allow invalid TLS certificates when necessary.")
    args = parser.parse_args()
    manifest = crawl(args.max_pages, args.insecure)
    print(f"Catalogued {len(manifest)} URLs.")
    print(f"Manifest: {MANIFEST_PATH.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()