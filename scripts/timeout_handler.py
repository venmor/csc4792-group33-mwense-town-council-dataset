"""
Timeout handler for web scraping with slow internet support.

This module provides configurable connection and read timeouts,
automatic retry with exponential backoff, and detailed logging.

Usage:
    from timeout_handler import TimeoutConfig, fetch_with_retry
    
    config = TimeoutConfig(
        connection_timeout=10,
        read_timeout=30,
        total_timeout=60,
        retries=3
    )
    
    response = fetch_with_retry(url, config)
"""

import time
import logging
from typing import Optional, Tuple
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class TimeoutConfig:
    """Configuration for timeout handling with slow internet support."""
    
    def __init__(
        self,
        connection_timeout: int = 15,
        read_timeout: int = 45,
        total_timeout: int = 120,
        retries: int = 3,
        backoff_factor: float = 0.5,
        status_forcelist: Optional[list] = None,
    ):
        """
        Initialize timeout configuration.
        
        Args:
            connection_timeout: Seconds to wait for connection (default: 15)
            read_timeout: Seconds to wait for response (default: 45)
            total_timeout: Total seconds allowed for request (default: 120)
            retries: Number of retry attempts (default: 3)
            backoff_factor: Exponential backoff factor (default: 0.5)
            status_forcelist: HTTP status codes to retry on
        """
        self.connection_timeout = connection_timeout
        self.read_timeout = read_timeout
        self.total_timeout = total_timeout
        self.retries = retries
        self.backoff_factor = backoff_factor
        self.status_forcelist = status_forcelist or [429, 500, 502, 503, 504]
        
    @property
    def timeout_tuple(self) -> Tuple[int, int]:
        """Return (connection_timeout, read_timeout) tuple for requests."""
        return (self.connection_timeout, self.read_timeout)
    
    def __repr__(self) -> str:
        return (f"TimeoutConfig(conn={self.connection_timeout}s, "
                f"read={self.read_timeout}s, total={self.total_timeout}s, "
                f"retries={self.retries})")


def create_session_with_retries(config: TimeoutConfig) -> requests.Session:
    """
    Create a requests session with automatic retry strategy.
    
    Args:
        config: TimeoutConfig instance
        
    Returns:
        Configured requests.Session
    """
    session = requests.Session()
    
    retry_strategy = Retry(
        total=config.retries,
        backoff_factor=config.backoff_factor,
        status_forcelist=config.status_forcelist,
        allowed_methods=["GET", "HEAD", "POST"]
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session


def fetch_with_retry(
    url: str,
    config: TimeoutConfig,
    headers: Optional[dict] = None,
    method: str = "GET",
    **kwargs
) -> Optional[requests.Response]:
    """
    Fetch a URL with automatic retry and timeout handling.
    
    Designed for slow or unreliable internet connections.
    
    Args:
        url: URL to fetch
        config: TimeoutConfig instance
        headers: Optional HTTP headers dict
        method: HTTP method (default: GET)
        **kwargs: Additional args for requests (e.g., params, data, json)
        
    Returns:
        requests.Response if successful, None if all retries failed
        
    Example:
        config = TimeoutConfig(connection_timeout=10, read_timeout=30)
        response = fetch_with_retry("https://example.com", config)
        if response and response.status_code == 200:
            print(response.text)
    """
    session = create_session_with_retries(config)
    
    if headers is None:
        headers = {"User-Agent": "CSC4792-Research-Bot/1.0"}
    
    attempt = 0
    start_time = time.time()
    
    while attempt < config.retries:
        try:
            attempt += 1
            elapsed = time.time() - start_time
            
            if elapsed > config.total_timeout:
                logger.warning(
                    f"Total timeout exceeded ({elapsed:.1f}s > {config.total_timeout}s) "
                    f"for {url}"
                )
                return None
            
            logger.info(
                f"Attempt {attempt}/{config.retries} for {url} "
                f"(elapsed: {elapsed:.1f}s)"
            )
            
            response = session.request(
                method,
                url,
                headers=headers,
                timeout=config.timeout_tuple,
                **kwargs
            )
            
            response.raise_for_status()
            logger.info(f"✓ Successfully fetched {url} (status: {response.status_code})")
            session.close()
            return response
            
        except requests.exceptions.Timeout as e:
            logger.warning(
                f"Timeout on attempt {attempt}/{config.retries} for {url}: {str(e)}"
            )
        except requests.exceptions.ConnectionError as e:
            logger.warning(
                f"Connection error on attempt {attempt}/{config.retries} for {url}: {str(e)}"
            )
        except requests.exceptions.HTTPError as e:
            if e.response.status_code >= 500:
                logger.warning(
                    f"Server error {e.response.status_code} on attempt {attempt}/{config.retries}"
                )
            else:
                logger.error(f"HTTP error {e.response.status_code}: {url}")
                session.close()
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {url}: {str(e)}")
            session.close()
            return None
        
        if attempt < config.retries:
            wait_time = config.backoff_factor * (2 ** (attempt - 1))
            logger.info(f"Waiting {wait_time:.1f}s before next retry...")
            time.sleep(wait_time)
    
    logger.error(f"✗ Failed to fetch {url} after {config.retries} attempts")
    session.close()
    return None


def fetch_pdf_with_resume(
    url: str,
    output_path: str,
    config: TimeoutConfig,
    headers: Optional[dict] = None,
    chunk_size: int = 8192
) -> bool:
    """
    Download a PDF with resume capability for slow connections.
    
    Args:
        url: PDF URL
        output_path: Local file path to save
        config: TimeoutConfig instance
        headers: Optional HTTP headers
        chunk_size: Bytes per chunk (default: 8KB)
        
    Returns:
        True if successful, False otherwise
    """
    import os
    
    if headers is None:
        headers = {"User-Agent": "CSC4792-Research-Bot/1.0"}
    
    session = create_session_with_retries(config)
    
    # Check if partial file exists
    resume_header = {}
    if os.path.exists(output_path):
        resume_header["Range"] = f"bytes={os.path.getsize(output_path)}-"
        logger.info(f"Resuming download from {os.path.getsize(output_path)} bytes")
    
    headers.update(resume_header)
    
    try:
        response = session.get(
            url,
            headers=headers,
            timeout=config.timeout_tuple,
            stream=True
        )
        response.raise_for_status()
        
        total_size = int(response.headers.get("content-length", 0))
        downloaded = os.path.getsize(output_path) if os.path.exists(output_path) else 0
        
        with open(output_path, "ab") as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size:
                        pct = (downloaded / total_size) * 100
                        logger.debug(f"Downloaded: {pct:.1f}% ({downloaded}/{total_size})")
        
        logger.info(f"✓ Successfully downloaded PDF to {output_path}")
        session.close()
        return True
        
    except Exception as e:
        logger.error(f"✗ Failed to download PDF: {str(e)}")
        session.close()
        return False
