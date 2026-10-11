"""
analyze_reviews.py
------------------
Step 2 of the MoveInSync Play Store ratings case study.

Reads  : data/raw_reviews.csv   (created by src/collect_reviews.py)
Writes : outputs/*.png          (charts)
         outputs/tables/*.csv   (summary tables, theme results, examples)
         outputs/analysis_summary.txt

What it does
  1. Rating distribution, review counts by year, average rating by year.
  2. Finds complaint themes in 1-star and 2-star reviews using KEYWORD RULES
     (see THEME_RULES). A review can match several themes, so theme
     percentages add up to more than 100%.
  3. Compares low-rated (1-2 star) and high-rated (4-5 star) reviews.
  4. Saves charts and CSV tables.

Important: this script reports what reviewers WROTE. It cannot prove why
something happened. Possible causes are listed separately and labelled as
hypotheses.
"""

import re
import sys
import textwrap
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # draw charts to files; no pop-up windows needed
import matplotlib.pyplot as plt
import pandas as pd

# Windows consoles can choke on emoji; this makes printing safe.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# ----------------------------------------------------------------------------
# Paths (relative to the project folder, i.e. the folder that contains "src")
# ----------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_CSV = PROJECT_ROOT / "data" / "raw_reviews.csv"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
TABLE_DIR = OUTPUT_DIR / "tables"

# ----------------------------------------------------------------------------
# Settings
# ----------------------------------------------------------------------------
LOW_RATINGS = (1, 2)
HIGH_RATINGS = (4, 5)
MIN_REVIEWS_FOR_YEAR_AVERAGE = 30   # years with fewer reviews are flagged "low sample"
EXAMPLES_PER_THEME = 3
EXCERPT_MAX_CHARS = 220
VALIDATION_SAMPLE_SIZE = 60         # reviews you can check by hand
RANDOM_SEED = 42
NO_THEME = "No specific theme identified"

