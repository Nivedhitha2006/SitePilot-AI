import ipaddress
import socket
import time
import warnings
from collections import deque
from urllib.parse import urldefrag, urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from requests.exceptions import RequestException, SSLError
from urllib3.exceptions import InsecureRequestWarning

from app.config import settings


warnings.filterwarnings("ignore", category=InsecureRequestWarning)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/139.0.0.0 Safari/537.36 SitePilotAI/2.2"
)


def _resolved_ips(host: str):
    try:
        infos = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise ValueError(f"Hostname could not be resolved: {host}") from exc

    ips = []
    for info in infos:
        try:
            ips.append(ipaddress.ip_address(info[4][0]))
        except ValueError:
            continue
    return list(dict.fromkeys(ips))


def safe_url(url: str):
    p = urlparse(str(url).strip())
    if p.scheme not in ("http", "https") or not p.hostname:
        raise ValueError("Only valid http/https URLs are allowed")

    for ip in _resolved_ips(p.hostname.lower()):
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified
        ):
            raise ValueError("SSRF protection blocked a private/reserved host")

    return url


def _clean_link(base: str, href: str):
    try:
        x = urljoin(base, href or "")
        x, _ = urldefrag(x)
        p = urlparse(x)
        if p.scheme not in ("http", "https") or not p.hostname:
            return None
        return x.rstrip("/") or x
    except Exception:
        return None


def _request(session: requests.Session, url: str, **kwargs):
    """Try normal TLS verification, then a narrowly scoped public-site fallback."""
    try:
        return session.get(url, verify=True, **kwargs), False
    except SSLError:
        # The URL has already passed SSRF validation. Some public sites still
        # expose an incomplete CA chain; allowing this fallback makes the audit
        # usable while recording the TLS warning in the page result.
        return session.get(url, verify=False, **kwargs), True


def _empty_row(url: str, error: str):
    return {
        "url": url,
        "status_code": 0,
        "title": "",
        "meta_description": "",
        "h1": 0,
        "h2": 0,
        "h3": 0,
        "images": 0,
        "missing_alt": 0,
        "internal_links": 0,
        "external_links": 0,
        "broken_links": 0,
        "canonical": "",
        "https": url.startswith("https://"),
        "word_count": 0,
        "response_ms": 0,
        "error": error,
        "text": "",
        "content_type": "",
        "bytes": 0,
        "redirected": False,
    }


def crawl(start_url: str, max_pages=None):
    start = safe_url(start_url)
    root = urlparse(start).netloc.lower()
    limit = max(1, int(max_pages or settings.max_crawl_pages))

    queue = deque([start])
    seen = set()
    rows = []

    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-IN,en;q=0.8",
            "Connection": "keep-alive",
        }
    )

    while queue and len(rows) < limit:
        url = queue.popleft()
        if url in seen:
            continue
        seen.add(url)

        try:
            safe_url(url)
            started = time.perf_counter()
            response, insecure_tls = _request(
                session,
                url,
                timeout=(5, settings.request_timeout),
                allow_redirects=True,
            )
            elapsed = (time.perf_counter() - started) * 1000

            final_url = response.url
            content_type = response.headers.get("content-type", "")
            html = response.text if "text/html" in content_type.lower() else ""
            soup = BeautifulSoup(html, "html.parser")

            title = soup.title.get_text(" ", strip=True)[:500] if soup.title else ""
            meta = soup.find("meta", attrs={"name": "description"})
            meta_description = meta.get("content", "").strip()[:1000] if meta else ""

            images = soup.find_all("img")
            links = soup.find_all("a", href=True)
            internal, external = [], []
            for anchor in links:
                target = _clean_link(final_url, anchor.get("href"))
                if not target:
                    continue
                if urlparse(target).netloc.lower() == root:
                    internal.append(target)
                else:
                    external.append(target)

            for target in internal:
                if target not in seen and target not in queue and len(seen) + len(queue) < limit * 3:
                    queue.append(target)

            canonical_tag = soup.find("link", rel="canonical")
            canonical = canonical_tag.get("href", "").strip() if canonical_tag else ""
            text = " ".join(soup.stripped_strings)

            warnings_for_page = []
            if insecure_tls:
                warnings_for_page.append(
                    "TLS certificate could not be verified; fetched with certificate verification disabled."
                )
            if response.status_code >= 400:
                warnings_for_page.append(f"HTTP status {response.status_code}")

            rows.append(
                {
                    "url": url,
                    "status_code": response.status_code,
                    "title": title,
                    "meta_description": meta_description,
                    "h1": len(soup.find_all("h1")),
                    "h2": len(soup.find_all("h2")),
                    "h3": len(soup.find_all("h3")),
                    "images": len(images),
                    "missing_alt": sum(1 for img in images if not img.get("alt", "").strip()),
                    "internal_links": len(set(internal)),
                    "external_links": len(set(external)),
                    "broken_links": 0,
                    "canonical": canonical,
                    "https": final_url.startswith("https://"),
                    "word_count": len(text.split()),
                    "response_ms": round(elapsed, 2),
                    "error": " ".join(warnings_for_page),
                    "text": text[:120000],
                    "content_type": content_type,
                    "bytes": len(response.content),
                    "redirected": final_url.rstrip("/") != url.rstrip("/"),
                }
            )

        except RequestException as exc:
            rows.append(_empty_row(url, f"Request failed: {exc}"))
        except Exception as exc:
            rows.append(_empty_row(url, str(exc)))

    return rows


def site_files(start_url: str):
    p = urlparse(start_url)
    base = f"{p.scheme}://{p.netloc}"
    result = {}

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept": "*/*"})

    for name in ("robots.txt", "sitemap.xml"):
        target = f"{base}/{name}"
        try:
            safe_url(target)
            response, insecure_tls = _request(
                session,
                target,
                timeout=(5, settings.request_timeout),
            )
            result[name] = {
                "status": response.status_code,
                "text": response.text[:100000],
                "error": (
                    "TLS certificate could not be verified; fetched with certificate verification disabled."
                    if insecure_tls
                    else ""
                ),
            }
        except Exception as exc:
            result[name] = {"status": 0, "text": "", "error": str(exc)}

    return result
