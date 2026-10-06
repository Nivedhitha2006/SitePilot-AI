import os, json, uuid, re, statistics
from collections import Counter
from urllib.parse import urlparse, quote_plus, parse_qs, urljoin
from google import genai
import pandas as pd
import requests
from bs4 import BeautifulSoup

from fastapi import FastAPI, Depends, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse

from sqlalchemy.orm import Session

from app.database.db import get_db, Base, engine
from app.models.models import *
from app.schemas.schemas import AnalyzeRequest
from app.crawler.crawler import crawl, site_files, safe_url
from app.analyzers.seo import analyze
from app.services.performance import run
from app.recommendations.rules import build
from app.ml.leads import train_predict
from app.reports.pdf import make_pdf


# =========================================================
# DATABASE
# =========================================================

Base.metadata.create_all(bind=engine)


# =========================================================
# FASTAPI APPLICATION
# =========================================================

app = FastAPI(
    title="SitePilot AI Website Intelligence API",
    version="2.0.0"
)


# =========================================================
# CORS CONFIGURATION
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # Production Vercel frontend
        "https://site-pilot-ai-rose.vercel.app",

        # Local development
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
    ],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1):\d+$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/api/health")
def health():
    return {"status": "ok"}


# =========================================================
# PUBLIC ROW CLEANUP
# =========================================================

def _public_rows(rows):
    return [
        {
            **{k: v for k, v in r.items() if k != "text"},
            "type": _classify_page(
                r.get("url", ""),
                r.get("title", "")
            )
        }
        for r in rows
    ]


# =========================================================
# SITE NAME
# =========================================================

def _site_name(url):
    host = (
        urlparse(url)
        .netloc
        .lower()
        .replace("www.", "")
    )

    return host.split(".")[0].replace("-", " ").title()


# =========================================================
# PAGE CLASSIFICATION
# =========================================================

def _classify_page(url, title=""):
    s = (url + " " + title).lower()

    rules = [
        (
            "Admissions / Conversion",
            [
                "admission",
                "apply",
                "application",
                "enquiry",
                "enroll",
                "join",
                "registration",
            ],
        ),
        (
            "Academics / Services",
            [
                "academic",
                "course",
                "program",
                "department",
                "service",
                "curriculum",
                "syllabus",
            ],
        ),
        (
            "Placements / Careers",
            [
                "placement",
                "career",
                "recruit",
                "job",
                "internship",
                "training",
            ],
        ),
        (
            "Student Life / Activities",
            [
                "club",
                "activity",
                "event",
                "campus",
                "student",
                "hostel",
                "sports",
                "facility",
            ],
        ),
        (
            "News / Updates",
            [
                "news",
                "notice",
                "announcement",
                "event",
                "blog",
                "update",
            ],
        ),
        (
            "About / Trust",
            [
                "about",
                "accredit",
                "ranking",
                "award",
                "recognition",
                "history",
                "leadership",
            ],
        ),
        (
            "Contact / Location",
            [
                "contact",
                "location",
                "reach",
                "map",
                "address",
            ],
        ),
    ]

    for cat, words in rules:
        if any(w in s for w in words):
            return cat

    return "General / Information"


# =========================================================
# WEBSITE PROFILE
# =========================================================

def _website_profile(url, rows, seo):
    host = urlparse(url).netloc

    titles = [
        r.get("title")
        for r in rows
        if r.get("title")
    ]

    headings = " ".join(
        (r.get("title") or "")
        for r in rows
    )

    page_types = Counter(
        _classify_page(
            r.get("url", ""),
            r.get("title", "")
        )
        for r in rows
    )

    all_text = []

    # Crawler text is used for NLP before rows are persisted;
    # unavailable here, so derive from titles/meta/headings.
    for r in rows:
        all_text += [
            r.get("title", ""),
            r.get("meta_description", "")
        ]

    blob = " ".join(all_text)
    low = blob.lower()

    if any(
        x in low
        for x in [
            "college",
            "university",
            "institute",
            "admission",
            "student",
            "campus",
        ]
    ):
        site_type = "Education / Institution"

    elif any(
        x in low
        for x in [
            "shop",
            "cart",
            "product",
            "price",
            "checkout",
        ]
    ):
        site_type = "E-commerce / Retail"

    elif any(
        x in low
        for x in [
            "hospital",
            "doctor",
            "patient",
            "health",
        ]
    ):
        site_type = "Healthcare / Services"

    elif any(
        x in low
        for x in [
            "software",
            "technology",
            "platform",
            "solution",
            "api",
        ]
    ):
        site_type = "Technology / SaaS"

    else:
        site_type = "Public information / Organization"

    purpose = (
        f"{site_type} website that presents information, "
        f"services and navigation paths for visitors."
    )

    if site_type == "Education / Institution":
        purpose = (
            "Institutional website focused on programmes, admissions, "
            "academics, campus life, placements and visitor enquiries."
        )

    elif site_type == "E-commerce / Retail":
        purpose = (
            "Commercial website focused on products, discovery, "
            "shopping and conversion actions."
        )

    return {
        "site_name": _site_name(url),
        "domain": host,
        "site_type": site_type,
        "purpose": purpose,
        "pages_crawled": len(rows),
        "page_types": dict(page_types),
        "https_coverage": round(
            sum(
                1 for r in rows
                if r.get("https")
            ) / max(1, len(rows)) * 100,
            1
        ),
        "titles": titles[:10],
    }