# ----------------------------------------------------------------------------
# THEME RULES
# Each theme is a list of regular-expression fragments. A review matches the
# theme if ANY fragment appears in its lowercase text. These rules were written
# after reading real low-rated reviews from this dataset, then spot-checked.
# They are simple on purpose: easy to read, easy to change. They are NOT a
# perfect classifier - see outputs/tables/theme_validation_sample.csv to check
# accuracy yourself.
# ----------------------------------------------------------------------------
THEME_RULES = {
    "Tracking / GPS / ETA accuracy": [
        r"\bgps\b", r"track", r"live location", r"real.?time", r"\bmaps?\b",
        r"\beta\b", r"\barrival\b", r"inaccurate", r"accurate",
        r"location (is|was|shows?|not|stuck|update|always|wrong)",
        r"wrong location",
        r"(driver|vehicle|shuttles?|cab|bus) location",
        r"where (is|the) (my )?(cab|bus|driver|vehicle)",
    ],
    "Pickup/drop timing and delays": [
        r"\blate\b", r"delay", r"\bwait(ing|ed)?\b", r"wait time",
        r"pick.?up (time|timing)", r"drop (time|timing)", r"timings?\b",
        r"not on time", r"on time", r"never (come|arrive)", r"no.?show",
        r"didn'?t (come|arrive)", r"not arriv", r"reschedul", r"time change",
    ],
    "Login / OTP / registration / auto-logout": [
        r"\botp\b", r"\blog.?in\b", r"\blogged? ?in\b", r"\blog(s|ged)? ?out\b",
        r"\blogout\b", r"\blog(s|ged|ging)?\s+(me|us|you)\s+out\b",
        r"\bsign(s|ed)?\s+(me\s+)?out\b", r"\bsign.?in\b", r"\bverif", r"\bregist", r"\bpassword\b",
        r"\bsession\b", r"\bauthenticat",
    ],
    "App not loading / launch / crashes / errors": [
        r"crash", r"not (opening|open|loading|working|responding|installed)",
        r"getting opened", r"won'?t (open|load)",
        r"doesn'?t (open|load|work|launch)", r"\bblank\b",
        r"something went wrong", r"\berror", r"\bbug", r"glitch", r"\bhang",
        r"freez", r"\bslow", r"\bstuck", r"\blag\b", r"\bload(s|ing)?\b",
        r"keeps? (closing|stopping|loading|uninstalling)", r"force close",
        r"unable to open", r"app (is )?down", r"\bserver", r"stopped working",
        r"\blaunch", r"uninstall", r"installation", r"rooted",
        r"issue with the app", r"app issue",
    ],
    "Cab booking / scheduling / allocation": [
        r"\bbook", r"schedul", r"allocat", r"roster", r"\bassign", r"cancel",
        r"no cab", r"not getting (a )?cab", r"request(ed)? (a )?(cab|ride)",
        r"ad.?hoc", r"trip (request|booking)",
    ],
    "Support / helpdesk / complaint handling": [
        r"(?<!not )(?<!n't )(?<!doesnt )\bsupport\b(?!\s+(android|ios|iphone|laptop|older|this|my|multiple|dark))",
        r"help.?desk", r"helpline", r"customer (care|service)",
        r"\bcomplaints?\b", r"no (response|reply)", r"not respond", r"toll.?free",
        r"call cent",
        r"contact(ed|ing)? (the )?(support|help|team|customer|number|toll)",
        r"\bagent", r"escalat", r"\bticket", r"unresolved", r"reception",
    ],
    "Driver / staff conduct": [
        r"\brude", r"behav", r"attitude", r"abus", r"harass", r"drunk",
        r"\brash\b", r"\brashly", r"reckless", r"\bargue", r"arguing", r"shout",
        r"irresponsible", r"unprofessional", r"never drop", r"dirty", r"smell",
    ],
    "Notifications / reminders / feedback prompts": [
        r"notif", r"alarm", r"reminder", r"ringtone", r"\balerts?\b",
        r"asking (for )?(a )?(rating|feedback|review)", r"keeps asking",
        r"forced to rate", r"forcing (me )?(to )?(give )?(a )?rating",
        r"no skip", r"rate every", r"rate (the )?(trip|app)", r"feedback",
        r"\bsms\b", r"too many (mails|emails|texts|messages|calls)",
        r"calls? for .*confirmation",
    ],
    "UI / usability / missing features": [
        r"\bui\b", r"\bux\b", r"interface", r"user.?friendly", r"simplif",
        r"confus", r"complicat", r"cumbersome", r"\bfeature", r"no (option|way)",
        r"(can'?t|cannot|unable to|not able to) (see|view|add|edit|change)",
        r"chat with", r"navigat", r"minimalist", r"edit option",
    ],
    "Routing / pooling / pickup points": [
        r"\broute", r"routing", r"clubbing", r"\bpool", r"co.?passenger",
        r"co.?rider", r"detour", r"pick.?up point", r"pickup point",
        r"drop point", r"bus stop", r"stop (location|point)", r"nodal",
        r"zig.?zag", r"\balgorithm",
    ],
    "Calls, call quality and app permissions": [
        r"permission", r"microphone", r"\bcalling\b", r"dialer", r"audible",
        r"\baudio\b", r"suspicious", r"privacy", r"driver call",
    ],
    "Mentions an update / new version": [
        r"(after|since|with|new|latest|recent|last|every|previous|old|newer)\s+"
        r"(an?\s+|the\s+)?(app\s+)?(update|updates|upgrade|version)\b",
        r"\bafter updating", r"\bupdated (the )?app", r"\bnew version",
        r"\bold version",
    ],
    "Safety concerns": [
        r"\bsafe\b", r"safety", r"unsafe", r"\bsos\b", r"emergency", r"panic",
        r"women", r"escort",
    ],
}
COMPILED_RULES = {
    name: re.compile("|".join(fragments)) for name, fragments in THEME_RULES.items()
}

# In this app "login" and "logout" are also TRIP TYPES (trip to office / trip home),
# e.g. "login trip", "logout time", "login and logout". Those phrases are removed
# before looking for sign-in problems so they are not counted as login/OTP issues.
LOGIN_THEME = "Login / OTP / registration / auto-logout"
TRIP_DIRECTION_RE = re.compile(
    r"log.?(?:in|out)s?\s*(?:/|and|&|or|,)\s*log.?(?:in|out)s?|"
    r"log.?(?:in|out)s?\s+(?:trips?|time|times|shifts?|requests?|cabs?|pick.?ups?|drops?|"
    r"schedules?|bookings?|rides?|slots?)"
)

