import os
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ────────────────────────────────────────────────────────────
# RESUME PROFILE
# ────────────────────────────────────────────────────────────
PROFILE_PATH = Path("resume_profile.json")


def load_profile() -> dict:
    if not PROFILE_PATH.exists():
        raise SystemExit(
            "❌ resume_profile.json not found. "
            "Run `python parse_resume.py` first, or run via run_all.py."
        )
    return json.loads(PROFILE_PATH.read_text(encoding="utf-8"))


PROFILE = load_profile()

# ────────────────────────────────────────────────────────────
# LOCAL KENYA TARGETING
# ────────────────────────────────────────────────────────────
LOCAL_COUNTRY = "Kenya"
LOCAL_REGION  = "Nairobi"

LOCAL_TARGETS = [
    "kenya", "nairobi", "mombasa", "kisumu", "nakuru", "eldoret",
    "thika", "kitale", "malindi", "nyeri", "ruiru", "karen",
    "westlands", "kilimani", "industrial area", "kiambu",
    "machakos", "embu", "meru", "kakamega",
]

REMOTE_BLACKLIST = [
    "remote", "worldwide", "anywhere", "global", "emea",
    "work from home", "wfh", "virtual", "distributed", "telecommute",
]

# ────────────────────────────────────────────────────────────
# SEARCH TERMS
# ────────────────────────────────────────────────────────────
SEARCH_TERMS = [
    "full stack developer", "fullstack developer",
    "software developer", "python developer",
    "backend developer", "django developer",
    "laravel developer", "web developer",
    "automation developer", "scraping developer",
    "javascript developer", "react developer",
    "data analyst", "business intelligence",
]

# ────────────────────────────────────────────────────────────
# SKILLS
# ────────────────────────────────────────────────────────────
STRONG_SKILLS = [
    "python", "django", "flask", "fastapi", "laravel", "php",
    "javascript", "react", "node", "automation", "scraping",
    "selenium", "beautifulsoup", "playwright", "scrapy",
    "power bi", "tableau", "looker",
]

MEDIUM_SKILLS = [
    "sql", "mysql", "postgresql", "sqlite", "docker",
    "ci/cd", "git", "github", "api", "rest", "mql5",
    "excel", "etl", "dashboard",
]

MUST_INCLUDE_ANY = STRONG_SKILLS + MEDIUM_SKILLS

# ────────────────────────────────────────────────────────────
# TITLE BLACKLIST
# ────────────────────────────────────────────────────────────
TITLE_BLACKLIST = [
    "writer", "copywriter", "content writer", "editor",
    "proofreader", "translator", "office assistant",
    "virtual assistant", "executive assistant",
    "administrative assistant", "personal assistant",
    "sales", "inside sales", "account executive",
    "business development", "recruiter", "talent acquisition",
    "hr ", "human resources", "data entry",
    "customer support", "customer service", "call center",
    "customer success", "marketing manager", "seo specialist",
    "social media manager", "product manager", "project manager",
    "scrum master", "designer", "ux ", "ui ", "graphic design",
    "accountant", "bookkeeper", "finance", "data scientist",
    "machine learning", "ml engineer", "site reliability",
    "qa engineer", "quality assurance", "test engineer",
    "mobile developer", "ios developer", "android developer",
    "intern", "internship", "junior", "entry level",
    "graduate", "trainee", "embedded", "firmware", "qa ",
]

COMPANY_BLACKLIST = ["lemon.io", "lemon io", "lemonio"]

URL_BLACKLIST = ["lemon.io", "remoteok.com", "remoteok.io"]

# ────────────────────────────────────────────────────────────
# LOCATION — Kenyan local only
# ────────────────────────────────────────────────────────────
LOCATIONS_OK = LOCAL_TARGETS

# ────────────────────────────────────────────────────────────
# HARD REJECT
# ────────────────────────────────────────────────────────────
HARD_REJECT = [
    "unpaid", "commission only", "volunteer", "equity only",
    "phd required", "phd is required",
    "us citizens only", "us citizen only",
    "must be located in the us", "security clearance",
    "top secret", "remote only", "fully remote",
    "work from anywhere",
]

NICE_TO_HAVE = [
    "flexible hours", "flexible schedule", "contract",
    "contractor", "freelance", "equity", "async",
    "4-day week", "four day week", "hybrid",
]

# ────────────────────────────────────────────────────────────
# SCORING
# ────────────────────────────────────────────────────────────
STRONG_SKILL_WEIGHT = 15
MEDIUM_SKILL_WEIGHT = 3
TITLE_MATCH_WEIGHT  = 25
LOCATION_WEIGHT     = 15
SALARY_WEIGHT       = 15
FRESH_WEIGHT        = 10
RECENT_WEIGHT       = 5
EMAIL_WEIGHT        = 5

QUALIFY_THRESHOLD = 45
TOP_N_LETTERS     = 30

MIN_SALARY_USD = 300

MY_YEARS = PROFILE["years"]

REPORT_TO = os.getenv("REPORT_TO", "abelshikanda3@gmail.com")

