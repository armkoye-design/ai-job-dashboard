import json
import re
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse
from xml.etree import ElementTree as ET


import pandas as pd
import requests
import streamlit as st
from bs4 import BeautifulSoup
from openai import OpenAI

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="AI Job Intelligence Dashboard",
    layout="wide"
)

# ============================================================
# SAVED API KEYS (paste once here)
# ============================================================
try:
    SAVED_SERPAPI_KEY = st.secrets["SERPAPI_KEY"]
except:
    SAVED_SERPAPI_KEY = ""

try:
    SAVED_OPENAI_KEY = st.secrets["OPENAI_KEY"]
except:
    SAVED_OPENAI_KEY = ""


SPECIAL_SOURCES = [
    "UN Careers",
    "UNDP",
    "UNICEF",
    "WHO",
    "UNHCR",
    "WFP",
    "IOM",
    "World Bank",
    "EBRD",
    "EURES",
]
# ============================================================
# DEFAULTS
# ============================================================
ROLE_QUERY_DEFAULT = "Data Analyst"

DEFAULT_SOURCES = [
    "SerpAPI Google Jobs",

    # Europe
    "EnglishJobs.de Network",
    "Relocate.me",
    "EURES",

    # Remote
    "RemoteOK",
    "We Work Remotely",

    # Canada
    "Job Bank Canada",

    # USA
    "USAJobs",

    # UK
    "Civil Service Jobs UK",

    # Australia
    "APS Jobs",
    "Seek Australia",

    # New Zealand
    "Jobs.govt.nz",

    # Ireland
    "IrishJobs.ie",

    # UN
    "UN Careers",
    "UNDP",
    "UNICEF",
    "UNHCR",
    "WFP",
    "WHO",
    "IOM",
    "World Bank",
    "EBRD",
   
]

ENGLISH_SPEAKING_COUNTRIES = {
    "Canada",
    "United Kingdom",
    "United States",
    "Ireland",
    "Australia",
    "New Zealand",
}

DEFAULT_COUNTRIES = [
    "Canada", "United Kingdom", "United States", "Ireland", "Australia", "New Zealand",
    "Germany", "Netherlands", "France", "Belgium", "Luxembourg", "Switzerland",
    "Austria", "Spain", "Portugal", "Italy", "Sweden", "Norway", "Denmark",
    "Finland", "Iceland", "Poland", "Czech Republic", "Slovakia", "Hungary",
    "Romania", "Bulgaria", "Greece", "Croatia", "Slovenia", "Serbia", "Montenegro",
    "Bosnia and Herzegovina", "North Macedonia", "Albania", "Kosovo", "Estonia",
    "Latvia", "Lithuania", "Ukraine", "Moldova", "Malta", "Cyprus",
]

# Country -> city fallbacks used behind the scenes for SerpAPI Google Jobs
SERPAPI_SEARCH_LOCATIONS = {
    "Canada": ["Toronto", "Vancouver", "Montreal", "Calgary", "Ottawa"],
    "United Kingdom": ["London", "Manchester", "Birmingham", "Edinburgh", "Glasgow"],
    "United States": ["New York", "San Francisco", "Boston", "Chicago", "Seattle", "Austin", "Washington DC"],
    "Ireland": ["Dublin", "Cork", "Galway"],
    "Germany": ["Berlin", "Munich", "Hamburg", "Frankfurt", "Dusseldorf", "Cologne", "Stuttgart"],
    "Netherlands": ["Amsterdam", "Rotterdam", "Utrecht", "Eindhoven", "The Hague"],
    "France": ["Paris", "Lyon", "Marseille", "Toulouse", "Nantes"],
    "Belgium": ["Brussels", "Antwerp", "Ghent"],
    "Luxembourg": ["Luxembourg City"],
    "Switzerland": ["Zurich", "Geneva", "Basel"],
    "Austria": ["Vienna", "Graz", "Linz"],
    "Spain": ["Madrid", "Barcelona", "Valencia", "Bilbao"],
    "Portugal": ["Lisbon", "Porto"],
    "Italy": ["Milan", "Rome", "Turin", "Bologna"],
    "Sweden": ["Stockholm", "Gothenburg", "Malmo"],
    "Norway": ["Oslo", "Bergen", "Trondheim"],
    "Denmark": ["Copenhagen", "Aarhus", "Odense"],
    "Finland": ["Helsinki", "Espoo", "Tampere"],
    "Iceland": ["Reykjavik"],
    "Poland": ["Warsaw", "Krakow", "Wroclaw"],
    "Czech Republic": ["Prague", "Brno"],
    "Slovakia": ["Bratislava"],
    "Hungary": ["Budapest"],
    "Romania": ["Bucharest"],
    "Bulgaria": ["Sofia"],
    "Greece": ["Athens", "Thessaloniki"],
    "Croatia": ["Zagreb"],
    "Slovenia": ["Ljubljana"],
    "Serbia": ["Belgrade"],
    "Montenegro": ["Podgorica"],
    "Bosnia and Herzegovina": ["Sarajevo"],
    "North Macedonia": ["Skopje"],
    "Albania": ["Tirana"],
    "Kosovo": ["Pristina"],
    "Estonia": ["Tallinn"],
    "Latvia": ["Riga"],
    "Lithuania": ["Vilnius"],
    "Ukraine": ["Kyiv", "Lviv"],
    "Moldova": ["Chisinau"],
    "Malta": ["Valletta"],
    "Cyprus": ["Nicosia"],
}

SERPAPI_GL_MAP = {
    "Canada": "ca", "United Kingdom": "uk", "United States": "us", "Ireland": "ie",
    "Germany": "de", "Netherlands": "nl", "France": "fr", "Belgium": "be",
    "Luxembourg": "lu", "Switzerland": "ch", "Austria": "at", "Spain": "es",
    "Portugal": "pt", "Italy": "it", "Sweden": "se", "Norway": "no", "Denmark": "dk",
    "Finland": "fi", "Iceland": "is", "Poland": "pl", "Czech Republic": "cz",
    "Slovakia": "sk", "Hungary": "hu", "Romania": "ro", "Bulgaria": "bg",
    "Greece": "gr", "Croatia": "hr", "Slovenia": "si", "Serbia": "rs",
    "Montenegro": "me", "Bosnia and Herzegovina": "ba", "North Macedonia": "mk",
    "Albania": "al", "Kosovo": "xk", "Estonia": "ee", "Latvia": "lv",
    "Lithuania": "lt", "Ukraine": "ua", "Moldova": "md", "Malta": "mt", "Cyprus": "cy",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/137.0.0.0 Safari/537.36"
    )
}
SESSION = requests.Session()
SESSION.headers.update(HEADERS)