# =========================================================
# PERFORMANCE SUMMARY
# =========================================================

def _performance_summary(rows, perf):
    times = [
        float(r.get("response_ms") or 0)
        for r in rows
        if r.get("status_code")
    ]

    sizes = [
        int(r.get("bytes") or 0)
        for r in rows
        if r.get("status_code")
    ]

    status = Counter(
        str(r.get("status_code") or "error")
        for r in rows
    )

    avg = (
        round(statistics.mean(times), 1)
        if times
        else None
    )

    p95 = (
        round(
            sorted(times)[
                max(0, int(len(times) * 0.95) - 1)
            ],
            1,
        )
        if times
        else None
    )

    slow = sorted(
        [
            {
                "url": r.get("url"),
                "response_ms": round(
                    float(r.get("response_ms") or 0),
                    1,
                ),
            }
            for r in rows
        ],
        key=lambda x: x["response_ms"],
        reverse=True,
    )[:5]

    return {
        "page_response_avg_ms": avg,
        "page_response_p95_ms": p95,
        "slow_pages": slow,
        "status_distribution": dict(status),
        "avg_page_bytes": (
            round(statistics.mean(sizes), 0)
            if sizes
            else None
        ),
        "https_coverage": round(
            sum(
                1 for r in rows
                if r.get("https")
            ) / max(1, len(rows)) * 100,
            1,
        ),
        "pages_with_errors": sum(
            1
            for r in rows
            if r.get("error")
            or int(r.get("status_code") or 0) >= 400
        ),
        "pagespeed": perf,
    }


# =========================================================
# CONTENT INTELLIGENCE
# =========================================================

def _content_intelligence(rows, seo):
    kws = seo.get("keywords", [])

    top = kws[:15]

    repetitive = [
        k
        for k in kws
        if k.get("coverage", 0) >= 50
    ][:10]

    niche = [
        k
        for k in kws
        if (
            k.get("coverage", 0) <= 30
            and k.get("count", 0) >= 2
        )
    ][:10]

    page_map = []

    for r in rows:
        page_map.append(
            {
                "url": r.get("url"),
                "title": r.get("title") or "Untitled",
                "words": r.get("word_count", 0),
                "type": _classify_page(
                    r.get("url", ""),
                    r.get("title", ""),
                ),
                "h1": r.get("h1", 0),
                "h2": r.get("h2", 0),
            }
        )

    return {
        "top_keywords": top,
        "repetitive_sitewide": repetitive,
        "distinctive_or_niche": niche,
        "page_content_map": page_map,
        "avg_words": seo.get(
            "stats", {}
        ).get("avg_words", 0),
        "duplicate_titles": seo.get(
            "stats", {}
        ).get("duplicate_titles", 0),
        "duplicate_meta": seo.get(
            "stats", {}
        ).get("duplicate_meta", 0),
        "improvements": [
            "Create topic-specific landing pages instead of repeating the same terms across every page.",
            "Strengthen pages with low word count where visitor intent needs more explanation.",
            "Use descriptive H1/H2 headings and internal links to connect related topics.",
        ],
    }


# =========================================================
# AUDIENCE INTELLIGENCE
# =========================================================

