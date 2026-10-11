# MoveInSync Forward Deployed Engineer Case Study
## Transforming Employee Commute Reliability: An Evidence-Based Operational & Product Analysis

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Dataset](https://img.shields.io/badge/reviews-2%2C000%20analyzed-green.svg)](data/raw_reviews.csv)
[![Report](https://img.shields.io/badge/report-PDF%20%26%20Markdown-orange.svg)](report/)

An end-to-end, reproducible empirical case study analyzing 2,000 public Android reviews for the MoveInSync enterprise commute app (`com.moveinsync.ets`), completed for the **Forward Deployed Engineer (Intern to FTE)** opportunity at MoveInSync.

---

## 1. Project Overview & Business Context

MoveInSync is the world’s largest enterprise employee commute platform, serving over 400 clients, including 97 Fortune 500 enterprises, managing 7,200+ vehicles (including 925+ EVs). In this enterprise B2B2C ecosystem, corporate commuters rely on MoveInSync to reach office shifts on time and return home safely.

Unlike consumer ride-hailing platforms where users can switch providers during outages, enterprise commuters are tied to their organization's transport system. A software crash or allocation failure directly impacts enterprise SLAs, transport safety compliance, and employee productivity.

This project delivers:
1. **Verified Review Analysis:** Empirical audit of 2,000 public Google Play reviews (Sept 2018 – Oct 2026).
2. **Taxonomy & Keyword Classification:** Audited 13-theme classification rules with 100% precision on a 60-review stratified validation sample.
3. **Sampling Bias Decomposition:** Rigorous analysis explaining why pre-2026 reviews reflect Google's "most-relevant" ranking bias rather than historical operational decline.
4. **Actionable FDE Recommendations:** Prioritised technical solutions (P0/P1/P2) designed for a Forward Deployed Engineer, including an **Offline Trip Pass & QR Fallback**, **Driver Heartbeat Telemetry**, **Omnichannel Auth Failover (WhatsApp/IVR)**, and **Geofenced Anti-Ghosting Dwell Checks**.
5. **Full Deliverable Suite:** Complete Markdown and publication-ready PDF reports.

---

## 2. Repository Structure

```text
MoveInSync_CaseStudy/
├── data/
│   ├── app_listing.json                  # Google Play app metadata snapshot (4.64 rating, 114k+ ratings)
│   └── raw_reviews.csv                   # 2,000 unique reviews collected via Google Play API
├── outputs/
│   ├── 01_rating_distribution.png        # Rating distribution chart (1-5 stars)
│   ├── 02_reviews_and_rating_by_year.png # Reviews and mean rating by year across collection passes
│   ├── 03_complaint_themes.png           # Complaint themes ranked by prevalence in 1-2 star reviews
│   ├── 04_themes_newest_vs_most_relevant.png # Comparison of themes across collection passes
│   ├── 05_low_vs_high_themes.png         # Comparison of keyword mentions: Low (1-2★) vs High (4-5★)
│   ├── analysis_summary.txt              # Plaintext analysis summary
│   └── tables/                           # 9 verified CSV tables
│       ├── complaint_theme_examples.csv
│       ├── complaint_themes_low_rated.csv
│       ├── low_vs_high_distinctive_words.csv
│       ├── low_vs_high_metrics.csv
│       ├── low_vs_high_theme_mentions.csv
│       ├── rating_distribution.csv
│       ├── rating_distribution_by_collection_pass.csv
│       ├── reviews_by_year.csv
│       └── theme_validation_sample.csv
├── report/
│   ├── MoveInSync_Case_Study.md          # 13-section comprehensive executive case study report
│   ├── MoveInSync_Case_Study.pdf         # Publication-ready executive PDF report
│   ├── methodology_note.md               # Detailed technical methodology note
│   └── generate_pdf.py                   # ReportLab script to build the PDF report
├── src/
│   ├── analyze_reviews.py                # Main analysis pipeline (cleaning, regex tagging, tables, charts)
│   └── collect_reviews.py                # Google Play review collection script
├── .gitignore                            # Clean Git exclusion rules
├── README.md                             # Repository overview and reproduction guide
├── requirements.txt                      # Exact Python package dependencies
└── SUBMISSION_GUIDE.md                   # Ready-to-paste submission guide for application fields
```

---

## 3. Key Verified Findings

All figures are grounded strictly in the verified dataset:

| Finding | Metric / Evidence | Operational Impact |
| :--- | :--- | :--- |
| **Dataset Volume** | 2,000 reviews (2018-09-21 to 2026-10-09) | Zero scraping duplicates; 100% complete text & ratings. |
| **Bimodal Rating Split** | 1★: 34.8% (695), 2★: 5.2% (105), 5★: 48.3% (966) | 40.0% low-rated (n=800); 55.2% high-rated (n=1,104). |
| **Mean Sample Rating** | **3.29 / 5.00** | Contrast with store total score of **4.64** across 114,874 ratings. |
| **Leading Complaint: Reliability** | **28.2% (n = 226 of low-rated)** | App freezes, white screen on launch, crash during shift rush. |
| **Leading Complaint: Allocation** | **25.5% (n = 204 of low-rated)** | Unassigned cabs before shift; rigid employer cut-off times. |
| **Leading Complaint: Tracking/GPS** | **21.8% (n = 174 of low-rated)** | Frozen map marker; ETA jumping erratically; wrong pickup pin. |
| **Leading Complaint: Delays** | **19.5% (n = 156 of low-rated)** | Cascading pooling delays; drivers departing prematurely. |
| **Leading Complaint: Usability** | **18.2% (n = 146 of low-rated)** | Missing multi-day bulk roster booking; non-editable shifts. |
| **Leading Complaint: Login / OTP**| **15.6% (n = 125 of low-rated)** | Auto-logout curbside; SMS verification carrier delays. |

### Sampling Bias Explanation
The dataset combines **1,400 newest reviews** (avg rating **3.81**) and **600 most-relevant reviews** (avg rating **2.07**). Pre-2026 reviews are drawn entirely from the "most-relevant" pass. Google Play's ranking algorithm prioritizes longer, critical reviews with high user engagement. Therefore, pre-2026 rating drops reflect Google's selection bias, not historical software degradation.

---

## 4. Setup & Reproduction Guide

### Environment Requirements
- Python 3.10 or higher
- PowerShell (Windows) or Bash (macOS/Linux)

### 1. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 2. Run the Analysis Pipeline
To regenerate all 5 charts, 9 summary tables, and `analysis_summary.txt`:
```powershell
python src/analyze_reviews.py
```

### 3. Compile the PDF Report
To compile `report/MoveInSync_Case_Study.pdf`:
```powershell
python report/generate_pdf.py
```

### 4. (Optional) Re-collect Live Reviews
To fetch fresh public reviews directly from Google Play:
```powershell
python src/collect_reviews.py --max-reviews 2000
```

---

## 5. Forward Deployed Engineering Recommendations Summary

1. **[P0] Offline Trip Pass & In-Cab QR Boarding Fallback:** Pre-cache confirmed trips locally in Room DB with 4-hour offline HMAC QR token. Eliminates curbside boarding failures in basement parking lots.
2. **[P0] Driver Telemetry Heartbeat & "Degraded GPS" Warning:** 10s driver ping monitoring; render transparent vehicle pin with stale telemetry warnings if ping stalls >60s. Rebuilds user trust.
3. **[P1] Omnichannel Auth Failover (WhatsApp, Voice IVR & SSO):** Automated failover to WhatsApp Business API after 30s SMS timeout; silent background JWT refresh.
4. **[P1] Proactive Allocation Transparency & FDE Deficit Bot:** User milestone tracking (T-120m, T-45m, T-30m) + automated client deficit alert bot with backup fleet vouchers.
5. **[P1] Anti-Ghosting Geofence Dwell Validation:** Require driver vehicle to dwell within 100m for 5 minutes + completed 30s virtual call bridge before triggering "No-Show".
6. **[P2] Multi-Select Bulk Shift Roster Calendar UX:** 2-tap recurring shift scheduling (e.g. Mon/Wed/Fri) with dynamic cut-off countdown timer clocks.

---

## 6. Deliverables Index

- **Full Executive Report:** [`report/MoveInSync_Case_Study.md`](report/MoveInSync_Case_Study.md)
- **Publication PDF Report:** [`report/MoveInSync_Case_Study.pdf`](report/MoveInSync_Case_Study.pdf)
- **Methodology & Tools Note:** [`report/methodology_note.md`](report/methodology_note.md)
- **Application Submission Guide:** [`SUBMISSION_GUIDE.md`](SUBMISSION_GUIDE.md)

---