ROLE_KEYWORDS = [
    "data analyst", "data manager", "data engineer", "data governance",
    "business intelligence", "bi analyst", "bi developer", "reporting analyst",
    "analytics", "data specialist", "database administrator", "sql",
    "power bi", "tableau", "etl", "dashboard", "master data",
    "mis", "information management", "metrics", "insights",
]

INTL_KEYWORDS = [
    "english", "international", "global", "relocation", "visa",
    "sponsorship", "work permit", "hybrid", "remote", "english-speaking",
    "no german required",
]

GENERIC_TITLE_SKIP = {
    "home", "faq", "about", "privacy", "cookies", "sitemap",
    "terms", "contact", "sign in", "log in", "post a job",
    "jobs", "job", "search", "apply filter", "filter jobs",
}

ENGLISHJOBS_SITES = [
    {"country": "Germany", "base": "https://englishjobs.de", "seeds": ["/", "/jobs/english", "/jobs/visa_sponsorship", "/in/berlin", "/in/hamburg", "/in/frankfurt", "/in/munich", "/in/dusseldorf", "/in/cologne", "/in/stuttgart"]},
    {"country": "France", "base": "https://englishjobs.fr", "seeds": ["/", "/jobs/english", "/jobs/visa_sponsorship"]},
    {"country": "Spain", "base": "https://englishjobs.es", "seeds": ["/", "/jobs/english", "/jobs/visa_sponsorship"]},
    {"country": "Italy", "base": "https://englishjobs.it", "seeds": ["/", "/jobs/english", "/jobs/visa_sponsorship"]},
    {"country": "Denmark", "base": "https://englishjobs.dk", "seeds": ["/", "/jobs/english", "/jobs/visa_sponsorship"]},
    {"country": "Finland", "base": "https://englishjobs.fi", "seeds": ["/", "/jobs/english", "/jobs/visa_sponsorship"]},
    {"country": "Norway", "base": "https://englishjobs.no", "seeds": ["/", "/jobs/english", "/jobs/visa_sponsorship"]},
    {"country": "Belgium", "base": "https://englishjobs.be", "seeds": ["/", "/jobs/english", "/jobs/visa_sponsorship"]},
    {"country": "Portugal", "base": "https://englishjobs.pt", "seeds": ["/", "/jobs/english", "/jobs/visa_sponsorship"]},
    {"country": "Poland", "base": "https://englishjobs.pl", "seeds": ["/", "/jobs/english", "/jobs/visa_sponsorship"]},
    {"country": "Austria", "base": "https://englishjobsearch.at", "seeds": ["/", "/jobs/english", "/jobs/visa_sponsorship"]},
    {"country": "Switzerland", "base": "https://englishjobsearch.ch", "seeds": ["/", "/jobs/english", "/jobs/visa_sponsorship"]},
    {"country": "Sweden", "base": "https://englishjobsearch.se", "seeds": ["/", "/jobs/english", "/jobs/visa_sponsorship"]},
    {"country": "Netherlands", "base": "https://englishjobsearch.nl", "seeds": ["/", "/jobs/english", "/jobs/visa_sponsorship"]},
]

# ============================================================
# HELPERS
# ============================================================
from bs4 import BeautifulSoup

def strip_html(html):
    if not html:
        return ""
    return BeautifulSoup(html, "html.parser").get_text(" ", strip=True)

def clean_text(value: Optional[str]) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def clamp(n: int, lo: int = 0, hi: int = 100) -> int:
    return max(lo, min(hi, int(n)))


def normalize_job(job: Dict) -> Dict:
    job["title"] = clean_text(job.get("title"))
    job["company"] = clean_text(job.get("company"))
    job["location"] = clean_text(job.get("location"))
    job["description"] = clean_text(job.get("description"))
    job["url"] = clean_text(job.get("url"))
    job["source"] = clean_text(job.get("source"))
    job["country"] = clean_text(job.get("country"))
    return job


def is_candidate_text(text: str) -> bool:
    t = (text or "").lower()
    if not t:
        return False
    if any(skip == t for skip in GENERIC_TITLE_SKIP):
        return False
    return any(k in t for k in ROLE_KEYWORDS) or any(k in t for k in INTL_KEYWORDS)


def infer_country_from_location(location_text: str, fallback_country: str = "") -> str:
    t = (location_text or "").lower()
    country_names = [
        "switzerland",
        "cameroon",
        "costa rica",
        "afghanistan",
        "india",
        "cambodia",
        "haiti",
        "greece",
        "niger",
        "kenya",
        "uganda",
        "ethiopia",
        "germany",
        "france",
        "canada",
        "united states",
        "united kingdom",
    ]
    
    for country in country_names:
        if country in t:
            return country.title()
    if not t:
        return fallback_country or ""

    if any(x in t for x in ["remote", "worldwide", "global", "europe", "emea"]):
        return "Remote/Global"

    city_to_country = {
        "toronto": "Canada", "vancouver": "Canada", "montreal": "Canada", "calgary": "Canada", "ottawa": "Canada",
        "london": "United Kingdom", "manchester": "United Kingdom", "birmingham": "United Kingdom", "edinburgh": "United Kingdom", "glasgow": "United Kingdom",
        "dublin": "Ireland", "cork": "Ireland", "galway": "Ireland",
        "new york": "United States", "san francisco": "United States", "boston": "United States", "chicago": "United States", "seattle": "United States", "austin": "United States", "washington dc": "United States", "washington": "United States",
        "berlin": "Germany", "munich": "Germany", "münchen": "Germany", "hamburg": "Germany", "frankfurt": "Germany", "cologne": "Germany", "köln": "Germany", "düsseldorf": "Germany", "stuttgart": "Germany",
        "amsterdam": "Netherlands", "rotterdam": "Netherlands", "utrecht": "Netherlands", "eindhoven": "Netherlands", "the hague": "Netherlands", "den haag": "Netherlands",
        "paris": "France", "lyon": "France", "marseille": "France", "toulouse": "France", "nantes": "France",
        "brussels": "Belgium", "antwerp": "Belgium", "ghent": "Belgium",
        "luxembourg city": "Luxembourg", "luxembourg": "Luxembourg",
        "zurich": "Switzerland", "zürich": "Switzerland", "geneva": "Switzerland", "genève": "Switzerland", "basel": "Switzerland",
        "vienna": "Austria", "wien": "Austria", "graz": "Austria", "linz": "Austria",
        "madrid": "Spain", "barcelona": "Spain", "valencia": "Spain", "bilbao": "Spain",
        "lisbon": "Portugal", "lisboa": "Portugal", "porto": "Portugal",
        "milan": "Italy", "rome": "Italy", "turin": "Italy", "torino": "Italy", "bologna": "Italy",
        "stockholm": "Sweden", "gothenburg": "Sweden", "göteborg": "Sweden", "malmo": "Sweden", "malmö": "Sweden",
        "oslo": "Norway", "bergen": "Norway", "trondheim": "Norway",
        "copenhagen": "Denmark", "aarhus": "Denmark", "odense": "Denmark",
        "helsinki": "Finland", "espoo": "Finland", "tampere": "Finland",
        "warsaw": "Poland", "warszawa": "Poland", "krakow": "Poland", "wroclaw": "Poland", "wrocław": "Poland",
        "prague": "Czech Republic", "brno": "Czech Republic",
        "bratislava": "Slovakia", "budapest": "Hungary", "bucharest": "Romania", "bucuresti": "Romania",
        "sofia": "Bulgaria", "athens": "Greece", "thessaloniki": "Greece", "zagreb": "Croatia",
        "ljubljana": "Slovenia", "belgrade": "Serbia", "podgorica": "Montenegro",
        "sarajevo": "Bosnia and Herzegovina", "skopje": "North Macedonia", "tirana": "Albania",
        "pristina": "Kosovo", "tallinn": "Estonia", "riga": "Latvia", "vilnius": "Lithuania",
        "kyiv": "Ukraine", "kiev": "Ukraine", "lviv": "Ukraine",
        "chisinau": "Moldova", "chişinău": "Moldova", "valletta": "Malta", "nicosia": "Cyprus", "reykjavik": "Iceland",
    }

    for city, country in city_to_country.items():
        if city in t:
            return country

    return fallback_country or ""