def _audience_intelligence(rows, content):
    categories = {
        "Prospective customers / visitors": [
            "product",
            "pricing",
            "service",
            "solution",
            "contact",
            "demo",
            "buy",
            "shop",
        ],
        "Prospective students / parents": [
            "admission",
            "course",
            "program",
            "student",
            "campus",
            "fee",
            "placement",
            "hostel",
            "academic",
        ],
        "Current students / users": [
            "student",
            "portal",
            "login",
            "notice",
            "event",
            "activity",
            "result",
            "timetable",
        ],
        "Recruiters / employers": [
            "placement",
            "career",
            "recruit",
            "company",
            "internship",
            "training",
        ],
        "Partners / professionals": [
            "research",
            "publication",
            "industry",
            "collaboration",
            "faculty",
            "department",
        ],
    }

    scores = {
        k: 0
        for k in categories
    }

    page_interest = []

    for r in rows:
        text = (
            (r.get("title") or "")
            + " "
            + (r.get("meta_description") or "")
            + " "
            + (r.get("url") or "")
        ).lower()

        local = []

        for cat, words in categories.items():
            hit = sum(
                text.count(w)
                for w in words
            )

            scores[cat] += hit

            if hit:
                local.append(
                    (cat, hit)
                )

        local.sort(
            key=lambda x: x[1],
            reverse=True
        )

        page_interest.append(
            {
                "url": r.get("url"),
                "title": r.get("title") or "Untitled",
                "likely_audience": (
                    local[0][0]
                    if local
                    else "General visitors"
                ),
                "interest_signal": (
                    local[0][1]
                    if local
                    else 0
                ),
                "page_type": _classify_page(
                    r.get("url", ""),
                    r.get("title", ""),
                ),
            }
        )

    ranked = sorted(
        scores.items(),
        key=lambda x: x[1],
        reverse=True,
    )

    maxs = max(
        [x[1] for x in ranked] or [1]
    )

    segments = [
        {
            "segment": k,
            "signal": v,
            "relative_interest": (
                round(v / maxs * 100, 1)
                if v
                else 0
            ),
        }
        for k, v in ranked
        if v > 0
    ]

    ranked_pages = sorted(
        page_interest,
        key=lambda x: x["interest_signal"],
        reverse=True,
    )[:10]

    funnel = []

    for r in ranked_pages:
        pt = r["page_type"]

        stage = "Awareness"

        if (
            "Admissions" in pt
            or "Contact" in pt
            or "Conversion" in pt
        ):
            stage = "Conversion"

        elif any(
            x in pt
            for x in [
                "Academics",
                "Placements",
                "Services",
            ]
        ):
            stage = "Consideration"

        funnel.append(
            {
                "url": r["url"],
                "stage": stage,
                "page_type": pt,
                "likely_audience": r["likely_audience"],
            }
        )

    return {
        "mode": "Inferred from public website structure",
        "disclaimer": (
            "This is not actual visitor analytics. "
            "It estimates audience intent from public page "
            "titles, URLs, metadata and site structure. "
            "Connect GA4/Search Console later for real user behaviour."
        ),
        "audience_segments": segments,
        "most_interest_pages": ranked_pages,
        "funnel": funnel,
        "conversion_opportunities": [
            "Make primary conversion actions visible in the header and key landing pages.",
            "Connect high-interest informational pages to enquiry/application/contact actions.",
            "Create audience-specific landing pages for the strongest inferred segments.",
        ],
    }


# =========================================================
# EXTRA RECOMMENDATIONS
# =========================================================

def _extra_recommendations(
    seo,
    profile,
    perf,
    content,
    audience
):
    out = []

    def add(
        priority,
        category,
        issue,
        explanation,
        solution,
        impact
    ):
        out.append(
            {
                "priority": priority,
                "category": category,
                "issue": issue,
                "explanation": explanation,
                "solution": solution,
                "expected_impact": impact,
            }
        )

    if profile["pages_crawled"] < 5:
        add(
            "MEDIUM",
            "Website Analysis",
            "Small crawl footprint",
            "Only a small number of pages were reachable within the crawl limit.",
            "Increase the crawl limit and ensure important pages are linked from crawlable navigation or the sitemap.",
            "Better coverage",
        )

    if profile["https_coverage"] < 100:
        add(
            "CRITICAL",
            "Security",
            "Some crawled pages are not HTTPS",
            "Mixed or insecure pages reduce trust and can create redirect/canonical issues.",
            "Force HTTPS with permanent redirects and update internal links/canonical URLs.",
            "High",
        )

    if content["repetitive_sitewide"]:
        add(
            "MEDIUM",
            "Content",
            "Keyword repetition is concentrated site-wide",
            "Some terms appear across a large share of crawled pages, which can weaken topical differentiation.",
            "Assign primary topics to individual pages and vary supporting terms according to search intent.",
            "Medium",
        )

    if content.get("distinctive_or_niche"):
        add(
            "HIGH",
            "Content",
            "Distinctive topics have limited coverage",
            "Some useful terms appear on only a small subset of pages.",
            "Build stronger topical clusters around these terms and link related pages together.",
            "High",
        )

    if audience["most_interest_pages"]:
        add(
            "HIGH",
            "Conversion",
            "High-intent pages need clearer next steps",
            "Pages showing strong inferred audience intent should guide visitors toward an action.",
            "Add contextual CTA buttons and internal links from high-interest pages to enquiry, application, contact or conversion pages.",
            "High",
        )

    if (
        perf["page_response_avg_ms"] is not None
        and perf["page_response_avg_ms"] > 1000
    ):
        add(
            "HIGH",
            "Performance",
            "Server response is slow on average",
            "Crawl response time is a real server/network signal from this audit.",
            "Investigate hosting latency, caching, database/API calls, compression and CDN usage.",
            "High",
        )

    add(
        "MEDIUM",
        "Accessibility",
        "Improve accessible navigation",
        "Public-site crawls can reveal image ALT and heading issues but cannot fully test assistive technology.",
        "Add descriptive ALT text, logical headings, visible focus states, keyboard navigation and accessible form labels.",
        "Medium",
    )

    add(
        "MEDIUM",
        "Analytics",
        "Instrument real visitor measurement",
        "Public crawling cannot reveal actual page views, sessions or user journeys.",
        "Connect GA4/Search Console or upload an export so page engagement and acquisition can be measured instead of inferred.",
        "High",
    )

    return out

# ---------------------------------------------------------
# Gemini website-name resolver
# ---------------------------------------------------------