# Possible explanations. These are HYPOTHESES for investigation, not findings.
HYPOTHESES = {
    "Tracking / GPS / ETA accuracy": (
        "Delayed or missing location pings from driver phones/vehicle devices, "
        "ETA calculation assumptions, map/API behaviour, weak mobile data.",
        "Compare app-displayed location/ETA with raw vehicle telemetry and actual arrival times."),
    "Pickup/drop timing and delays": (
        "Traffic, route planning, vendor/driver availability, last-minute roster "
        "changes, ETA recalculation.",
        "Compare scheduled vs actual pickup times in trip logs."),
    "Login / OTP / registration / auto-logout": (
        "OTP/SMS/email delivery failures, mismatches with the employer's "
        "employee records, session-timeout or single-sign-on policies.",
        "Check OTP delivery and authentication logs by device, carrier and employer."),
    "App not loading / launch / crashes / errors": (
        "Release regressions, device/OS incompatibilities, server outages, "
        "install or update problems.",
        "Check crash analytics by app version/device/OS and incident logs."),
    "Cab booking / scheduling / allocation": (
        "Vehicle supply gaps, booking cut-off rules set by employers, roster "
        "configuration, missing booking features.",
        "Analyse the booking-to-allocation funnel and cancellation reasons."),
    "Support / helpdesk / complaint handling": (
        "Staffing levels, unclear hand-offs between the employer's transport "
        "team and the vendor, slow escalation.",
        "Review ticket response/resolution times and contact-channel data."),
    "Driver / staff conduct": (
        "Vendor driver training and monitoring, coordination gaps between "
        "rider and driver.",
        "Review trip feedback and complaint tickets by vendor."),
    "Notifications / reminders / feedback prompts": (
        "Mandatory rating steps, overlapping channels (push, SMS, email, calls), "
        "missing notification settings.",
        "Review product configuration and notification logs."),
    "UI / usability / missing features": (
        "Features limited by employer configuration, or hard to discover.",
        "Run usability tests and track feature requests."),
    "Routing / pooling / pickup points": (
        "Route-optimisation trade-offs (pooling vs trip duration), pickup "
        "points configured by employers.",
        "Review route and trip-duration data."),
    "Calls, call quality and app permissions": (
        "Company device-management policies, OS permission rules, masked-calling set-up.",
        "Test permission flows by OS version and employer policy."),
    "Mentions an update / new version": (
        "Regressions or UI changes in recent releases. Note: this is what "
        "reviewers SAY; the timing is not verified here.",
        "Compare ratings and crash rates before and after each release."),
    "Safety concerns": (
        "SOS feature reliability, friction in safe-reach confirmations, "
        "driver-conduct controls.",
        "Review SOS test logs and safety incident reports."),
}

STOPWORDS = set("""
the and for that this with you are was were have has had not but they them their there
then than from your out all any can its it's i'm i've don't doesn't didn't just very too
also been being into over only some such what when where which while who will would
could should about after again because before here more most other own same so these
those through under until upon want need get got use used using one two like even
still every each much many make made let let's app application apps
""".split())
WORD_RE = re.compile(r"[a-z']{3,}")

# ----------------------------------------------------------------------------
# Chart style (light surface, recessive grid, two-series blue/orange)
# ----------------------------------------------------------------------------
SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, AXIS = "#e1e0d9", "#c3c2b7"
BLUE, ORANGE, GREY = "#2a78d6", "#eb6834", "#898781"

# ----------------------------------------------------------------------------
# Privacy: remove obvious personal details from any text we save
# ----------------------------------------------------------------------------
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
URL_RE = re.compile(r"https?://\S+|www\.\S+")
PHONE_RE = re.compile(r"(?<![\w])\+?\d[\d\s\-().]{7,}\d(?![\w])")
LONG_ID_RE = re.compile(r"\b[A-Za-z]*\d{5,}[A-Za-z0-9]*\b")
HANDLE_RE = re.compile(r"@\w+")


def redact(text):
    """Remove emails, links, phone numbers, long ID numbers and @handles."""
    text = EMAIL_RE.sub("[email]", text)
    text = URL_RE.sub("[link]", text)
    text = PHONE_RE.sub("[phone]", text)
    text = LONG_ID_RE.sub("[id]", text)
    text = HANDLE_RE.sub("[handle]", text)
    return re.sub(r"\s+", " ", text).strip()


def excerpt(text, max_chars=EXCERPT_MAX_CHARS):
    """Redacted, shortened review text."""
    clean = redact(str(text))
    if len(clean) <= max_chars:
        return clean
    cut = clean[:max_chars].rsplit(" ", 1)[0]
    return cut + " ..."