def country_matches_selected(job_country: str, selected_countries: List[str]) -> bool:
    if not selected_countries:
        return True
    if job_country in selected_countries:
        return True
    if job_country == "Remote/Global":
        return True
    return False
    
def query_match_score(job: Dict, search_query: str) -> int:
    title = (job.get("title", "") or "").lower().strip()
    query = (search_query or "").lower().strip()

    if not title or not query:
        return 0

    title = re.sub(r"[^a-z0-9\s]+", " ", title)
    query = re.sub(r"[^a-z0-9\s]+", " ", query)

    title = re.sub(r"\s+", " ", title).strip()
    query = re.sub(r"\s+", " ", query).strip()

    query_words = [w for w in query.split() if len(w) > 2]
    title_words = title.split()
    
    synonyms = {
        "analyst": ["analytics", "analysis", "research"],
        "data": ["dataset", "analytics"],
    }
    
    matches = 0
    
    for word in query_words:
    
        if word in title_words:
            matches += 1
            continue
    
        if word in synonyms:
            if any(s in title_words for s in synonyms[word]):
                matches += 1
    
    # all words matched
    if matches == len(query_words):
        return 90
        
    # Query Title
    if query in title:
        return 90
    
    # almost all words matched
    if matches == len(query_words) - 1:
        return 35
    
    # one keyword matched
    if matches == 1:
        return 10
    
    return 0

def heuristic_score(job: Dict) -> Dict:
    text = " ".join([
        job.get("title", ""),
        job.get("company", ""),
        job.get("location", ""),
        job.get("description", ""),
        " ".join(job.get("tags", []) if isinstance(job.get("tags"), list) else []),
        job.get("source", ""),
    ]).lower()

    relevance = 0
    visa = 0
    english_fit = 0

    for k in ROLE_KEYWORDS:
        if k in text:
            relevance += 8

    for k in INTL_KEYWORDS:
        if k in text:
            visa += 8

    if any(x in text for x in ["english", "international", "global"]):
        english_fit += 20
        relevance += 5

    if job.get("source") in {"EnglishJobs", "Relocate.me"}:
        relevance += 10
        english_fit += 15
        visa += 10

    if job.get("source") in {"RemoteOK", "WWR"}:
        relevance += 8
        english_fit += 20

    if any(x in text for x in ["relocation", "visa", "sponsorship"]):
        visa += 20

    return {
        "relevance": clamp(relevance),
        "visa_likelihood": clamp(visa),
        "english_fit": clamp(english_fit),
        "query_match": clamp(relevance),
        "reason": "Heuristic fallback scoring",
    }