GEMINI_API_KEY = os.getenv("LLM_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("LLM_MODEL", "gemini-3.8-flash").strip()

gemini_client = None

if GEMINI_API_KEY:
    try:
        gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        print("Gemini initialization failed:", e)


def _resolve_with_gemini(site_name: str):
    if not gemini_client:
        return None

    prompt = f"""
Find the official public website for this organization, company,
college, university, institution, or website name:

{site_name}

Use Google Search.

Rules:
1. Return only the official homepage URL.
2. Do not return Facebook, Instagram, LinkedIn, YouTube, Wikipedia,
   Justdial, IndiaMART, directories, review sites, or other third-party pages.
3. Prefer the organization's own official domain.
4. If you cannot identify a reliable official website, return NONE.
"""

    try:
        interaction = gemini_client.interactions.create(
            model=GEMINI_MODEL,
            input=prompt,
            tools=[{"type": "google_search"}],
        )

        text = getattr(interaction, "output_text", "") or ""

        urls = re.findall(
            r'https?://[^\s<>"\'\]\[)]+',
            text
        )

        blocked_domains = {
            "facebook.com",
            "instagram.com",
            "linkedin.com",
            "youtube.com",
            "wikipedia.org",
            "justdial.com",
            "indiamart.com",
            "twitter.com",
            "x.com",
        }

        for candidate in urls:
            candidate = candidate.rstrip(".,;:)]}")

            try:
                parsed = urlparse(candidate)
                host = (parsed.hostname or "").lower()

                if not host:
                    continue

                if any(
                    host == d or host.endswith("." + d)
                    for d in blocked_domains
                ):
                    continue

                safe_url(candidate)

                return candidate

            except Exception:
                continue

        return None

    except Exception as e:
        print("Gemini website resolver error:", e)
        return None
# =========================================================
# WEBSITE RESOLUTION
# =========================================================

@app.get('/api/resolve-site')
def resolve_site(q: str = Query(..., min_length=2, max_length=200)):
    q = q.strip()

    # 1. Direct URL
    if re.match(r'^https?://', q, re.I):
        try:
            return {
                'query': q,
                'url': safe_url(q),
                'source': 'direct'
            }
        except Exception as e:
            raise HTTPException(400, str(e))

    # 2. Domain entered without https://
    if re.match(r'^[\w.-]+\.[A-Za-z]{2,}(/.*)?$', q):
        u = 'https://' + q

        try:
            safe_url(u)

            return {
                'query': q,
                'url': u,
                'source': 'domain heuristic'
            }

        except Exception:
            pass

    # 3. Gemini + Google Search
    gemini_url = _resolve_with_gemini(q)

    if gemini_url:
        return {
            'query': q,
            'url': gemini_url,
            'source': 'gemini google search'
        }

    # 4. Existing public-search fallback
    headers = {
        'User-Agent':
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 Chrome/126 Safari/537.36'
    }

    candidates = []

    for engine in [
        f'https://www.google.com/search?q={quote_plus(q)}',
        f'https://html.duckduckgo.com/html/?q={quote_plus(q)}'
    ]:
        try:
            r = requests.get(
                engine,
                headers=headers,
                timeout=8
            )

            soup = BeautifulSoup(r.text, 'html.parser')

            for a in soup.find_all('a', href=True):
                href = a.get('href', '')

                if (
                    'google.' in urlparse(href).netloc.lower()
                    or
                    'duckduckgo.' in urlparse(href).netloc.lower()
                ):
                    continue

                if href.startswith('/url?'):
                    href = parse_qs(
                        urlparse(href).query
                    ).get('q', [''])[0]

                if href.startswith('//'):
                    href = 'https:' + href

                if href.startswith(('http://', 'https://')):
                    candidates.append(href)

            if candidates:
                break

        except Exception:
            continue

    blocked_domains = {
        'facebook.com',
        'instagram.com',
        'youtube.com',
        'linkedin.com',
        'x.com',
        'twitter.com',
        'wikipedia.org',
        'justdial.com',
        'indiamart.com',
    }

    for candidate in candidates:
        try:
            p = urlparse(candidate)
            host = (p.hostname or '').lower()

            if not host:
                continue

            if any(
                host == d or host.endswith("." + d)
                for d in blocked_domains
            ):
                continue

            safe_url(candidate)

            return {
                'query': q,
                'url': candidate.split('#')[0],
                'source': 'public search'
            }

        except Exception:
            continue

    raise HTTPException(
        404,
        'Could not resolve that name to a public website. '
        'Try saying the website URL or type the domain.'
    )

# =========================================================
# WEBSITE ANALYSIS
# =========================================================

@app.post("/api/analyze")
def analyze_site(
    req: AnalyzeRequest,
    db: Session = Depends(get_db)
):
    url = (
        str(req.url)
        .strip()
        .rstrip("/")
    )

    try:
        safe_url(url)

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )

    try:
        rows = crawl(
            url,
            req.max_pages
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )

    except requests.RequestException as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Could not fetch the website: {exc}"
        )

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Could not fetch the website: {exc}"
        )

    successful = [
        r
        for r in rows
        if int(r.get("status_code") or 0) > 0
    ]

    if not successful:
        detail = next(
            (
                r.get("error")
                for r in rows
                if r.get("error")
            ),
            "No pages could be fetched."
        )

        raise HTTPException(
            status_code=502,
            detail=(
                "Could not fetch the website: "
                f"{detail}"
            )
        )

    # Auxiliary public files must never turn a
    # successful crawl into a 500.
    try:
        files = site_files(url)

    except Exception as exc:
        files = {
            "robots.txt": {
                "status": 0,
                "text": "",
                "error": str(exc),
            },
            "sitemap.xml": {
                "status": 0,
                "text": "",
                "error": str(exc),
            },
        }

    try:
        seo = analyze(
            rows,
            files
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Website analysis failed: "
                f"{exc}"
            )
        )

    # PageSpeed is optional; the crawl remains usable
    # when the external API is unavailable or misconfigured.
    try:
        perf = run(url)

    except Exception as exc:
        perf = {
            "available": False,
            "performance_score": None,
            "message":
                f"Performance API unavailable: {exc}",
        }

    profile = _website_profile(
        url,
        rows,
        seo
    )

    content = _content_intelligence(
        rows,
        seo
    )

    performance = _performance_summary(
        rows,
        perf
    )

    audience = _audience_intelligence(
        rows,
        content
    )

    recs = (
        build(seo["issues"])
        + _extra_recommendations(
            seo,
            profile,
            performance,
            content,
            audience
        )
    )

    seen_rec = set()

    recs = [
        r
        for r in recs
        if not (
            r["issue"] in seen_rec
            or seen_rec.add(r["issue"])
        )
    ]

    w = (
        db.query(Website)
        .filter_by(url=url)
        .first()
        or Website(url=url)
    )

    db.add(w)
    db.commit()
    db.refresh(w)

    db.query(CrawlResult).filter_by(
        website_id=w.id
    ).delete()

    db.query(Keyword).filter_by(
        website_id=w.id
    ).delete()

    db.query(Recommendation).filter_by(
        website_id=w.id
    ).delete()

    db.query(SEOResult).filter_by(
        website_id=w.id
    ).delete()

    db.query(PerformanceResult).filter_by(
        website_id=w.id
    ).delete()

    for r in _public_rows(rows):
        db.add(
            CrawlResult(
                website_id=w.id,
                **{
                    k: r.get(k)
                    for k in [
                        "url",
                        "status_code",
                        "title",
                        "meta_description",
                        "h1",
                        "h2",
                        "h3",
                        "images",
                        "missing_alt",
                        "internal_links",
                        "external_links",
                        "broken_links",
                        "canonical",
                        "https",
                        "word_count",
                        "response_ms",
                        "error",
                    ]
                },
            )
        )

    db.add(
        SEOResult(
            website_id=w.id,
            score=seo["score"],
            technical_score=seo["technical_score"],
            content_score=seo["content_score"],
            issues_json=json.dumps(
                seo["issues"]
            ),
        )
    )

    for k in seo["keywords"]:
        db.add(
            Keyword(
                website_id=w.id,
                phrase=k["phrase"],
                count=k["count"],
                density=k["density"],
            )
        )

    db.add(
        PerformanceResult(
            website_id=w.id,
            available=perf.get(
                "available",
                False
            ),
            performance_score=perf.get(
                "performance_score"
            ),
            lcp=perf.get("lcp"),
            cls=perf.get("cls"),
            inp=perf.get("inp"),
            raw_json=json.dumps(
                perf.get(
                    "raw_json",
                    {}
                )
            ),
            message=perf.get(
                "message",
                ""
            ),
        )
    )

    for r in recs:
        db.add(
            Recommendation(
                website_id=w.id,
                **r
            )
        )

    db.commit()

    # Counts are calculated here before returning the response.
    analytics_count = db.query(
        AnalyticsData
    ).filter_by(
        website_id=w.id
    ).count()

    lead_count = db.query(
        Lead
    ).filter_by(
        website_id=w.id
    ).count()

    prediction_count = db.query(
        LeadPrediction
    ).filter_by(
        website_id=w.id
    ).count()

    high_intent_count = db.query(
        LeadPrediction
    ).filter(
        LeadPrediction.website_id == w.id,
        LeadPrediction.intent == "High",
    ).count()

    public = _public_rows(rows)

    return {
        "website_id": w.id,
        "url": url,

        "overview": {
            "gist": profile["purpose"],
            "verdict": (
                "Strong foundation"
                if seo["score"] >= 80
                else (
                    "Needs improvement"
                    if seo["score"] >= 60
                    else "Major improvement needed"
                )
            ),
            "score": seo["score"],
            "site_name": profile["site_name"],
            "site_type": profile["site_type"],
            "pages_crawled": len(rows),
            "top_opportunity": (
                recs[0]["issue"]
                if recs
                else "No major issue detected"
            ),
        },

        "website_analysis": {
            "profile": profile,
            "pages": public,
            "strengths": [
                "HTTPS coverage is measured directly from crawled URLs.",
                "Page structure, headings, metadata and links are inspected page-by-page.",
                "Recommendations are tied to observed public signals.",
            ],
            "limitations": [
                "A public crawl cannot see private dashboards, actual traffic, conversions or backend systems."
            ],
        },

        "seo": seo,
        "performance": performance,
        "content": content,

        "analytics": {
            **audience,
            "imported_rows": analytics_count,
        },

        "lead_intelligence": {
            **audience,
            "imported_leads": lead_count,
            "predictions": prediction_count,
            "high_intent_predictions": high_intent_count,
        },

        "recommendations": recs,
        "pages": public,
        "files": files,
    }