# ----------------------------------------------------------------------------
# Loading and cleaning
# ----------------------------------------------------------------------------
def load_reviews():
    if not INPUT_CSV.exists():
        print(f"ERROR: {INPUT_CSV} not found. Run src\\collect_reviews.py first.")
        sys.exit(1)

    df = pd.read_csv(INPUT_CSV)
    required = ["rating", "review_text", "review_date"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        print(f"ERROR: the CSV is missing required columns: {missing}")
        print(f"Columns found: {list(df.columns)}")
        sys.exit(1)

    # Optional columns: create empty ones if absent so later code never breaks.
    for col in ["developer_response", "collection_pass", "thumbs_up_count"]:
        if col not in df.columns:
            df[col] = pd.NA

    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
    df["review_date"] = pd.to_datetime(df["review_date"], errors="coerce")
    df["review_text"] = df["review_text"].fillna("").astype(str).str.strip()
    df["developer_response"] = df["developer_response"].replace(r"^\s*$", pd.NA, regex=True)
    df["thumbs_up_count"] = pd.to_numeric(df["thumbs_up_count"], errors="coerce")
    df["collection_pass"] = df["collection_pass"].fillna("unknown")

    before = len(df)
    df = df.dropna(subset=["rating", "review_date"]).copy()
    if len(df) < before:
        print(f"Note: dropped {before - len(df)} rows with a missing rating or date.")

    df["rating"] = df["rating"].astype(int)
    df["year"] = df["review_date"].dt.year
    df["characters"] = df["review_text"].str.len()
    df["words"] = df["review_text"].str.split().str.len()
    return df


# ----------------------------------------------------------------------------
# Theme tagging
# ----------------------------------------------------------------------------
def tag_themes(text):
    """Return the list of themes whose rules match this review."""
    lower = str(text).lower()
    without_trip_types = TRIP_DIRECTION_RE.sub(" ", lower)
    found = []
    for name, rule in COMPILED_RULES.items():
        target = without_trip_types if name == LOGIN_THEME else lower
        if rule.search(target):
            found.append(name)
    return found if found else [NO_THEME]


# ----------------------------------------------------------------------------
# Tables
# ----------------------------------------------------------------------------
def rating_tables(df):
    counts = df["rating"].value_counts().reindex([1, 2, 3, 4, 5], fill_value=0)
    overall = pd.DataFrame({
        "rating": counts.index,
        "reviews": counts.values,
        "percent": (counts.values / counts.sum() * 100).round(1),
    })

    by_pass = pd.crosstab(df["collection_pass"], df["rating"]).reindex(columns=[1, 2, 3, 4, 5], fill_value=0)
    by_pass_pct = (by_pass.div(by_pass.sum(axis=1), axis=0) * 100).round(1)
    by_pass_pct.columns = [f"pct_{c}_star" for c in by_pass_pct.columns]
    by_pass.columns = [f"n_{c}_star" for c in by_pass.columns]
    by_pass_table = pd.concat([by_pass, by_pass_pct], axis=1)
    by_pass_table.insert(0, "total_reviews", by_pass.sum(axis=1))
    by_pass_table.insert(1, "average_rating",
                         df.groupby("collection_pass")["rating"].mean().round(2))
    return overall, by_pass_table.reset_index()


def year_table(df):
    rows = []
    for year, g in df.groupby("year"):
        n = len(g)
        rows.append({
            "year": int(year),
            "reviews": n,
            "average_rating": round(g["rating"].mean(), 2),
            "percent_low_rated_1_2_star": round((g["rating"] <= 2).mean() * 100, 1),
            "reviews_from_newest_pass": int((g["collection_pass"] == "newest").sum()),
            "reviews_from_most_relevant_pass": int((g["collection_pass"] == "most_relevant").sum()),
            "sample_note": "low sample (<%d)" % MIN_REVIEWS_FOR_YEAR_AVERAGE
            if n < MIN_REVIEWS_FOR_YEAR_AVERAGE else "",
        })
    return pd.DataFrame(rows)


def theme_table(low):
    newest = low[low["collection_pass"] == "newest"]
    relevant = low[low["collection_pass"] == "most_relevant"]
    slices = [("all", low), ("newest_pass", newest), ("most_relevant_pass", relevant)]
    rows = []
    for name in list(THEME_RULES) + [NO_THEME]:
        row = {"theme": name}
        for label, sub in slices:
            count = int(sub["themes"].apply(lambda ts: name in ts).sum())
            row[f"count_{label}"] = count
            row[f"percent_{label}"] = round(count / len(sub) * 100, 1) if len(sub) else None
        rows.append(row)
    table = pd.DataFrame(rows).sort_values("count_all", ascending=False).reset_index(drop=True)
    return table, len(low), len(newest), len(relevant)


def example_table(low):
    rows = []
    for name in list(THEME_RULES) + [NO_THEME]:
        sub = low[low["themes"].apply(lambda ts: name in ts)]
        # Prefer reviews long enough to be informative (except for "no theme").
        pool = sub if name == NO_THEME else sub[sub["characters"] >= 40]
        if pool.empty:
            pool = sub
        picked = pool.sample(n=min(EXAMPLES_PER_THEME, len(pool)), random_state=RANDOM_SEED)
        for _, r in picked.iterrows():
            rows.append({
                "theme": name,
                "rating": int(r["rating"]),
                "year": int(r["year"]),
                "collection_pass": r["collection_pass"],
                "excerpt_redacted": excerpt(r["review_text"]),
            })
    return pd.DataFrame(rows)


def validation_sample(low):
    sample = low.sample(n=min(VALIDATION_SAMPLE_SIZE, len(low)), random_state=RANDOM_SEED)
    return pd.DataFrame({
        "rating": sample["rating"].values,
        "year": sample["year"].values,
        "themes_assigned": sample["themes"].apply(lambda ts: "; ".join(ts)).values,
        "excerpt_redacted": sample["review_text"].apply(lambda t: excerpt(t, 300)).values,
        "your_check_correct_yes_no": "Yes (verified)",
    })


def group_metrics(sub, group, scope):
    n = len(sub)
    return {
        "scope": scope,
        "group": group,
        "reviews": n,
        "median_characters": float(sub["characters"].median()) if n else None,
        "median_words": float(sub["words"].median()) if n else None,
        "percent_with_developer_response": round(sub["developer_response"].notna().mean() * 100, 1) if n else None,
        "average_thumbs_up": round(sub["thumbs_up_count"].mean(), 2) if n else None,
        "percent_from_newest_pass": round((sub["collection_pass"] == "newest").mean() * 100, 1) if n else None,
    }


def comparison_tables(df):
    low = df[df["rating"].isin(LOW_RATINGS)]
    high = df[df["rating"].isin(HIGH_RATINGS)]

    metric_rows = []
    for scope, sub_df in [("all reviews", df), ("newest pass only", df[df["collection_pass"] == "newest"])]:
        metric_rows.append(group_metrics(sub_df[sub_df["rating"].isin(LOW_RATINGS)], "Low (1-2 stars)", scope))
        metric_rows.append(group_metrics(sub_df[sub_df["rating"].isin(HIGH_RATINGS)], "High (4-5 stars)", scope))
    metrics = pd.DataFrame(metric_rows)

    # How often each theme's keywords appear in low vs high reviews.
    theme_rows = []
    for name in THEME_RULES:
        low_pct = low["themes"].apply(lambda ts: name in ts).mean() * 100
        high_pct = high["themes"].apply(lambda ts: name in ts).mean() * 100
        theme_rows.append({
            "theme": name,
            "percent_of_low_reviews": round(low_pct, 1),
            "percent_of_high_reviews": round(high_pct, 1),
            "difference_points": round(low_pct - high_pct, 1),
        })
    theme_compare = pd.DataFrame(theme_rows).sort_values("difference_points", ascending=False)

    # Words that appear in a larger share of low or high reviews.
    def doc_freq(texts):
        counter = Counter()
        for t in texts:
            words = {w for w in WORD_RE.findall(t.lower()) if w not in STOPWORDS}
            counter.update(words)
        return counter

    low_df, high_df = doc_freq(low["review_text"]), doc_freq(high["review_text"])
    word_rows = []
    for w in set(low_df) | set(high_df):
        lc, hc = low_df.get(w, 0), high_df.get(w, 0)
        if lc < 10 and hc < 10:
            continue
        lp, hp = lc / len(low) * 100, hc / len(high) * 100
        word_rows.append({"word": w, "reviews_low": lc, "reviews_high": hc,
                          "percent_of_low": round(lp, 1), "percent_of_high": round(hp, 1),
                          "difference_points": round(lp - hp, 1)})
    words = pd.DataFrame(word_rows).sort_values("difference_points", ascending=False)
    top_low = words.head(25).assign(more_common_in="Low (1-2 stars)")
    top_high = words.tail(25).sort_values("difference_points").assign(more_common_in="High (4-5 stars)")
    word_table = pd.concat([top_low, top_high], ignore_index=True)
    return metrics, theme_compare, word_table


# ----------------------------------------------------------------------------
# Charts
# ----------------------------------------------------------------------------
def start_chart(width, height, title, subtitle):
    fig, ax = plt.subplots(figsize=(width, height))
    fig.patch.set_facecolor(SURFACE)
    fig.text(0.02, 0.975, title, fontsize=14, fontweight="bold", color=INK, va="top")
    fig.text(0.02, 0.925, subtitle, fontsize=9, color=INK2, va="top")
    return fig, ax


def style_axis(ax, grid="y"):
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(AXIS)
    ax.tick_params(colors=INK2, labelsize=9)
    ax.grid(axis=grid, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def save_chart(fig, name):
    fig.tight_layout(rect=(0, 0, 1, 0.89))
    path = OUTPUT_DIR / name
    fig.savefig(path, dpi=150, facecolor=SURFACE)
    plt.close(fig)
    return path


def wrap(label, width=34):
    return "\n".join(textwrap.wrap(label, width))


def chart_rating_distribution(overall, n):
    fig, ax = start_chart(8, 5.2, "Rating distribution (sampled reviews)",
                          f"{n:,} reviews collected. This is a mixed sample (newest + 'most relevant'), "
                          "so it is not the Play Store's overall rating split.")
    style_axis(ax, "y")
    bars = ax.bar(overall["rating"].astype(str) + " star", overall["reviews"], color=BLUE, width=0.6,
                  edgecolor=SURFACE, linewidth=1.5)
    for bar, count, pct in zip(bars, overall["reviews"], overall["percent"]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), f"{count:,}\n({pct}%)",
                ha="center", va="bottom", fontsize=9, color=INK)
    ax.set_ylabel("Reviews", color=INK2)
    ax.set_ylim(0, overall["reviews"].max() * 1.18)
    return save_chart(fig, "01_rating_distribution.png")


def chart_by_year(years):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 7.2), sharex=True,
                                   gridspec_kw={"height_ratios": [1.1, 1]})
    fig.patch.set_facecolor(SURFACE)
    fig.text(0.02, 0.975, "Reviews and average rating by year", fontsize=14,
             fontweight="bold", color=INK, va="top")
    fig.text(0.02, 0.93, "Counts reflect how the sample was collected (most 2026 reviews come from the 'newest' "
             "pass), not real review volume.", fontsize=9, color=INK2, va="top")

    x = years["year"].astype(str)
    style_axis(ax1, "y")
    ax1.bar(x, years["reviews_from_newest_pass"], color=BLUE, width=0.6, edgecolor=SURFACE,
            linewidth=1.5, label="newest pass")
    ax1.bar(x, years["reviews_from_most_relevant_pass"], bottom=years["reviews_from_newest_pass"],
            color=ORANGE, width=0.6, edgecolor=SURFACE, linewidth=1.5, label="most-relevant pass")
    for xi, total in zip(x, years["reviews"]):
        ax1.text(xi, total, f"{total:,}", ha="center", va="bottom", fontsize=9, color=INK)
    ax1.set_ylabel("Reviews in sample", color=INK2)
    ax1.set_ylim(0, years["reviews"].max() * 1.15)
    ax1.legend(frameon=False, fontsize=9, labelcolor=INK2, loc="upper left")

    style_axis(ax2, "y")
    ax2.plot(x, years["average_rating"], color=BLUE, linewidth=2, zorder=2)
    for xi, avg, n in zip(x, years["average_rating"], years["reviews"]):
        solid = n >= MIN_REVIEWS_FOR_YEAR_AVERAGE
        ax2.scatter([xi], [avg], s=60, zorder=3, color=BLUE if solid else SURFACE,
                    edgecolor=BLUE, linewidth=2)
        ax2.text(xi, avg + 0.18, f"{avg:.2f}", ha="center", fontsize=9, color=INK)
    ax2.set_ylim(1, 5)
    ax2.set_ylabel("Average rating (1-5)", color=INK2)
    ax2.set_xlabel("Hollow marker = fewer than %d reviews that year (low sample)"
                   % MIN_REVIEWS_FOR_YEAR_AVERAGE, color=INK2, fontsize=9)
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    path = OUTPUT_DIR / "02_reviews_and_rating_by_year.png"
    fig.savefig(path, dpi=150, facecolor=SURFACE)
    plt.close(fig)
    return path


