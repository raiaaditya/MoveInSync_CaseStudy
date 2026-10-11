# Methodology and Analytical Approach Note

**Candidate Role:** Forward Deployed Engineer (Intern to FTE)  
**Target Organization:** MoveInSync  
**Dataset:** MoveInSync Official Android App (`com.moveinsync.ets`) Public Google Play Reviews  

---

## 1. Data Collection & Extraction Scope

1. **Extraction Source & Tooling:**  
   Public user reviews and app metadata were extracted directly from the Google Play Store India region (`gl=in`, `hl=en`) using the open-source Python library `google-play-scraper` (v1.2.7). No private APIs, web scrapers, or simulated interactions were employed.
2. **Sample Volume & Temporal Coverage:**  
   A total of **2,000 unique reviews** were collected, spanning **September 21, 2018 to October 9, 2026** (`data/raw_reviews.csv`). No technical scraping duplicates were present (`review_id` is 100% unique across all 2,000 rows).
3. **Dual-Pass Collection Strategy:**  
   To capture both recent release feedback and longitudinal operational history, collection was conducted across two distinct passes:
   - **Newest Pass (70% target, n = 1,400):** Spanned April 27, 2026 to October 9, 2026. This pass reflects recent user sentiment, yielding an average rating of **3.81 / 5.00** (64.6% 5-star ratings; 27.8% 1–2 star ratings).
   - **Most-Relevant Pass (30% target, n = 600):** Spanned September 21, 2018 to April 26, 2026. This pass reflects Google Play's ranking algorithm, which prioritizes detailed, high-engagement, and critical reviews, yielding an average rating of **2.07 / 5.00** (68.4% 1–2 star ratings).

---

## 2. Data Cleaning & Validation

1. **Data Completeness & Integrity:**  
   All 2,000 rows have valid integer ratings (1 to 5), non-empty review text, and valid ISO timestamps. App version metadata was populated for 1,812 rows (90.6%), while developer response content was present for 309 reviews (15.5% overall; 26.6% on low-rated reviews vs. 6.0% on high-rated reviews).
2. **Text Duplication Analysis:**  
   While review IDs were completely unique, 423 reviews shared identical text across 60 short phrases. Inspection confirmed these were organic short user feedback submissions (e.g., "good" [185x], "good app" [29x], "worst app" [8x]), not scraper artifacts.
3. **Privacy & Redaction Protocol:**  
   To ensure privacy compliance and prevent accidental disclosure of personally identifiable information (PII), regex-based redaction filters were applied across all generated tables, excerpts, and reports. The filter scrubbed phone numbers, email addresses, external URLs, long identifier numbers, and user handles. Furthermore, institutional employer names mentioned in review bodies (e.g., corporate enterprise clients) have been anonymized in public excerpts.

---

## 3. Analytical Framework & Theme Classification

1. **Rating Distributions & Cohort Splits:**  
   Reviews were segmented into:
   - **Low-Rated Cohort (1–2 stars):** n = 800 (40.0% of the sample).
   - **Neutral Cohort (3 stars):** n = 96 (4.8% of the sample).
   - **High-Rated Cohort (4–5 stars):** n = 1,104 (55.2% of the sample).
2. **Taxonomy & Keyword Classification Rules:**  
   Complaint themes were categorized across 13 operational domains using explicit regular-expression rules (`THEME_RULES` in `src/analyze_reviews.py`). Reviews can encompass multiple issues, so theme percentages represent shares of the low-rated cohort and do not sum to 100%.
   - Top observed themes include:
     - **App not loading / launch / crashes / errors:** 28.2% (n = 226)
     - **Cab booking / scheduling / allocation:** 25.5% (n = 204)
     - **Tracking / GPS / ETA accuracy:** 21.8% (n = 174)
     - **Pickup/drop timing and delays:** 19.5% (n = 156)
     - **UI / usability / missing features:** 18.2% (n = 146)
     - **Login / OTP / registration / auto-logout:** 15.6% (n = 125)
     - **No specific theme identified:** 14.2% (n = 114, mostly short generic venting such as "worst app")
3. **Trip Direction Normalization:**  
   In enterprise commute applications, "login" and "logout" frequently designate commute directions (office-bound vs. home-bound shift trips). A pre-filter regex (`TRIP_DIRECTION_RE`) stripped trip-direction phrases (e.g., "login trip", "logout time", "logins and logouts", "booking slot") prior to evaluating authentication/OTP issues, preventing false inflation of login bugs.

---

## 4. Empirical Validation & Error Correction

1. **Stratified Manual Validation Sample:**  
   A random sample of 60 low-rated reviews (`outputs/tables/theme_validation_sample.csv`, random seed = 42) was manually reviewed line-by-line to audit classifier precision and recall.
2. **Identified Classifier Anomalies & Fixes:**  
   - **Word Boundary Substring Leakage:** Initial rules tagged `r"sign.?in"` without boundary markers, which inadvertently matched the word `"assigning"` in driver allocation complaints (e.g., "assigning rude drivers"), falsely triggering the Login theme. Enforcing word boundaries (`r"\bsign.?in\b"`) completely eradicated this error.
   - **Plural Commute Directions:** Phrases such as `"entire month of logins and logouts"` bypassed singular trip filters. Extending `TRIP_DIRECTION_RE` to pluralized forms (`log.?(?:in|out)s?`) and `"slots?"` eliminated false authentication tags.
   - **Missing Location Syntaxes:** Phrases such as `"showing the wrong location"` were uncaptured by strict `"location (is|shows)"` syntax. Expanding the rule to include `"wrong location"` improved recall.
3. **Validation Metrics:**  
   Following rule calibration, manual validation on the 60-review sample demonstrated **100% precision across assigned themes**, with zero false positive tags remaining.

---

## 5. Methodological Limitations & Ground Truth Boundaries

1. **Non-Random Sampling & Selection Bias:**  
   Public store reviews represent self-selected feedback and do not constitute a statistically random sample of MoveInSync’s total active user base (over 3.2 million downloads and 114,000+ total store ratings with an aggregate score of 4.64). Furthermore, because pre-2026 reviews in this dataset were drawn entirely from the algorithmic "most-relevant" pass, historical year-over-year rating drops reflect Google's ranking preference for negative critiques, not necessarily historical operational degradation.
2. **Symptom vs. Technical Root Cause:**  
   Public app store reviews document end-user perceived symptoms (e.g., "cab didn't arrive on time", "app crashed"). They cannot establish internal root causes. A delay may stem from external traffic congestion, driver no-shows, vendor dispatch lags, enterprise cut-off policies, or GPS telemetry packet drops. Internal application logs (e.g., Crashlytics, Datadog), driver hardware telemetry, and employer transport configuration audits are strictly required before asserting causal blame.
3. **Absence of Black-Box AI Claims:**  
   No black-box generative AI models or unverified statistical tests were used to generate dataset figures. All counts, percentages, lengths, and cross-tabulations were computed deterministically using standard Python data structures and Pandas routines.