# =========================================================
# GET SAVED ANALYSIS
# =========================================================

@app.get("/api/analysis/{website_id}")
def get_analysis(
    website_id: int,
    db: Session = Depends(get_db)
):
    w = db.get(
        Website,
        website_id
    )

    if not w:
        raise HTTPException(
            404,
            "Website not found"
        )

    s = (
        db.query(SEOResult)
        .filter_by(
            website_id=website_id
        )
        .order_by(
            SEOResult.id.desc()
        )
        .first()
    )

    p = (
        db.query(PerformanceResult)
        .filter_by(
            website_id=website_id
        )
        .order_by(
            PerformanceResult.id.desc()
        )
        .first()
    )

    rows = db.query(
        CrawlResult
    ).filter_by(
        website_id=website_id
    ).all()

    rec_rows = db.query(
        Recommendation
    ).filter_by(
        website_id=website_id
    ).all()

    kws = db.query(
        Keyword
    ).filter_by(
        website_id=website_id
    ).all()

    public = [
        {
            "url": r.url,
            "status_code": r.status_code,
            "title": r.title,
            "meta_description": r.meta_description,
            "h1": r.h1,
            "h2": r.h2,
            "h3": r.h3,
            "images": r.images,
            "missing_alt": r.missing_alt,
            "internal_links": r.internal_links,
            "external_links": r.external_links,
            "broken_links": r.broken_links,
            "canonical": r.canonical,
            "https": r.https,
            "word_count": r.word_count,
            "response_ms": r.response_ms,
            "error": r.error,
        }
        for r in rows
    ]

    issues = (
        json.loads(s.issues_json)
        if s
        else []
    )

    seo = {
        "score":
            s.score if s else None,
        "technical_score":
            s.technical_score if s else None,
        "content_score":
            s.content_score if s else None,
        "issues": issues,
        "keywords": [
            {
                "phrase": k.phrase,
                "count": k.count,
                "density": k.density,
            }
            for k in kws
        ],
        "stats": {
            "pages": len(rows),
            "avg_words": round(
                sum(
                    (r.word_count or 0)
                    for r in rows
                ) / max(1, len(rows)),
                1,
            ),
        },
    }

    perf = (
        {
            "available": p.available,
            "performance_score":
                p.performance_score,
            "lcp": p.lcp,
            "cls": p.cls,
            "inp": p.inp,
            "message": p.message,
        }
        if p
        else {
            "available": False,
            "performance_score": None,
            "message":
                "Performance API unavailable",
        }
    )

    return {
        "website_id": website_id,
        "url": w.url,
        "pages": public,
        "seo": seo,
        "performance": perf,
        "recommendations": [
            {
                "id": r.id,
                "priority": r.priority,
                "category": r.category,
                "issue": r.issue,
                "explanation": r.explanation,
                "solution": r.solution,
                "expected_impact":
                    r.expected_impact,
            }
            for r in rec_rows
        ],
    }