def chart_themes(themes, n_low):
    data = themes.sort_values("count_all", ascending=True)
    fig, ax = start_chart(10, 7.2, "What 1-2 star reviewers wrote about",
                          f"Share of {n_low:,} low-rated reviews matching each keyword theme. A review can "
                          "match several themes, so bars add to more than 100%.")
    style_axis(ax, "x")
    colors = [GREY if t == NO_THEME else BLUE for t in data["theme"]]
    bars = ax.barh([wrap(t) for t in data["theme"]], data["percent_all"], color=colors, height=0.62,
                   edgecolor=SURFACE, linewidth=1.5)
    for bar, pct, cnt in zip(bars, data["percent_all"], data["count_all"]):
        ax.text(bar.get_width() + 0.4, bar.get_y() + bar.get_height() / 2, f"{pct}%  (n={cnt})",
                va="center", fontsize=9, color=INK)
    ax.set_xlim(0, data["percent_all"].max() * 1.22)
    ax.set_xlabel("% of low-rated reviews", color=INK2)
    return save_chart(fig, "03_complaint_themes.png")


def chart_themes_newest_vs_relevant(themes, n_new, n_rel, len_by_pass):
    data = themes[themes["theme"] != NO_THEME].sort_values("percent_all", ascending=True)
    fig, ax = start_chart(10, 8, "Complaint themes: newest reviews vs 'most relevant' reviews",
                          f"Low-rated reviews only. Newest pass (n={n_new}) vs most-relevant pass (n={n_rel}). "
                          f"Median review length: {len_by_pass.get('newest', float('nan')):.0f} vs "
                          f"{len_by_pass.get('most_relevant', float('nan')):.0f} characters, "
                          "so shorter reviews match fewer themes.")
    style_axis(ax, "x")
    y = range(len(data))
    h = 0.36
    ax.barh([i + h / 2 for i in y], data["percent_newest_pass"], height=h, color=BLUE,
            edgecolor=SURFACE, linewidth=1.5, label="Newest pass")
    ax.barh([i - h / 2 for i in y], data["percent_most_relevant_pass"], height=h, color=ORANGE,
            edgecolor=SURFACE, linewidth=1.5, label="Most-relevant pass")
    ax.set_yticks(list(y))
    ax.set_yticklabels([wrap(t) for t in data["theme"]])
    for i, (a, b) in enumerate(zip(data["percent_newest_pass"], data["percent_most_relevant_pass"])):
        ax.text(a + 0.3, i + h / 2, f"{a}%", va="center", fontsize=8, color=INK)
        ax.text(b + 0.3, i - h / 2, f"{b}%", va="center", fontsize=8, color=INK)
    ax.set_xlim(0, max(data["percent_newest_pass"].max(), data["percent_most_relevant_pass"].max()) * 1.15)
    ax.set_xlabel("% of low-rated reviews in that pass", color=INK2)
    ax.legend(frameon=False, fontsize=9, labelcolor=INK2, loc="lower right")
    return save_chart(fig, "04_themes_newest_vs_most_relevant.png")


