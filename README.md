# SitePilot AI — Complete v5

## One-click startup
1. Extract this folder to a simple path such as `C:\Users\Nivedhitha\Downloads\SitePilot_AI_v5`.
2. Open the extracted folder.
3. Double-click `RUN_SITEPILOT.bat`.
4. Keep the backend window open.
5. Open `http://localhost:8000/`.

## Test order
- `https://example.com`
- `https://velammal.edu.in/`
- Reports → Generate Full PDF Report
- Analytics → upload `data\analytics_sample.csv`
- Lead Intelligence → upload `data\leads_demo.csv`

## v5 fixes
- Fixed a backend 500 caused by undefined analytics/lead count variables after a successful crawl.
- Auxiliary robots/sitemap requests can no longer turn a valid crawl into a server error.
- Optional PageSpeed failures do not break website analysis.
- Public websites with certificate-chain problems can use the recorded TLS fallback.
- PDF report generation remains available through POST and GET endpoints.
- PDF download page provides both automatic download and an Open PDF fallback.
- Failed audits clear stale previous results.

This prototype uses public website signals only and does not fabricate traffic, revenue, users, conversions, or private analytics.