# =========================================================
# ANALYTICS UPLOAD
# =========================================================

@app.post("/api/analytics/{website_id}")
async def upload_analytics(
    website_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if not db.get(
        Website,
        website_id
    ):
        raise HTTPException(
            404,
            "Website not found. Run an audit first."
        )

    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            400,
            "CSV only"
        )

    data = await file.read()

    if len(data) > 10 * 1024 * 1024:
        raise HTTPException(
            413,
            "File too large"
        )

    try:
        df = pd.read_csv(
            __import__("io")
            .BytesIO(data)
        )

    except Exception as e:
        raise HTTPException(
            400,
            f"Invalid CSV: {e}"
        )

    db.query(
        AnalyticsData
    ).filter_by(
        website_id=website_id
    ).delete()

    for _, row in df.head(10000).iterrows():
        db.add(
            AnalyticsData(
                website_id=website_id,
                row_json=row.where(
                    pd.notna(row),
                    None
                ).to_json(),
            )
        )

    db.commit()

    return {
        "rows": len(df),
        "columns": df.columns.tolist(),
        "preview": (
            df.head(10)
            .fillna("")
            .to_dict("records")
        ),
    }


# =========================================================
# LEADS UPLOAD
# =========================================================

@app.post("/api/leads/{website_id}")
async def upload_leads(
    website_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if not db.get(
        Website,
        website_id
    ):
        raise HTTPException(
            404,
            "Website not found. Run an audit first."
        )

    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            400,
            "CSV only"
        )

    data = await file.read()

    try:
        df = pd.read_csv(
            __import__("io")
            .BytesIO(data)
        )

    except Exception as e:
        raise HTTPException(
            400,
            f"Invalid CSV: {e}"
        )

    if len(df) > 20000:
        df = df.head(20000)

    try:
        metrics, preds = train_predict(df)

    except Exception as e:
        raise HTTPException(
            400,
            str(e)
        )

    db.query(
        Lead
    ).filter_by(
        website_id=website_id
    ).delete()

    db.query(
        LeadPrediction
    ).filter_by(
        website_id=website_id
    ).delete()

    for _, row in df.iterrows():
        db.add(
            Lead(
                website_id=website_id,
                row_json=row.where(
                    pd.notna(row),
                    None
                ).to_json(),
            )
        )

    for p in preds:
        db.add(
            LeadPrediction(
                website_id=website_id,
                lead_key=p["lead_id"],
                score=p["score"],
                probability=p["probability"],
                intent=p["intent"],
            )
        )

    db.commit()

    return {
        "rows": len(df),
        "metrics": metrics,
        "predictions": preds[:100],
    }


