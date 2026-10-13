SitePilot AI 🚀

AI-Powered Website Intelligence, Optimization & Digital Analytics Platform

SitePilot AI is a full-stack website intelligence platform that analyzes publicly accessible websites and transforms website data into actionable SEO insights, content intelligence, performance signals, lead insights, and prioritized optimization recommendations.

The project combines web crawling, automated analysis, machine learning, data visualization, and PDF reporting in one interactive dashboard.

---

📌 Project Overview

Website owners often need to inspect SEO health, website structure, content quality, performance, and conversion opportunities using multiple tools. SitePilot AI brings these analysis capabilities together in a centralized application.

Users can submit a website URL, analyze its publicly accessible pages, explore the findings through a dashboard, and generate a structured PDF report.

🎯 Key Objectives

- Automate website auditing and page-level analysis.
- Identify common SEO and technical issues.
- Extract content and keyword insights.
- Measure available website performance signals.
- Generate prioritized, actionable recommendations.
- Explore analytics data and machine-learning-based lead insights.
- Simplify website analysis through an interactive dashboard and PDF reports.

---

✨ Key Features

Feature| Description
🌐 Website Crawling| Crawls publicly accessible pages within the target website's domain.
🔎 SEO Analysis| Examines page titles, meta descriptions, headings, canonical URLs, HTTPS, image ALT attributes, and other SEO signals.
⚡ Performance Insights| Captures available response-time, page-size, and HTTP-status information. Optional PageSpeed integration can provide additional metrics when configured.
📝 Content Intelligence| Analyzes word counts, headings, keyword signals, and potential content improvements.
📊 Interactive Dashboard| Presents website analysis findings in a centralized visual interface.
🧠 Audience Intelligence| Infers potential audience intent and content opportunities from available website information.
🤖 Lead Intelligence| Uses a Random Forest-based machine-learning component for lead analysis based on available engagement features.
💡 Recommendation Engine| Organizes optimization suggestions by issue, category, priority, and potential impact.
📁 Analytics Upload| Accepts CSV analytics data for numeric summaries and analysis.
📄 PDF Reporting| Generates a structured report containing website findings and recommendations.
🎙️ Convenient Input| Supports website URL input, website-name resolution, and voice input in the interface.

---

Architecture Highlights

- Frontend: Provides the interface for website input, analysis results, charts, and reports.
- Backend: Handles API requests, crawling, analysis, and report generation.
- Analysis modules: Extract SEO, performance, and content signals from website pages.
- Intelligence modules: Produce recommendations and support audience and lead analysis.
- Database: SQLite stores application analysis data locally.
- Reporting: Converts available analysis results into a downloadable PDF report.

---

🛠️ Technology Stack

Layer| Technologies
Frontend| React, Vite
UI and Styling| Tailwind CSS, Lucide Icons
Data Visualization| Recharts
Backend| Python, FastAPI
Web Crawling| Requests, BeautifulSoup
Database| SQLite
Machine Learning| Random Forest
Reporting| PDF generation
API Documentation| FastAPI / Swagger UI

---

🔄 How It Works

1. Enter a website: Provide a public website URL or use a supported website-name resolution option.
2. Validate the URL: Check and validate the target before analysis.
3. Crawl pages: Retrieve publicly accessible pages within the configured crawl scope.
4. Analyze the website: Examine SEO, technical, performance, content, and keyword signals.
5. Generate intelligence: Process available data for audience insights, lead analysis, and optimization suggestions.
6. Explore the dashboard: Review findings and visual summaries.
7. Generate a report: Export the analysis into a structured PDF.

---

🖥️ Run Locally

Prerequisites

- Python 3.10 or a compatible version supported by the project's dependencies
- Node.js and npm
- Git

1. Clone the repository

git clone https://github.com/Nivedhitha2006/SitePilot-AI.git
cd SitePilot-AI

2. Start the backend

Open a terminal:

cd backend
python -m venv .venv

Activate the environment on Windows:

.\.venv\Scripts\Activate.ps1

Install dependencies and start FastAPI:

python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload

Backend URL:

"http://localhost:8000"

Interactive API documentation:

"http://localhost:8000/docs"

3. Start the frontend

Open a second terminal from the repository root:

cd frontend
npm install
npm run dev

Open the local frontend URL printed by Vite, usually:

"http://localhost:5173"

Keep both terminals running while using the application.

«Configuration note: The frontend should point to the local backend API. If your frontend uses "VITE_API_URL", configure it according to the API base URL expected by the frontend's API client. Check the existing project configuration before changing it.»

---

🧪 Testing the API

Once the backend is running, open:

"http://localhost:8000/docs"

The API documentation provides interactive access to the application's endpoints, including:

- "GET /api/health" — check backend health.
- "GET /api/resolve-site" — resolve a website query.
- "POST /api/analyze" — analyze a website.
- "GET /api/analysis/{website_id}" — retrieve saved analysis.
- "POST /api/analytics/{website_id}" — upload analytics data.
- "POST /api/leads/{website_id}" — upload lead data.
- "GET /api/recommendations/{website_id}" — retrieve recommendations.
- "POST /api/report/{website_id}" — generate a PDF report.

Use a public website you are authorized to analyze. Endpoint availability may depend on the current project version.

---

🚀 Future Enhancements

- Integrate Google PageSpeed Insights and Google Analytics.
- Add Google Search Console data integration.
- Improve crawling support for dynamic websites.
- Introduce website monitoring and historical comparisons.
- Expand competitor and keyword-gap analysis.
- Enhance recommendation quality using additional validation and evaluation.
- Extend predictive analytics and reporting capabilities.
- Explore secure multi-user deployment.

---

👩‍💻 Author

Nivedhitha K
B.Tech — Artificial Intelligence and Data Science
Velammal Engineering College, Chennai

- GitHub: "@Nivedhitha2006" (https://github.com/Nivedhitha2006)
- LinkedIn: "Nivedhitha K" (https://www.linkedin.com/in/nivedhitha-k-a9ab87301/)

---

⭐ Support

If you find this project interesting, consider starring the repository and sharing feedback.

SitePilot AI — Turning website data into actionable intelligence.