# ────────────────────────────────────────────────────────────
# LLM — BI recommendations
# ────────────────────────────────────────────────────────────
USE_LLM_BI      = True
USE_LLM_LETTERS = False

ANTHROPIC_API_KEY  = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_BASE_URL = os.getenv("ANTHROPIC_BASE_URL")
LLM_MODEL          = "claude-sonnet-4-5"
BI_MODEL           = "claude-sonnet-4-5"

# ────────────────────────────────────────────────────────────
# STORAGE / BROWSER
# ────────────────────────────────────────────────────────────
DB_PATH        = "jobs.db"
LETTERS_DIR    = Path("letters")
HEADLESS       = True
NAV_TIMEOUT_MS = 30_000

# ────────────────────────────────────────────────────────────
# SERPER — local Kenyan search
# ────────────────────────────────────────────────────────────
SERPER_ENABLED   = True
SERPER_MAX_TERMS = 5
SERPER_LOCATION  = "Nairobi, Kenya"

SERPER_URL_BLACKLIST = [
    "/blog/", "/news/", "/article/", "/guide/", "/how-to/",
    "/salary/", "/resume/", "/cover-letter/",
    "reddit.com/r/", "quora.com", "medium.com",
    "indeed.com/q-", "glassdoor.com/Job/", "ziprecruiter.com/c/",
    "remoteok.com", "weworkremotely.com",
]

SERPER_URL_WHITELIST = [
    "brightermonday.co.ke", "fuzu.com", "myjobmag.co.ke",
    "careers.ke", "jobs.", "careers.", "/careers/", "/jobs/",
    "linkedin.com/jobs/view/",
]

SERPER_TITLE_BLACKLIST = [
    "jobs in", "job openings", "how to", "guide to",
    "best remote", "top remote", "flexible remote",
    "salary", "resume", "cover letter", "interview questions",
    "reddit", "quora", "what is", "everything you",
    "10000+", "1000+", "50+ ", "10+ ",
    "opening", "search results", "browse",
    "remote python developer jobs", "developer jobs",
]

# ────────────────────────────────────────────────────────────
# BRIGHT DATA
# ────────────────────────────────────────────────────────────
BRIGHTDATA_ENABLED    = True
BRIGHTDATA_API_KEY    = os.getenv("BRIGHTDATA_API_KEY")
BRIGHTDATA_DATASET_ID = os.getenv("BRIGHTDATA_DATASET_ID")
BRIGHTDATA_MAX_TERMS  = 25
BRIGHTDATA_LOCATION   = "Nairobi, Kenya"
BRIGHTDATA_RADIUS_KM  = 20

ORG_CATEGORIES = [
    # Tier 1 — retail / FMCG
    "supermarket",
    "grocery store",
    "convenience store",
    "wholesale store",
    "distributor",

    # Tier 1 — pharmacy & health
    "pharmacy",
    "medical supply store",
    "diagnostic center",
    "dental clinic",
    "optician",

    # Tier 1 — logistics
    "logistics service",
    "courier service",
    "freight forwarder",
    "clearing agent",
    "warehouse",
    "delivery service",

    # Tier 1 — fuel & energy
    "petrol station",
    "gas station",
    "solar energy company",
    "water supplier",

    # Tier 2 — auto
    "garage",
    "car repair",
    "car wash",
    "auto parts store",
    "tire shop",
    "motorcycle repair",

    # Tier 2 — hospitality
    "restaurant",
    "cafe",
    "bakery",
    "butcher shop",
    "hotel",
    "catering service",
    "bar",

    # Tier 2 — manufacturing
    "manufacturer",
    "food processing company",
    "packaging company",
    "printing press",
    "furniture store",
    "metal fabricator",

    # Tier 2 — agribusiness
    "agrovet",
    "farm supply store",
    "dairy",
    "poultry farm",
    "animal feed store",

    # Tier 2 — construction & hardware
    "hardware store",
    "building materials supplier",
    "plumbing supply store",
    "electrical supply store",
    "paint store",

    # Tier 2 — electronics
    "electronics store",
    "phone repair",
    "computer store",
    "appliance store",
    "cctv installer",

    # Tier 3 — services
    "laundry",
    "dry cleaner",
    "beauty salon",
    "barber shop",
    "spa",
    "gym",
    "car rental",
    "travel agency",
    "cyber cafe",
    "printing shop",
    "tailor",
    "cleaning service",

    # Tier 3 — retail consumer
    "clothing store",
    "shoe store",
    "boutique",
    "cosmetics store",
    "bookstore",
    "stationery store",
    "pet store",
    "sports store",
    "jewelry store",

    # Tier 3 — financial services
    "sacco",
    "insurance agency",
    "money transfer",
    "accounting firm",
    "audit firm",

    # Tier 3 — education
    "private school",
    "college",
    "training center",
    "driving school",

    # Tier 3 — real estate
    "real estate agency",
    "property management",
    "apartment building",

    # Tier 3 — media & agencies
    "digital agency",
    "marketing agency",
    "advertising agency",
    "event planner",
    "photography studio",
    "signage company",
]