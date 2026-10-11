# MoveInSync Forward Deployed Engineer Case Study — Submission Guide

This guide provides everything you need to package, commit, push, and submit your case study project for the MoveInSync Forward Deployed Engineer (Intern to FTE) role.

---

## 1. Application Submission Fields (Ready to Copy & Paste)

### Field 5: Submission Link(s)
*GitHub / project / submission / solution link(s)*

> **Suggested Content:**
> ```text
> https://github.com/[YOUR_GITHUB_USERNAME]/MoveInSync_CaseStudy
> ```
> *(Replace `[YOUR_GITHUB_USERNAME]` with your actual GitHub username after pushing the repository).*

---

### Field 6: Related PPT, demo video, other demo, or project link(s)
*Related presentation, video demo, or alternative artifact links*

> **Suggested Content:**
> ```text
> Complete project repository, data pipeline, verified charts, and executive PDF report are available at:
> https://github.com/[YOUR_GITHUB_USERNAME]/MoveInSync_CaseStudy
>
> Direct link to executive PDF report:
> https://github.com/[YOUR_GITHUB_USERNAME]/MoveInSync_CaseStudy/blob/main/report/MoveInSync_Case_Study.pdf
> ```
> *(A separate PPT or demo video is not required; the complete repository and executive PDF deliver the full analysis).*

---

### Field 7: A short note on how the work was completed and which tools were used
*A concise, professional summary of your data collection, analytical methodology, and validation steps.*

> **Ready-to-Paste Text for Application Field 7:**
> ```text
> This case study analyzed 2,000 public Android reviews (Sept 2018 to Oct 2026) for the MoveInSync app (com.moveinsync.ets) collected via the open-source Python library google-play-scraper across dual passes: 1,400 newest reviews (avg rating 3.81) and 600 most-relevant reviews (avg rating 2.07). The data was processed using Python, Pandas, Matplotlib, and ReportLab.
>
> Rating distributions, temporal trends, and 13 operational complaint themes in 1-2 star reviews (n=800) were evaluated using deterministic keyword regex rules. Initial classifier logic was manually audited against a stratified 60-review validation sample. Substring leakage (e.g., 'assigning' triggering login rules) and plural commute shift terms ('logins and logouts slot') were corrected, achieving 100% precision post-refinement across the validation sample. Personally identifying details (emails, phone numbers, external IDs, client enterprise names) were scrubbed from all public excerpts.
>
> The analysis highlights that historical rating declines reflect Google Play's algorithmic preference for critical reviews rather than historical software degradation. Acknowledging that public reviews describe end-user symptoms rather than technical root causes, the submission delivers an FDE-focused roadmap—including offline trip pass caching, driver telemetry heartbeat monitoring, WhatsApp auth failover, and geofenced anti-ghosting checks—paired with the internal logs and experiments needed to validate each initiative.
> ```

---

### Field 8: Any other relevant link(s)
*Additional supporting links*

> **Recommendation:**
> Leave blank, or include your personal LinkedIn / portfolio link:
> ```text
> LinkedIn: https://www.linkedin.com/in/[YOUR_LINKEDIN_PROFILE]/
> ```

---

## 2. Deliverables Checklist

Confirm that all deliverables exist in your project folder before publishing:

- [x] **`data/raw_reviews.csv`** — 2,000 reviews collected (no scraping duplicates; 100% complete ratings & text).
- [x] **`data/app_listing.json`** — Google Play listing snapshot (4.64 score, 114,874 ratings, 1M+ installs).
- [x] **`src/collect_reviews.py`** — Documented review extraction script using `google-play-scraper`.
- [x] **`src/analyze_reviews.py`** — Verified analysis pipeline with calibrated keyword rules and trip normalization.
- [x] **`outputs/*.png`** — 5 verified charts (rating distribution, yearly trends, complaint themes, pass comparison, low vs high).
- [x] **`outputs/tables/*.csv`** — 9 verified CSV tables (including audited `theme_validation_sample.csv`).
- [x] **`outputs/analysis_summary.txt`** — Clean summary of empirical findings and hypotheses.
- [x] **`report/MoveInSync_Case_Study.md`** — 13-section comprehensive executive case study report.
- [x] **`report/MoveInSync_Case_Study.pdf`** — Polished, publication-ready PDF report compiled via ReportLab.
- [x] **`report/methodology_note.md`** — Detailed technical methodology note.
- [x] **`report/generate_pdf.py`** — Reproducible Python script to recompile the PDF report.
- [x] **`requirements.txt`** — Lean dependency list (`google-play-scraper`, `pandas`, `matplotlib`, `reportlab`).
- [x] **`.gitignore`** — Complete exclusion rules for virtual environments, caches, and temporary files.
- [x] **`README.md`** — Professional project documentation and reproduction instructions.
- [x] **`SUBMISSION_GUIDE.md`** — This submission guide.