# =========================================================
# RECOMMENDATIONS
# =========================================================

@app.get("/api/recommendations/{website_id}")
def recommendations(
    website_id: int,
    db: Session = Depends(get_db)
):
    return [
        r.__dict__
        for r in db.query(
            Recommendation
        )
        .filter_by(
            website_id=website_id
        )
        .all()
    ]


# =========================================================
# REPORT GENERATION
# =========================================================

def _report_file(
    website_id: int,
    db: Session
):
    w = db.get(
        Website,
        website_id
    )

    if not w:
        raise HTTPException(
            404,
            "Website not found"
        )

    s = (
        db.query(SEOResult)
        .filter_by(
            website_id=website_id
        )
        .order_by(
            SEOResult.id.desc()
        )
        .first()
    )

    p = (
        db.query(PerformanceResult)
        .filter_by(
            website_id=website_id
        )
        .order_by(
            PerformanceResult.id.desc()
        )
        .first()
    )

    recs = db.query(
        Recommendation
    ).filter_by(
        website_id=website_id
    ).all()

    rows = db.query(
        CrawlResult
    ).filter_by(
        website_id=website_id
    ).all()

    kws = db.query(
        Keyword
    ).filter_by(
        website_id=website_id
    ).all()

    if not s:
        raise HTTPException(
            409,
            "No completed website analysis exists for this website."
        )

    public = [
        {
            "url": r.url,
            "status_code": r.status_code,
            "title": r.title,
            "meta_description":
                r.meta_description,
            "h1": r.h1,
            "h2": r.h2,
            "h3": r.h3,
            "images": r.images,
            "missing_alt":
                r.missing_alt,
            "word_count":
                r.word_count,
            "response_ms":
                r.response_ms,
            "https": r.https,
            "internal_links":
                r.internal_links,
            "external_links":
                r.external_links,
            "broken_links":
                r.broken_links,
            "error": r.error,
            "type": _classify_page(
                r.url,
                r.title
            ),
        }
        for r in rows
    ]

    seo = {
        "score": s.score,
        "technical_score":
            s.technical_score,
        "content_score":
            s.content_score,
        "issues":
            json.loads(
                s.issues_json or "[]"
            ),
        "stats": {
            "pages": len(rows),
            "avg_words": round(
                sum(
                    (x.word_count or 0)
                    for x in rows
                ) / max(1, len(rows)),
                1,
            ),
        },
        "keywords": [
            {
                "phrase": k.phrase,
                "count": k.count,
                "density": k.density,
            }
            for k in kws
        ],
    }

    times = [
        float(x.response_ms or 0)
        for x in rows
        if x.status_code
    ]

    performance = {
        "page_response_avg_ms":
            round(
                statistics.mean(times),
                1
            )
            if times
            else None,

        "page_response_p95_ms":
            round(
                sorted(times)[
                    max(
                        0,
                        int(
                            len(times)
                            * 0.95
                        ) - 1,
                    )
                ],
                1,
            )
            if times
            else None,

        "avg_page_bytes": None,

        "pages_with_errors":
            sum(
                1
                for x in rows
                if x.error
                or int(
                    x.status_code or 0
                ) >= 400
            ),

        "https_coverage":
            round(
                sum(
                    1 for x in rows
                    if x.https
                )
                / max(1, len(rows))
                * 100,
                1,
            ),

        "pagespeed": {
            "available":
                bool(
                    p
                    and p.available
                ),
            "performance_score":
                p.performance_score
                if p
                else None,
            "lcp":
                p.lcp
                if p
                else None,
            "cls":
                p.cls
                if p
                else None,
            "inp":
                p.inp
                if p
                else None,
            "message":
                p.message
                if p
                else "Performance API unavailable",
        },
    }

    content = {
        "top_keywords":
            seo["keywords"][:40],

        "repetitive_sitewide": [],

        "distinctive_or_niche": [],

        "avg_words":
            seo["stats"]["avg_words"],

        "duplicate_titles": 0,

        "duplicate_meta": 0,

        "improvements": [
            "Create topic-specific landing pages instead of repeating the same terms across every page.",
            "Strengthen pages with low word count where visitor intent needs more explanation.",
            "Use descriptive H1/H2 headings and internal links to connect related topics.",
        ],

        "page_content_map": [
            {
                "url": x["url"],
                "title":
                    x["title"]
                    or "Untitled",
                "words":
                    x["word_count"]
                    or 0,
                "type": x["type"],
                "h1":
                    x["h1"]
                    or 0,
                "h2":
                    x["h2"]
                    or 0,
            }
            for x in public
        ],
    }

    # Reuse the same public-intent logic
    # used by the live dashboard.
    audience = _audience_intelligence(
        [
            {
                "url": x["url"],
                "title": x["title"],
                "meta_description":
                    x["meta_description"],
            }
            for x in public
        ],
        content,
    )

    profile = {
        "site_name":
            _site_name(w.url),

        "domain":
            urlparse(w.url).netloc,

        "site_type":
            "Public website / organization",

        "purpose":
            f"Public website audit of {w.url}.",

        "pages_crawled":
            len(rows),

        "page_types":
            dict(
                Counter(
                    x["type"]
                    for x in public
                )
            ),

        "https_coverage":
            performance[
                "https_coverage"
            ],
    }

    analytics_count = db.query(
        AnalyticsData
    ).filter_by(
        website_id=website_id
    ).count()

    lead_count = db.query(
        Lead
    ).filter_by(
        website_id=website_id
    ).count()

    prediction_count = db.query(
        LeadPrediction
    ).filter_by(
        website_id=website_id
    ).count()

    high_intent_count = db.query(
        LeadPrediction
    ).filter(
        LeadPrediction.website_id
        == website_id,

        LeadPrediction.intent
        == "High",
    ).count()

    data = {
        "url": w.url,

        "overview": {
            "gist":
                f"Public website audit of {w.url}.",

            "site_name":
                _site_name(w.url),

            "verdict": (
                "Strong foundation"
                if seo["score"] >= 80
                else (
                    "Needs improvement"
                    if seo["score"] >= 60
                    else "Major improvement needed"
                )
            ),

            "score":
                seo["score"],

            "top_opportunity":
                recs[0].issue
                if recs
                else "No major issue detected",
        },

        "website_analysis": {
            "profile": profile,
            "pages": public,
        },

        "pages": public,
        "seo": seo,
        "performance": performance,
        "content": content,
        "analytics": audience,
        "lead_intelligence": audience,

        "recommendations": [
            {
                "priority":
                    r.priority,
                "category":
                    r.category,
                "issue":
                    r.issue,
                "explanation":
                    r.explanation,
                "solution":
                    r.solution,
                "expected_impact":
                    r.expected_impact,
            }
            for r in recs
        ],
    }

    path = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "reports",
            f"report_{website_id}_"
            f"{uuid.uuid4().hex[:8]}.pdf",
        )
    )

    try:
        make_pdf(
            path,
            data
        )

    except Exception as exc:
        raise HTTPException(
            500,
            f"PDF generation failed: {exc}"
        )

    db.add(
        Report(
            website_id=website_id,
            path=path
        )
    )

    db.commit()

    return path


