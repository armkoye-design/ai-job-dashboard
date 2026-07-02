# AI Job Intelligence Dashboard

## 1. Project Purpose

The AI Job Intelligence Dashboard is a worldwide job search platform designed for skilled professionals who want to relocate internationally.

The system searches multiple job boards, government career portals, UN organizations, NGOs, universities, and company career websites from one interface.

The primary objective is to identify genuine job opportunities that:

- are suitable for English-speaking professionals
- have a reasonable chance of visa sponsorship
- match the user's professional skills and experience
- reduce the amount of manual searching across hundreds of websites

The project prioritizes quality of results over quantity.

---

# 2. Target Users


The platform should work for any profession that will be written in key word, not only Data Specialist or IT.

---

# 3. Main Features

The application should provide:

- Search across multiple job websites simultaneously
- AI-assisted job relevance scoring
- Visa sponsorship likelihood estimation
- English-language suitability estimation
- Organization type classification
- Country filtering
- Remote job support
- Download results to Excel and CSV
- Custom job source support
- Custom country support

---

# 4. Supported Countries

The long-term goal is worldwide coverage.

Priority countries include:

- Germany
- Netherlands
- United Kingdom
- Ireland
- Canada
- Australia
- New Zealand
- Sweden
- Norway
- Denmark
- Finland
- Belgium
- Switzerland
- Austria
- Portugal
- Spain
- France
- Luxembourg
- United States

Additional countries should be easy to add.

---

# 5. Supported Job Sources

The application should continuously expand to include:

- EnglishJobs
- UN Careers
- UNDP
- UNICEF
- WHO
- UNHCR
- WFP
- IOM
- World Bank
- EBRD
- EU Careers
- EURES
- EURAXESS
- Academic Positions
- Nature Careers
- Times Higher Education
- LinkedIn (where allowed)
- Job Bank Canada
- USAJobs
- APS Jobs
- Jobs.govt.nz
- Civil Service Jobs UK
- IrishJobs
- Company career websites

Future sources should be easy to plug in.

---

# 6. English-Speaking Job Philosophy

The dashboard should estimate whether a job is realistically suitable for applicants who primarily speak English.

The score should consider:

- Job language
- Required local language
- Employer language
- International organization
- Company culture
- Previous hiring patterns when available

The goal is not to determine whether the posting is written in English.

The goal is to estimate whether an English-speaking applicant has a realistic chance.

---

# 7. Visa Sponsorship Philosophy

Visa sponsorship should be estimated using multiple indicators rather than one keyword.

Examples include:

- Explicit sponsorship statements
- Employer history
- International recruitment
- Skilled worker visas
- Relocation packages
- Immigration programs
- Government organizations
- Universities
- Large multinational companies

The score should be a probability estimate rather than a simple Yes/No.

---

# 8. Job Matching Philosophy

The search engine should understand professional relationships rather than exact keyword matching.

Example:

Searching for

Data Analyst

should also find

- Business Analyst
- BI Developer
- Data Engineer
- Analytics Engineer
- Reporting Analyst
- Data Scientist
- Machine Learning Engineer

but should avoid unrelated jobs like

- Sales Manager
- Marketing Manager
- Financial Controller
- Automotive Sales Consultant

Matching should prioritize professional similarity rather than exact text.

---

# 9. Scraper Design Rules

Every scraper should:

- scrape only genuine job postings
- ignore navigation pages
- ignore category pages
- ignore search pages
- ignore location pages
- fetch the job detail page
- store the complete job description
- normalize all jobs into one common structure
- remove duplicate jobs
- fail gracefully when websites change

Scrapers should maximize precision rather than collecting every possible page.

---

# 10. Query Matching Rules

The query matching engine should:

- recognize job title synonyms
- recognize related professions
- recognize abbreviations
- use exact phrase matching when appropriate
- use semantic matching
- reduce false positives
- reward title matches more than description matches

The objective is high-quality recommendations rather than maximum recall.

---

# 11. AI Scoring Goals

Future AI scoring should evaluate:

- Professional relevance
- Visa likelihood
- English suitability
- Career level
- Required experience
- Required education
- Salary (when available)
- Relocation friendliness

AI should assist ranking but never hide jobs completely.

---

# 12. Coding Rules

When modifying the project:

- Never modify unrelated functions.
- Keep changes focused.
- Preserve backward compatibility whenever possible.
- Explain all code changes.
- Avoid duplicated logic.
- Write readable and maintainable code.
- Prefer simple solutions.
- Avoid introducing unnecessary dependencies.
- Test changes before committing.

---

# 13. Performance Goals

The application should:

- search many sources efficiently
- minimize duplicate requests
- cache where appropriate
- remain responsive
- support future parallel scraping
- scale to thousands of jobs

---

# 14. Future Roadmap

Future versions may include:

- AI semantic job matching
- Resume matching
- CV scoring
- Cover letter generation
- Salary estimation
- Employer reputation scoring
- Interview difficulty estimation
- Saved searches
- User accounts
- Daily email alerts
- Job recommendation engine
- Dashboard analytics
- Historical trends

---

# 15. Things That Must Not Change Without Explicit Approval

Do not:

- remove existing job sources
- reduce supported countries
- change scoring philosophy
- replace working scrapers unnecessarily
- modify unrelated code
- remove existing features
- simplify matching at the expense of accuracy

Large architectural changes should always be discussed before implementation.