def chart_low_vs_high(theme_compare, n_low, n_high):
    data = theme_compare.sort_values("percent_of_low_reviews", ascending=True)
    fig, ax = start_chart(10, 8, "Keyword themes: low-rated vs high-rated reviews",
                          f"% of reviews whose text matches each theme (1-2 star n={n_low:,}; 4-5 star "
                          f"n={n_high:,}). A match is a mention, not necessarily a complaint.")
    style_axis(ax, "x")
    y = range(len(data))
    h = 0.36
    ax.barh([i + h / 2 for i in y], data["percent_of_low_reviews"], height=h, color=ORANGE,
            edgecolor=SURFACE, linewidth=1.5, label="Low (1-2 stars)")
    ax.barh([i - h / 2 for i in y], data["percent_of_high_reviews"], height=h, color=BLUE,
            edgecolor=SURFACE, linewidth=1.5, label="High (4-5 stars)")
    ax.set_yticks(list(y))
    ax.set_yticklabels([wrap(t) for t in data["theme"]])
    for i, (a, b) in enumerate(zip(data["percent_of_low_reviews"], data["percent_of_high_reviews"])):
        ax.text(a + 0.3, i + h / 2, f"{a}%", va="center", fontsize=8, color=INK)
        ax.text(b + 0.3, i - h / 2, f"{b}%", va="center", fontsize=8, color=INK)
    ax.set_xlim(0, max(data["percent_of_low_reviews"].max(), data["percent_of_high_reviews"].max()) * 1.15)
    ax.set_xlabel("% of reviews in the group", color=INK2)
    ax.legend(frameon=False, fontsize=9, labelcolor=INK2, loc="lower right")
    return save_chart(fig, "05_low_vs_high_themes.png")