---

## 3. GitHub Readiness & File Inclusion Guidelines

### Files to Commit to GitHub:
```text
MoveInSync_CaseStudy/
├── .gitignore
├── README.md
├── SUBMISSION_GUIDE.md
├── requirements.txt
├── data/
│   ├── app_listing.json
│   └── raw_reviews.csv
├── outputs/
│   ├── 01_rating_distribution.png
│   ├── 02_reviews_and_rating_by_year.png
│   ├── 03_complaint_themes.png
│   ├── 04_themes_newest_vs_most_relevant.png
│   ├── 05_low_vs_high_themes.png
│   ├── analysis_summary.txt
│   └── tables/
│       └── *.csv
├── report/
│   ├── MoveInSync_Case_Study.md
│   ├── MoveInSync_Case_Study.pdf
│   ├── generate_pdf.py
│   └── methodology_note.md
└── src/
    ├── analyze_reviews.py
    └── collect_reviews.py
```

### Files to EXCLUDE from GitHub:
- Virtual environments (`.venv/`, `venv/`, `env/`) — *covered by `.gitignore`*.
- Python cache (`__pycache__/`, `*.pyc`) — *covered by `.gitignore`*.
- Scratch scripts and temporary evaluation files (`scratch/`, `tmp/`) — *covered by `.gitignore`*.
- IDE settings (`.vscode/`, `.idea/`) — *covered by `.gitignore`*.
- Operating system files (`Thumbs.db`, `.DS_Store`) — *covered by `.gitignore`*.
- No API keys, credentials, or private internal client data exist in this repository.

---

## 4. Suggested GitHub Repository Details

- **Repository Name:** `MoveInSync_CaseStudy` (or `moveinsync-fde-case-study`)
- **Visibility:** **Public** (so hiring managers can review it)
- **Description:**
  ```text
  MoveInSync Forward Deployed Engineer Case Study: Empirical analysis of 2,000 public Play Store reviews, validated keyword taxonomy, and operational engineering recommendations.
  ```
- **Topics / Tags:**
  `moveinsync`, `forward-deployed-engineer`, `case-study`, `python`, `data-analysis`, `product-analytics`, `operations-engineering`

---

## 5. Exact Git Commands to Publish to GitHub

Open PowerShell in `C:\Users\ASUS\OneDrive\Desktop\MoveInSync_CaseStudy` and run:

### Step 1: Initialize Git and Check Status
```powershell
git init
git status
```

### Step 2: Stage and Commit the Verified Files
```powershell
git add .
git commit -m "feat: complete MoveInSync Forward Deployed Engineer case study submission"
```

### Step 3: Create GitHub Repository & Link Remote
1. Log in to [GitHub](https://github.com/) and click **New Repository**.
2. Name it `MoveInSync_CaseStudy`. Keep it **Public**. Do NOT check "Add a README" or ".gitignore" (these already exist locally).
3. Copy your remote repository URL (e.g. `https://github.com/[YOUR_USERNAME]/MoveInSync_CaseStudy.git`).

### Step 4: Push to GitHub
```powershell
git branch -M main
git remote add origin https://github.com/[YOUR_USERNAME]/MoveInSync_CaseStudy.git
git push -u origin main
```

---

## 6. Pre-Submission Final Verification

Before submitting the form, perform this 60-second sanity check:
1. Visit your GitHub URL in a private/incognito browser window to ensure it is public and readable.
2. Click on `report/MoveInSync_Case_Study.pdf` on GitHub and verify that the PDF previews properly.
3. Check `README.md` on GitHub to ensure all formatting, badges, and code blocks render cleanly.
4. Copy the ready-to-paste text from Section 1 into Application Field 7.
5. Paste your repository link into Field 5 and Field 6.