def build_openai_client(api_key: str) -> Optional[OpenAI]:
    key = (api_key or "").strip()
    if not key or key == "PASTE_YOUR_OPENAI_KEY_HERE":
        return None
    try:
        return OpenAI(api_key=key)
    except Exception:
        return None

    prompt = f"""
You are helping an Iraqi applicant with 10+ years in data management, good English, and a bachelor in computer studies.

User Search Query:
{search_query}

Evaluate this job for:
1) relevance to the applicant's background
2) likelihood it could support an English-speaking international applicant
3) likelihood of visa/relocation friendliness
4) how well the job matches the user's search query

Scoring rules for query_match:
- 90-100 = direct match (Data Analyst, BI Analyst, Reporting Analyst)
- 70-89 = closely related (Power BI Developer, Business Intelligence Developer, Analytics Engineer)
- 40-69 = partially related (Data Engineer, Database Administrator, MIS Officer)
- 0-39 = unrelated jobs such as Teacher, Nurse, Marketing, Sales, Receptionist, HR, Finance, Legal

Return ONLY valid JSON with exactly these keys:
{{
  "relevance": 0-100,
  "visa_likelihood": 0-100,
  "english_fit": 0-100,
  "query_match": 0-100,
  "reason": "short explanation"
}}

Job source: {job.get("source", "")}
Country: {job.get("country", "")}
Title: {job.get("title", "")}
Company: {job.get("company", "")}
Location: {job.get("location", "")}
Description:
{job.get("description", "")[:2500]}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Return only JSON. No markdown."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        data = json.loads(response.choices[0].message.content)
        return {
            "relevance": clamp(data.get("relevance", 0)),
            "visa_likelihood": clamp(data.get("visa_likelihood", 0)),
            "english_fit": clamp(data.get("english_fit", 0)),
            "query_match": clamp(data.get("query_match", 0)),
            "reason": clean_text(data.get("reason", ""))[:300],
        }
    except Exception as e:

        return heuristic_score(job)


# ============================================================
# SOURCES
# ============================================================
def fetch_serpapi_jobs(query: str, country: str, api_key: str) -> List[Dict]:
    if not api_key or api_key == "PASTE_YOUR_SERPAPI_KEY_HERE":
        return []

    locations = SERPAPI_SEARCH_LOCATIONS.get(country, [country])
    gl = SERPAPI_GL_MAP.get(country, "")
    seen = set()
    results: List[Dict] = []

    for location in locations[:3]:
        try:
            params = {
                "engine": "google_jobs",
                "q": query,
                "location": location,
                "hl": "en",
                "api_key": api_key,
            }
            if gl:
                params["gl"] = gl

            resp = requests.get("https://serpapi.com/search.json", params=params, timeout=30)
            data = resp.json()
            jobs = data.get("jobs_results", [])
            st.write(f"SerpAPI {country} → {location}: {len(jobs)} jobs")

            for job in jobs:
                title = clean_text(job.get("title"))
                company = clean_text(job.get("company_name"))
                loc = clean_text(job.get("location"))
                desc = clean_text(job.get("description", ""))
                url = clean_text(job.get("apply_options", [{}])[0].get("link"))

                key = (title, company, loc, url)
                if key in seen:
                    continue
                seen.add(key)

                inferred_country = infer_country_from_location(loc, fallback_country=country)
                if not inferred_country:
                    inferred_country = country

                results.append(normalize_job({
                    "source": "SerpAPI",
                    "country": inferred_country,
                    "title": title,
                    "company": company,
                    "location": loc,
                    "description": f"{title} {company} {location}",
                    "url": url,
                    "tags": [],
                }))
        except Exception:
            continue

    return results


def scrape_html_jobs_from_site(country: str, base: str, seeds: List[str]) -> List[Dict]:
    found = []
    seen_urls = set()

    for path in seeds:
        url = urljoin(base, path)
        try:
            resp = SESSION.get(url, timeout=20)
            if resp.status_code >= 400:
                continue
            html = resp.text
        except requests.RequestException:
            continue

        soup = BeautifulSoup(html, "html.parser")
        for a in soup.find_all("a", href=True):
            title = clean_text(a.get_text(" ", strip=True))
            href = urljoin(base, a["href"])
            href_l = href.lower()

            if len(title) < 8:
                continue
            if title.lower() in GENERIC_TITLE_SKIP:
                continue
           # TEMP DEBUG    
           # if not any(x in href_l for x in ["/job", "/jobs/", "/in/"]):
           #    continue

            context = clean_text(a.parent.get_text(" ", strip=True)) if a.parent else ""
            combined = f"{title} {context}".lower()
            if not is_candidate_text(combined):
                continue
            if href in seen_urls:
                continue
            seen_urls.add(href)
            
            title_l = title.lower()

            bad_terms = [
                "blog",
                "stories",
                "story",
                "visa",
                "immigration",
                "salary",
                "salaries",
                "cost of living",
                "working abroad",
                "relocation companies",
                "read our blog",
                "expat",
                "money & taxes",
                "about",
                "contact",
                "newsletter",
                "english jobs germany",
                "english jobs",
            ]
            
            good_job_terms = [
                "job",
                "jobs",
                "analyst",
                "developer",
                "engineer",
                "manager",
                "specialist",
                "consultant",
                "officer",
                "coordinator",
                "director",
                "lead",
                "head",
                "scientist",
                "administrator",
            ]
            
            if any(term in title_l for term in bad_terms):
                continue
            
            if not any(term in title_l for term in good_job_terms):
                continue
            
            
            found.append(normalize_job({
                "source": "EnglishJobs",
                "country": country,
                "title": title,
                "company": "",
                "location": country,
                "description": context[:2500],
                "url": href,
                "tags": [],
            }))

    return found


def fetch_relocate_me() -> List[Dict]:
    url = "https://relocate.me/international-jobs"
    found = []
    seen_urls = set()

    try:
        resp = SESSION.get(url, timeout=25)
        if resp.status_code >= 400:
            return []
        soup = BeautifulSoup(resp.text, "html.parser")
    except requests.RequestException:
        return []

    for a in soup.find_all("a", href=True):
        title = clean_text(a.get_text(" ", strip=True))
        bad_titles = [
        "expat stories",
        "visas & immigration",
        "money & taxes",
        "working abroad",
        "read our blog",
        ]

        if title.lower() in bad_titles:
            continue

        
        href = urljoin(url, a["href"])
        href_l = href.lower()

        if len(title) < 8:
            continue
        if title.lower() in GENERIC_TITLE_SKIP:
            continue
        if "relocate.me" not in href_l:
            continue

        context = clean_text(a.parent.get_text(" ", strip=True)) if a.parent else ""
        combined = f"{title} {context}".lower()
        if not is_candidate_text(combined):
            continue
        if href in seen_urls:
            continue
        seen_urls.add(href)

        inferred_country = "Europe"
        for c in ["Germany", "Netherlands", "United Kingdom", "Portugal", "Spain", "France", "Belgium", "Sweden", "Denmark", "Finland", "Ireland", "Cyprus", "Austria", "Switzerland", "Poland", "Italy", "Norway", "Canada",
    "United States",
    "Australia",
    "New Zealand",]:
            if c.lower() in combined:
                inferred_country = c
                break

        found.append(normalize_job({
            "source": "Relocate.me",
            "country": inferred_country,
            "title": title,
            "company": "",
            "location": inferred_country,
            "description": context[:2500],
            "url": href,
            "tags": [],
        }))

    return found


def fetch_remoteok() -> List[Dict]:
    url = "https://remoteok.com/api"
    found = []
    try:
        resp = SESSION.get(url, timeout=25)
        data = resp.json()
    except Exception:
        return []

    for item in data[1:]:
        title = clean_text(item.get("position"))
        company = clean_text(item.get("company"))
        location = clean_text(item.get("location"))
        desc = clean_text(item.get("description"))
        apply_url = clean_text(item.get("apply_url") or item.get("url") or item.get("url_raw"))
        tags = item.get("tags", []) if isinstance(item.get("tags", []), list) else []

        combined = f"{title} {company} {location} {desc} {' '.join(tags)}".lower()
        if not is_candidate_text(combined):
            continue
        
        found.append(normalize_job({
            "source": "RemoteOK",
            "country": "Remote/Global",
            "title": title,
            "company": company,
            "location": location or "Remote",
            "description": desc[:2500],
            "url": apply_url,
            "tags": tags,
        }))

    return found
    


def fetch_wwr() -> List[Dict]:
    url = "https://weworkremotely.com/remote-jobs.rss"
    found = []
    try:
        resp = SESSION.get(url, timeout=25)
        root = ET.fromstring(resp.text)
    except Exception:
        return []

    for item in root.findall(".//item"):
        title = clean_text(item.findtext("title"))
        link = clean_text(item.findtext("link"))
        raw_desc = item.findtext("description")
        desc = strip_html(raw_desc)
        combined = f"{title} {desc}".lower()
        if not is_candidate_text(combined):
            continue

        found.append(normalize_job({
            "source": "WWR",
            "country": "Remote/Global",
            "title": title,
            "company": "",
            "location": "Remote",
            "description": desc[:500],
            "url": link,
            "tags": [],
        }))

    return found


def parse_custom_source(url: str) -> List[Dict]:
    url = clean_text(url)
    if not url:
        return []

    found = []
    try:
        resp = SESSION.get(url, timeout=25)
        if resp.status_code >= 400:
            return []
        html = resp.text
    except requests.RequestException:
        return []

    soup = BeautifulSoup(html, "html.parser")
    base = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
    seen_urls = set()

    for a in soup.find_all("a", href=True):
        title = clean_text(a.get_text(" ", strip=True))

        href = urljoin(url, a["href"])
        href = urljoin(base, a["href"])
        href_l = href.lower()

        if len(title) < 8:
            continue
        if title.lower() in GENERIC_TITLE_SKIP:
            continue
        if not any(x in href_l for x in ["job", "career", "vacanc", "opportun", "opening"]):
            continue

        context = clean_text(a.parent.get_text(" ", strip=True)) if a.parent else ""
        combined = f"{title} {context}".lower()
        if not is_candidate_text(combined):
            continue
        if href in seen_urls:
            continue
        seen_urls.add(href)

        found.append(normalize_job({
            "source": "Custom",
            "country": "Custom",
            "title": title,
            "company": "",
            "location": "",
            "description": context[:2500],
            "url": href,
            "tags": [],
        }))

    return found
    


from urllib.parse import quote_plus

def fetch_eures_jobs(query="", countries=None):
    jobs = []

    try:
        url = (
            "https://europa.eu/eures/portal/jv-se/search"
            f"?keywordsEverywhere={query.replace(' ', '+')}"
        )

        r = SESSION.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0"
            },
            timeout=30
        )

       

        import re
    
        matches = re.findall(
            r'https://[^"]+',
            r.text
        )
    
       
        for m in matches[:100]:
            st.write(m)

    except Exception as e:
        st.write("EURES error:", e)

    return jobs
# ==========================================
# VERSION 10 - UN CAREERS
# ==========================================
def fetch_un_jobs():
    jobs = []

    try:
        url = "https://careers.un.org"

        jobs.append({
            "source": "UN Careers",
            "country": "International",
            "title": "Visit UN Careers",
            "company": "United Nations",
            "location": "Various",
            "description": "Browse current UN vacancies",
            "url": url,
            "tags": ["UN"],
        })
    except:
        pass

    return jobs
    
def fetch_undp_jobs():
    jobs = []

    try:
        url = "https://jobs.undp.org"

        jobs.append({
            "source": "UNDP",
            "country": "International",
            "title": "Visit UNDP Careers",
            "company": "UNDP",
            "location": "Various",
            "description": "Browse current UNDP vacancies",
            "url": url,
            "tags": ["UNDP"],
        })
        
        st.write(full_page_text[:2000])

    except Exception:
        pass

    return jobs    

def fetch_unicef_jobs():
    return [{
        "source": "UNICEF",
        "country": "International",
        "title": "Visit unicef Careers",
        "company": "UNICEF",
        "location": "Global",
        "description": "UNICEF vacancies",
        "url": "https://careers.unicef.org",
        "tags": ["UNICEF"],
    }]
def fetch_who_jobs():
    return [{
        "source": "WHO",
        "country": "International",
        "title": "Visit WHO Careers",
        "company": "WHO",
        "location": "Global",
        "description": "WHO vacancies",
        "url": "https://careers.who.int",
        "tags": ["WHO"],
    }]
def fetch_unhcr_jobs():
    return [{
        "source": "UNHCR",
        "country": "International",
        "title": "Visit UNHCR Careers",
        "company": "UNHCR",
        "location": "Global",
        "description": "UNHCR vacancies",
        "url": "https://www.unhcr.org/careers",
        "tags": ["UNHCR"],
    }]
def fetch_wfp_jobs():
    return [{
        "source": "WFP",
        "country": "International",
        "title": "Visit WFP Careers",
        "company": "World Food Programme",
        "location": "Global",
        "description": "WFP vacancies",
        "url": "https://www.wfp.org/careers",
        "tags": ["WFP"],
    }]
def fetch_iom_jobs():
    return [{
        "source": "IOM",
        "country": "International",
        "title": "Visit IOM Careers",
        "company": "IOM",
        "location": "Global",
        "description": "IOM vacancies",
        "url": "https://www.iom.int/careers",
        "tags": ["IOM"],
    }]
def fetch_worldbank_jobs():
    return [{
        "source": "World Bank",
        "country": "International",
        "title": "Visit World Bank Careers",
        "company": "World Bank",
        "location": "Global",
        "description": "World Bank vacancies",
        "url": "https://www.worldbank.org/en/about/careers",
        "tags": ["World Bank"],
    }]
def fetch_ebrd_jobs():
    return [{
        "source": "EBRD",
        "country": "International",
        "title": "Visit EBRD Careers",
        "company": "EBRD",
        "location": "Global",
        "description": "EBRD vacancies",
        "url": "https://jobs.ebrd.com",
        "tags": ["EBRD"],
    }]
    
import requests

def fetch_job_bank_canada(query: str, limit: int = 50) -> List[Dict]:
    

    jobs = []

    try:
        url = "https://www.jobbank.gc.ca/jobsearch/jobsearch?searchstring=" + quote_plus(query)
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
        if r.status_code != 200:
            return jobs

        soup = BeautifulSoup(r.text, "html.parser")
        cards = soup.select("article.action-buttons")

        for card in cards[:limit]:
            title_el = card.select_one("span.noctitle")
            link_el = card.select_one("a.resultJobItem")
            date_el = card.select_one("li.date")
            company_el = card.select_one("li.business")
            location_el = card.select_one("li.location")

            if not title_el or not link_el:
                continue

            title = clean_text(title_el.get_text(" ", strip=True))
            href = link_el.get("href", "")
            if href.startswith("/"):
                href = "https://www.jobbank.gc.ca" + href
                st.write("Fetching:", href)

            company = clean_text(company_el.get_text(" ", strip=True)) if company_el else ""
            location = clean_text(location_el.get_text(" ", strip=True)) if location_el else ""
            desc = clean_text(date_el.get_text(" ", strip=True)) if date_el else ""

            job_page = requests.get(
                href,
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=30
            )
            
            st.write("Page size:", len(job_page.text))
            st.write(job_page.text[:3000])
            
            full_page_text = ""
            
            if job_page.status_code == 200:
                job_soup = BeautifulSoup(job_page.text, "html.parser")
            
                full_page_text = clean_text(
                    job_soup.get_text(" ", strip=True)
                )
                        
            jobs.append({
                "source": "Job Bank Canada",
                "country": "Canada",
                "title": title,
                "company": company,
                "location": location,
                "description": full_page_text,
                "url": href,
                "tags": [],
            })
        
        return jobs

    except Exception as e:
        st.error(f"Job Bank error: {e}")
        return jobs


# ============================================================
# STREAMLIT UI
# ============================================================
st.title("🧠 AI Job Intelligence Dashboard")
st.caption("Hybrid job search: Google Jobs + English job boards + remote boards + custom sources")

openai_client = build_openai_client(SAVED_OPENAI_KEY)

st.sidebar.header("Search")

query = st.sidebar.text_input(
    "Search keywords",
    ROLE_QUERY_DEFAULT
)

selected_countries = st.sidebar.multiselect(
    "Choose countries",
    options=DEFAULT_COUNTRIES,
    default=[]
)

custom_country = st.sidebar.text_input(
    "Add custom country",
    placeholder="Example: Germany, France, Sweden, Australia"
)

st.sidebar.divider()

countries = list(selected_countries)

if custom_country.strip():
    countries.append(custom_country.strip())

countries = [x for x in dict.fromkeys([clean_text(x) for x in countries]) if x]
english_countries = {
    "Canada",
    "United States",
    "United Kingdom",
    "Ireland",
    "Australia",
    "New Zealand",
}

europe_countries = {
    "Germany",
    "France",
    "Netherlands",
    "Belgium",
    "Austria",
    "Switzerland",
    "Sweden",
    "Norway",
    "Denmark",
    "Finland",
}

st.sidebar.header("Sources")


available_sources = set()

for country in countries:

    if country == "Canada":

        available_sources.update([
            "SerpAPI Google Jobs",
            "Job Bank Canada",
            "RemoteOK",
            "We Work Remotely",
            "Relocate.me",
        ])

    elif country == "United States":

        available_sources.update([
            "SerpAPI Google Jobs",
            "USAJobs",
            "RemoteOK",
            "We Work Remotely",
            "Relocate.me",
        ])

    elif country == "United Kingdom":

        available_sources.update([
            "SerpAPI Google Jobs",
            "Civil Service Jobs UK",
            "RemoteOK",
            "We Work Remotely",
            "Relocate.me",
        ])

    elif country == "Australia":

        available_sources.update([
            "SerpAPI Google Jobs",
            "APS Jobs",
            "Seek Australia",
            "RemoteOK",
            "We Work Remotely",
        ])

    elif country == "New Zealand":

        available_sources.update([
            "SerpAPI Google Jobs",
            "Jobs.govt.nz",
            "RemoteOK",
            "We Work Remotely",
        ])

    elif country == "Ireland":

        available_sources.update([
            "SerpAPI Google Jobs",
            "IrishJobs.ie",
            "RemoteOK",
            "We Work Remotely",
        ])

    elif country in europe_countries:

        available_sources.update([
            "SerpAPI Google Jobs",
            "EnglishJobs.de Network",
            "EURES",
            "Relocate.me",
            "RemoteOK",
            "We Work Remotely",
        ])

if not countries:
    available_sources = set(DEFAULT_SOURCES)

available_sources = sorted(list(available_sources))



# filter available_sources based on countries

selected_sources = st.sidebar.multiselect(
    "Choose job sources",
    options=available_sources,
    default=[],
)


custom_source_url = st.sidebar.text_input(
    "Add custom source URL",
    placeholder="https://example.com/jobs",
    help="Use this for extra websites only.",
)


organization_types = st.sidebar.multiselect(
    "Organization Type",
    [
        "Private Sector",
        "UN System",
        "International NGO",
        "Development Bank",
        "European Union",
    ],
    default=[],
)

if "UN System" in organization_types:
        for src in [
            "UN Careers",
            "UNDP",
            "UNICEF",
            "UNHCR",
            "WHO",
            "WFP",
            "IOM",
        ]:
            if src not in selected_sources:
                selected_sources.append(src)
    
if "Development Bank" in organization_types:
        for src in [
            "World Bank",
            "EBRD",
        ]:
            if src not in selected_sources:
                selected_sources.append(src)

min_visa = st.sidebar.slider("Min Visa Likelihood", 0, 100, 0)
min_relevance = st.sidebar.slider("Min Relevance", 0, 100, 0)
min_english = st.sidebar.slider("Min English Fit", 0, 100, 0)
only_high_fit = st.sidebar.checkbox("Show only high-fit jobs", value=False)
include_remote_jobs = st.sidebar.checkbox(
    "Include Remote Jobs",
    value=False
)


if custom_country.strip():
    countries.append(custom_country.strip())

countries = [x for x in dict.fromkeys([clean_text(x) for x in countries]) if x]

search_clicked = st.sidebar.button("🔍 Search Jobs")
    
if search_clicked:
        st.session_state.results_df = pd.DataFrame()
        if not countries:
            st.warning("Please select at least one country.")
            st.stop()
        
        if not selected_sources:
            st.warning("Please select at least one job source.")
            st.stop()
        all_jobs: List[Dict] = []
        seen_keys = set()
    
    # 1) SerpAPI Google Jobs
        if "SerpAPI Google Jobs" in selected_sources:
            if not SAVED_SERPAPI_KEY.strip() or SAVED_SERPAPI_KEY.startswith("PASTE_YOUR_SERPAPI_KEY_HERE"):
                st.warning("SerpAPI key is missing in the script. Google Jobs will be skipped.")
            else:
                for country in countries:
                    
                    serp_jobs = fetch_serpapi_jobs(query, country, SAVED_SERPAPI_KEY.strip())
                    for job in serp_jobs:
                        job_country = infer_country_from_location(job.get("location", ""), fallback_country=country)
                        if not country_matches_selected(job_country, countries):
                            continue
                        job["country"] = job_country or country
                        key = (job.get("source"), job.get("title"), job.get("company"), job.get("location"), job.get("url"))
                        if key in seen_keys:
                            continue
                        seen_keys.add(key)
                        all_jobs.append(job)
        
        # 2) EnglishJobs network
        if "EnglishJobs.de Network" in selected_sources:
            for site in ENGLISHJOBS_SITES:
                if site["country"] not in countries:
                    continue
              
                jobs = scrape_html_jobs_from_site(site["country"], site["base"], site["seeds"])
                for job in jobs:
                    key = (job.get("source"), job.get("title"), job.get("company"), job.get("location"), job.get("url"))
                    if key in seen_keys:
                        continue
                    seen_keys.add(key)
                    all_jobs.append(job)
        
        # 3) Relocate.me
        if "Relocate.me" in selected_sources:
            
            jobs = fetch_relocate_me()
            for job in jobs:
                inferred = infer_country_from_location(job.get("location", ""), fallback_country=job.get("country", ""))
                job_country = job.get("country", "")
        
                if (
                    countries
                    and job_country not in countries
                    and job_country not in ["Europe", "Remote/Global"]
                ):
                    continue
                key = (job.get("source"), job.get("title"), job.get("company"), job.get("location"), job.get("url"))
                if key in seen_keys:
                    continue
                seen_keys.add(key)
                all_jobs.append(job)
        
        # 4) RemoteOK
        if "RemoteOK" in selected_sources:
            
            jobs = fetch_remoteok()
            for job in jobs:
                key = (job.get("source"), job.get("title"), job.get("company"), job.get("location"), job.get("url"))
                if key in seen_keys:
                    continue
                seen_keys.add(key)
                all_jobs.append(job)
        
        # 5) We Work Remotely
        if "We Work Remotely" in selected_sources:
           
        
            jobs = fetch_wwr()
        
            
        
            
        
            for job in jobs:
                key = (
                    job.get("source"),
                    job.get("title"),
                    job.get("company"),
                    job.get("location"),
                    job.get("url"),
                )
        
                if key in seen_keys:
                    continue
        
                seen_keys.add(key)
                all_jobs.append(job)
        
            
                
        # 6) EURES
        if "EURES" in selected_sources:
            
        
            jobs = fetch_eures_jobs(query, countries)
        
            for job in jobs:
                key = (
                    job.get("source"),
                    job.get("title"),
                    job.get("company"),
                    job.get("location"),
                    job.get("url"),
                )
        
                if key in seen_keys:
                    continue
        
                seen_keys.add(key)
                all_jobs.append(job)
        # 7) UN Careers
        if "UN Careers" in selected_sources:
            
        
            jobs = fetch_un_jobs()
        
            for job in jobs:
                key = (
                    job.get("source"),
                    job.get("title"),
                    job.get("company"),
                    job.get("location"),
                    job.get("url"),
                )
        
                if key in seen_keys:
                    continue
        
                seen_keys.add(key)
                all_jobs.append(job)
        # 8) UNDP
        if "UNDP" in selected_sources:
            
        
            jobs = fetch_undp_jobs()
        
            for job in jobs:
                key = (
                    job.get("source"),
                    job.get("title"),
                    job.get("company"),
                    job.get("location"),
                    job.get("url"),
                )
        
                if key in seen_keys:
                    continue
        
                seen_keys.add(key)
                all_jobs.append(job) 

    # 9) Job Bank Canada

        if "Job Bank Canada" in selected_sources:
            jobs = fetch_job_bank_canada(query)
        
                
        
            for job in jobs:
                key = (
                    job.get("source", ""),
                    job.get("title", ""),
                    job.get("company", ""),
                    job.get("location", ""),
                    job.get("url", ""),
                )
        
                if key in seen_keys:
                    continue
        
                seen_keys.add(key)
                all_jobs.append(job)
        
        
            
            
        # 10) Other Agencies
        if "UNICEF" in selected_sources:
            
        
            jobs = fetch_unicef_jobs()
        
            for job in jobs:
                key = (
                    job.get("source"),
                    job.get("title"),
                    job.get("company"),
                    job.get("location"),
                    job.get("url"),
                )
        
                if key in seen_keys:
                    continue
        
                seen_keys.add(key)
                all_jobs.append(job)
            
            
        
        if "WHO" in selected_sources:
           
        
            jobs = fetch_who_jobs()
        
            for job in jobs:
                key = (
                    job.get("source"),
                    job.get("title"),
                    job.get("company"),
                    job.get("location"),
                    job.get("url"),
                )
        
                if key in seen_keys:
                    continue
        
                seen_keys.add(key)
                all_jobs.append(job)
        
        
        
        if "UNHCR" in selected_sources:
           
        
            jobs = fetch_unhcr_jobs()
        
            for job in jobs:
                key = (
                    job.get("source"),
                    job.get("title"),
                    job.get("company"),
                    job.get("location"),
                    job.get("url"),
                )
        
                if key in seen_keys:
                    continue
        
                seen_keys.add(key)
                all_jobs.append(job)
        
        
        if "WFP" in selected_sources:
            
        
            jobs = fetch_wfp_jobs()
        
            for job in jobs:
                key = (
                    job.get("source"),
                    job.get("title"),
                    job.get("company"),
                    job.get("location"),
                    job.get("url"),
                )
        
                if key in seen_keys:
                    continue
        
                seen_keys.add(key)
                all_jobs.append(job)
        
        
        if "IOM" in selected_sources:
         
        
            jobs = fetch_iom_jobs()
        
            for job in jobs:
                key = (
                    job.get("source"),
                    job.get("title"),
                    job.get("company"),
                    job.get("location"),
                    job.get("url"),
                )
        
                if key in seen_keys:
                    continue
        
                seen_keys.add(key)
                all_jobs.append(job)
        
        
        if "World Bank" in selected_sources:
          
        
            jobs = fetch_worldbank_jobs()
        
            for job in jobs:
                key = (
                    job.get("source"),
                    job.get("title"),
                    job.get("company"),
                    job.get("location"),
                    job.get("url"),
                )
        
                if key in seen_keys:
                    continue
        
                seen_keys.add(key)
                all_jobs.append(job)
        
        
        if "EBRD" in selected_sources:
            
        
            jobs = fetch_ebrd_jobs()
        
            for job in jobs:
                key = (
                    job.get("source"),
                    job.get("title"),
                    job.get("company"),
                    job.get("location"),
                    job.get("url"),
                )
        
                if key in seen_keys:
                    continue
        
                seen_keys.add(key)
                all_jobs.append(job)
                
        
        # 9) Custom source URL
        if custom_source_url.strip():
            
        
            jobs = parse_custom_source(custom_source_url.strip())
        
            for job in jobs:
                key = (
                    job.get("source"),
                    job.get("title"),
                    job.get("company"),
                    job.get("location"),
                    job.get("url"),
                )
        
                if key in seen_keys:
                    continue
        
                seen_keys.add(key)
                all_jobs.append(job)

    
         # 10) Score jobs
       
        rows = []
        progress = st.progress(0)
           
        if not include_remote_jobs:
            filtered_jobs = []
        
            for job in all_jobs:
               
                location = str(job.get("location", "")).lower()
                country = str(job.get("country", "")).lower()
            
                is_remote = (
                    "remote" in location
                    or "remote" in country
                    or country == "remote/global"
                )
            
                if not is_remote:
                    filtered_jobs.append(job)
            
            all_jobs = filtered_jobs
        
                    
        
        
        #if not include_remote_jobs:
         #   all_jobs = [
         #       job for job in all_jobs
          #      if job.get("country") != "Remote/Global"
          #  ]
        
        total = max(len(all_jobs), 1)
        
        
        
        for idx, job in enumerate(all_jobs, start=1):
                
        
            progress.progress(min(idx / total, 1.0))
        
            score = query_match_score(job, query)
            ai = heuristic_score(job)

            text = (
                str(job.get("title", "")) + " " +
                str(job.get("description", ""))
            ).lower()
            
            visa_evidence = ""
            
            if job.get("source") == "Job Bank Canada":
            
                if any(x in text for x in [
                    "other candidates",
                    "with or without a valid canadian work permit",
                    "international candidates",
                    "foreign candidates",
                    "foreign worker",
                    "international applicants"
                ]):
            
                    ai["visa_likelihood"] = 90
                    visa_evidence = "Foreign workers accepted"
            
                elif any(x in text for x in [
                    "do not apply if you are not authorized to work in canada",
                    "canadian citizen",
                    "permanent resident of canada",
                    "temporary resident of canada with a valid work permit",
                    "you must be legally entitled to work in canada",
                    "must be authorized to work in canada"
                ]):
            
                    ai["visa_likelihood"] = 0
                    visa_evidence = "Canadian work authorization required"
            
                elif "posted on indeed.com" in text:
            
                    ai["visa_likelihood"] = 0
                    visa_evidence = "Indeed repost"
            
                elif "posted on talent.com" in text:
            
                    ai["visa_likelihood"] = 0
                    visa_evidence = "Talent repost"
            
                else:
            
                    ai["visa_likelihood"] = 20
                    visa_evidence = "No sponsorship evidence found"
            # -----------------------------------
            # Canada Job Bank visa override
            # -----------------------------------
            text = (
                str(job.get("title", "")) + " " +
                str(job.get("description", ""))
            ).lower()
        
            if job.get("source") == "Job Bank Canada":
                
                st.write("URL:", job.get("url"))
                st.write("TEXT:", text[:300])
                
                if (
                    "canadian citizen" in text
                    or "permanent resident" in text
                    or "valid work permit" in text
                    or "not authorized to work in canada" in text
                ):
                    ai["visa_likelihood"] = 0
        
            special_sources = [
                "UN Careers",
                "UNDP",
                "UNICEF",
                "WHO",
                "UNHCR",
                "WFP",
                "IOM",
                "World Bank",
                "EBRD",
                "EURES",
            ]
        
            if job.get("source") in special_sources:
                ai["relevance"] = 100
                ai["query_match"] = 100
           
            rows.append({
                "Source": job.get("source", ""),
                "Country": job.get("country", ""),
                "Title": job.get("title", ""),
                "Company": job.get("company", ""),
                "Location": job.get("location", ""),
                "Relevance": ai.get("relevance", 0),
                "Visa_Likelihood": ai.get("visa_likelihood", 0),
                "Visa_Evidence": visa_evidence,
                "English_Fit": ai.get("english_fit", 0),
                "Query_Match": score,
                "Reason": ai.get("reason", ""),
                "URL": job.get("url", ""),
                "Description": job.get("description", "")[:3000],
            })

            st.write(
            job.get("title"),
            score,
            ai["visa_likelihood"]
        )

            
    
        df = pd.DataFrame(rows)

        if not df.empty:
    
            if "Visa_Likelihood" in df.columns:
                df = df[df["Visa_Likelihood"] > 0]

        
        if not df.empty and "Query_Match" in df.columns:
            
            df = df[df["Query_Match"] >= 35]
            
        
        
            if not df.empty:
                df = df.sort_values(
                    by=["Query_Match", "Relevance", "Visa_Likelihood"],
                    ascending=[False, False, False]
                )
                
            
            
            st.session_state.results_df = df
        else:
            st.session_state.results_df = pd.DataFrame()
    
           
      
    # ============================================================
    # DISPLAY
    # ============================================================


if "results_df" in st.session_state and isinstance(st.session_state.results_df, pd.DataFrame):


    df = st.session_state.results_df
    
    if not df.empty:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Avg Visa Likelihood", f"{df['Visa_Likelihood'].mean():.1f}")
        with c2:
            st.metric("Avg Relevance", f"{df['Relevance'].mean():.1f}")
        with c3:
            st.metric("Avg English Fit", f"{df['English_Fit'].mean():.1f}")
            
        display_df = df[
            [
                "Source",
                "Country",
                "Title",
                "Company",
                "Location",
                "Relevance",
                "Visa_Likelihood",
                "English_Fit",
                "Query_Match",
                "URL",
            ]
        ].copy()
        
        st.dataframe(
            display_df,
            column_config={
                "URL": st.column_config.LinkColumn(
                    "Open Job",
                    display_text="Open"
                )
            },
            use_container_width=True,
            height=600
        )
    
    
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download results as CSV",
            data=csv,
            file_name="job_results.csv",
            mime="text/csv",
        )
    
        try:
            from io import BytesIO
            output = BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="Jobs")
            st.download_button(
                "Download results as Excel",
                data=output.getvalue(),
                file_name="job_results.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        except Exception:
            pass
    else:
        st.warning("No jobs matched your filters.")
else:
    st.info("Choose sources and countries, then click Search Jobs.")