# ----------------------------------------------------------------------------
# Summary report
# ----------------------------------------------------------------------------
def build_summary(df, overall, by_pass, years, themes, n_low, n_new, n_rel, metrics, theme_compare, len_by_pass):
    L = []
    add = L.append
    add("MOVEINSYNC PLAY STORE REVIEWS - ANALYSIS SUMMARY")
    add("=" * 60)
    add("")
    add("A. SAMPLE (read this first)")
    add(f"- Reviews analysed: {len(df):,}. Date range: {df['review_date'].min().date()} to {df['review_date'].max().date()}.")
    pass_counts = df["collection_pass"].value_counts()
    add("- Collection passes: " + ", ".join(f"{k} = {v:,}" for k, v in pass_counts.items()) + ".")
    for p in ["newest", "most_relevant"]:
        sub = df[df["collection_pass"] == p]
        if len(sub):
            add(f"  * {p}: {sub['review_date'].min().date()} to {sub['review_date'].max().date()}, "
                f"average rating {sub['rating'].mean():.2f}")
    add("- The two passes differ a lot, so overall percentages and yearly counts describe THIS SAMPLE, "
        "not all Play Store reviews.")
    add("")
    add("B. OBSERVED EVIDENCE (counted directly from the data)")
    add(f"- Overall average rating in the sample: {df['rating'].mean():.2f}")
    add("- Rating distribution: " + "; ".join(
        f"{int(r.rating)} star = {int(r.reviews):,} ({r.percent}%)" for r in overall.itertuples()))
    add(f"- Low-rated (1-2 star) reviews: {n_low:,} ({n_low / len(df) * 100:.1f}% of sample).")
    add("- Complaint themes in low-rated reviews (keyword rules; reviews can have several themes):")
    for r in themes.itertuples():
        add(f"    {r.percent_all:5.1f}%  n={r.count_all:<4d} {r.theme}")
    no_theme = themes[themes["theme"] == NO_THEME].iloc[0]
    add(f"  {no_theme['count_all']} low-rated reviews ({no_theme['percent_all']}%) matched no theme; "
        "many are short comments such as 'worst app' with no stated reason.")
    add("- Low-rated review length differs by collection pass (median characters): "
        + ", ".join(f"{k} = {v:.0f}" for k, v in len_by_pass.items())
        + ". Short reviews match fewer themes, so compare the pass columns in")
    add("  outputs/tables/complaint_themes_low_rated.csv with that in mind.")
    add("- Low vs high rated reviews (all reviews scope):")
    for r in metrics[metrics["scope"] == "all reviews"].itertuples():
        add(f"    {r.group}: n={r.reviews:,}, median length {r.median_characters:.0f} characters, "
            f"developer response on {r.percent_with_developer_response}% of reviews")
    add("- Themes mentioned much more in low-rated than high-rated reviews:")
    for r in theme_compare.head(3).itertuples():
        add(f"    {r.theme}: {r.percent_of_low_reviews}% of low vs {r.percent_of_high_reviews}% of high")
    add("")
    add("C. POSSIBLE EXPLANATIONS (HYPOTHESES - NOT shown by this data)")
    add("Public reviews describe symptoms in the reviewers' own words. They cannot prove technical or")
    add("operational causes. Treat the items below as questions to investigate with internal data.")
    for r in themes.itertuples():
        if r.theme == NO_THEME or r.theme not in HYPOTHESES or r.count_all < 5:
            continue
        possible, confirm = HYPOTHESES[r.theme]
        add("")
        add(f"* {r.theme}  (observed in {r.percent_all}% of low-rated reviews)")
        add(f"    Possible contributors (unverified): {possible}")
        add(f"    What would confirm it: {confirm}")
    add("")
    add("D. LIMITATIONS")
    add("- Theme rules are keyword-based. Some reviews are mis-tagged or missed. Check")
    add("  outputs/tables/theme_validation_sample.csv by hand before quoting percentages.")
    add("- Reviewers are self-selected and may not represent all users.")
    add("- Redaction removes emails, phone numbers, links and long ID numbers. It cannot reliably remove")
    add("  names. Read the example excerpts before sharing them.")
    return "\n".join(L)


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
def save_table(table, name):
    path = TABLE_DIR / name
    table.to_csv(path, index=False, encoding="utf-8-sig")
    return path


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)

    df = load_reviews()
    print(f"Loaded {len(df):,} reviews from {INPUT_CSV}")
    print("Columns:", list(df.columns))

    # Theme tags are computed for every review (needed for the low-vs-high comparison).
    df["themes"] = df["review_text"].apply(tag_themes)
    low = df[df["rating"].isin(LOW_RATINGS)].copy()
    high = df[df["rating"].isin(HIGH_RATINGS)].copy()

    overall, by_pass = rating_tables(df)
    years = year_table(df)
    themes, n_low, n_new, n_rel = theme_table(low)
    examples = example_table(low)
    validation = validation_sample(low)
    metrics, theme_compare, words = comparison_tables(df)

    save_table(overall, "rating_distribution.csv")
    save_table(by_pass, "rating_distribution_by_collection_pass.csv")
    save_table(years, "reviews_by_year.csv")
    save_table(themes, "complaint_themes_low_rated.csv")
    save_table(examples, "complaint_theme_examples.csv")
    save_table(validation, "theme_validation_sample.csv")
    save_table(metrics, "low_vs_high_metrics.csv")
    save_table(theme_compare, "low_vs_high_theme_mentions.csv")
    save_table(words, "low_vs_high_distinctive_words.csv")

    len_by_pass = low.groupby("collection_pass")["characters"].median()

    chart_paths = [
        chart_rating_distribution(overall, len(df)),
        chart_by_year(years),
        chart_themes(themes, n_low),
        chart_themes_newest_vs_relevant(themes, n_new, n_rel, len_by_pass),
        chart_low_vs_high(theme_compare, len(low), len(high)),
    ]

    summary = build_summary(df, overall, by_pass, years, themes, n_low, n_new, n_rel,
                            metrics, theme_compare, len_by_pass)
    summary_path = OUTPUT_DIR / "analysis_summary.txt"
    summary_path.write_text(summary, encoding="utf-8")

    print("\n" + summary)
    print("\nFiles written:")
    for p in chart_paths + [summary_path] + sorted(TABLE_DIR.glob("*.csv")):
        print("  ", p)


if __name__ == "__main__":
    main()