# =========================================================
# REPORT ENDPOINTS
# =========================================================

@app.post("/api/report/{website_id}")
def report(
    website_id: int,
    db: Session = Depends(get_db)
):
    path = _report_file(
        website_id,
        db
    )

    return FileResponse(
        path,
        media_type="application/pdf",
        filename=os.path.basename(path),
        headers={
            "Cache-Control":
                "no-store"
        },
    )


@app.get("/api/report/{website_id}")
def report_get(
    website_id: int,
    db: Session = Depends(get_db)
):
    path = _report_file(
        website_id,
        db
    )

    return FileResponse(
        path,
        media_type="application/pdf",
        filename=os.path.basename(path),
        headers={
            "Cache-Control":
                "no-store"
        },
    )


# =========================================================
# OPTIONAL FRONTEND SERVING
# =========================================================

# Optional single-process mode:
# after `npm run build`, FastAPI serves the React app.

from fastapi.staticfiles import StaticFiles

_FRONTEND_DIST = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "frontend",
        "dist",
    )
)

if os.path.isdir(_FRONTEND_DIST):

    app.mount(
        "/assets",
        StaticFiles(
            directory=os.path.join(
                _FRONTEND_DIST,
                "assets"
            )
        ),
        name="assets",
    )

    @app.get(
        "/{full_path:path}",
        response_class=HTMLResponse
    )
    def frontend_fallback(
        full_path: str
    ):
        if (
            full_path.startswith("api/")
            or full_path == "api"
        ):
            raise HTTPException(
                404,
                "API route not found"
            )

        index_file = os.path.join(
            _FRONTEND_DIST,
            "index.html"
        )

        if os.path.exists(index_file):
            return FileResponse(
                index_file,
                media_type="text/html"
            )

        raise HTTPException(
            404,
            "Frontend build not found. "
            "Run the single-start script first."
        )