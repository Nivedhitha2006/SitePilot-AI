# 🚀 SitePilot AI
**AI-Powered Website Optimization & Digital Analytics Platform**
SitePilot AI is a full-stack application that analyzes websites, identifies SEO and technical issues, and provides actionable recommendations through an interactive dashboard and PDF reports.
## ✨ Key Features
- 🌐 **Website Crawling** – Extracts data from publicly accessible pages.
- 🔎 **SEO Analysis** – Checks titles, meta descriptions, headings, canonical URLs, and image ALT attributes.
- ⚡ **Performance Insights** – Collects response time, page size, and HTTP status information.
- 📝 **Content Analysis** – Examines word counts, headings, and keyword signals.
- 📊 **Interactive Dashboard** – Visualizes website analysis results.
- 🤖 **Lead Intelligence** – Uses a Random Forest classifier.
- 💡 **Recommendations** – Suggests prioritized website improvements.
- 📁 **Analytics Upload** – Processes supported CSV data.
- 📄 **PDF Reports** – Generates structured analysis reports.
## 🛠️ Tech Stack

| Component | Technologies |
|---|---|
| Frontend | React, Vite, Tailwind CSS |
| Backend | Python, FastAPI |
| Web Scraping | Requests, BeautifulSoup |
| Database | SQLite |
| Machine Learning | Random Forest |
| Visualization | Recharts |

## ⚙️ Run Locally

**Prerequisites:** Python, Node.js, npm, and Git.

**1. Clone the repository**
```bash
git clone https://github.com/Nivedhitha2006/SitePilot-AI.git
cd SitePilot-AI
```

**2. Start the backend**
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

**3. Start the frontend** in a second terminal:
```bash
cd frontend
npm install
npm run dev
```

Backend API: `http://localhost:8000`  
API Documentation: `http://localhost:8000/docs`

## 🔄 How It Works

1. Enter a website URL.
2. Crawl accessible website pages.
3. Analyze SEO, technical, and content signals.
4. View findings and recommendations.
5. Generate a PDF report.

## 🚀 Future Enhancements

- Google PageSpeed Insights integration
- Google Analytics and Search Console integration
- Website monitoring and historical comparisons
- Enhanced predictive analytics

## 👩‍💻 Author

**Nivedhitha K**  
B.Tech Artificial Intelligence and Data Science  
Velammal Engineering College, Chennai

- GitHub: [Nivedhitha2006](https://github.com/Nivedhitha2006)
- LinkedIn: [Nivedhitha K](https://www.linkedin.com/in/nivedhitha-k-a9ab87301/)

---

⭐ *Turning website data into actionable intelligence.*
