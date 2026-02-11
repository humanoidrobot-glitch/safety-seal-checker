# Safety Seal Checker — Claude Code Build Prompt

## Project Overview

Build a consumer-facing web application called **SealCheck** (or similar) that helps users determine whether a product they purchased should have a tamper-evident safety seal, what type of seal to expect, and what to do if it's missing or broken.

This is an MVP. Keep it lean, functional, and shippable. We can iterate later.

---

## Tech Stack

- **Frontend:** React (Vite) with Tailwind CSS
- **Backend:** FastAPI (Python)
- **Database:** PostgreSQL
- **Deployment-ready:** Dockerized, ready for VPS or cloud deployment

---

## Core Features (MVP)

### 1. Product Category Search & Checker

The main feature. User flow:

1. User lands on homepage with a prominent search bar: *"Does your product need a safety seal?"*
2. User types a product name or selects from category browse (e.g., "Tylenol", "eye drops", "mouthwash", "baby formula")
3. App matches input to a **product category** in our database
4. Results page shows:
   - ✅ or ❌ whether this category requires tamper-evident packaging
   - **What regulation requires it** (e.g., "21 CFR 211.132 — OTC Drugs")
   - **What type of seal to look for** (shrink band, foil inner seal, breakable cap, sealed wrapper, etc.)
   - **Visual example** of what a proper seal looks like for this category
   - **What to do** if the seal is missing or broken (don't use it, return it, report to FDA/retailer)

### 2. Category Browser

A browsable, filterable grid/list of all product categories:

- OTC Medications (oral, topical, nasal, ophthalmic)
- Contact Lens Solutions
- Food Products (specific categories requiring seals)
- Cosmetics & Skincare
- Baby Formula & Baby Food
- Dietary Supplements
- Dental/Oral Care Products
- Vaginal Products

Each category card links to a detail page with full regulatory info.

### 3. "Report a Problem" Form

Simple form where users can report a product they found without a proper seal:

- Product name, brand, UPC/barcode (optional)
- Where purchased (store name, location)
- Photo upload (optional)
- Description of the issue
- Store in database for future crowdsourced data

### 4. Educational Content Section

Static pages (rendered from markdown or stored in DB):

- "What is a Safety Seal?" — history (1982 Tylenol poisonings), why they matter
- "Types of Tamper-Evident Packaging" — visual guide
- "Your Rights as a Consumer" — what to do, who to contact
- "FAQ"

---

## Database Schema

### `product_categories` table
```
id: UUID (PK)
name: VARCHAR — e.g., "OTC Oral Medications"
slug: VARCHAR (unique, indexed) — e.g., "otc-oral-medications"
description: TEXT
requires_seal: BOOLEAN
regulation_code: VARCHAR — e.g., "21 CFR 211.132"
regulation_name: VARCHAR — e.g., "Tamper-Evident Packaging Requirements for OTC Human Drug Products"
regulation_summary: TEXT
seal_types: JSONB — e.g., ["foil_inner_seal", "shrink_band", "breakable_cap"]
seal_description: TEXT — human-readable description of expected seals
what_to_do: TEXT — instructions if seal is missing/broken
parent_category_id: UUID (FK, nullable) — for subcategories
created_at: TIMESTAMP
updated_at: TIMESTAMP
```

### `product_keywords` table (for search matching)
```
id: UUID (PK)
category_id: UUID (FK → product_categories)
keyword: VARCHAR (indexed) — e.g., "tylenol", "ibuprofen", "advil", "eye drops"
```

### `seal_types` table
```
id: UUID (PK)
name: VARCHAR — e.g., "Foil Inner Seal"
slug: VARCHAR
description: TEXT
image_url: VARCHAR (nullable)
```

### `reports` table
```
id: UUID (PK)
product_name: VARCHAR
brand: VARCHAR (nullable)
upc: VARCHAR (nullable)
store_name: VARCHAR (nullable)
store_location: VARCHAR (nullable)
description: TEXT
photo_url: VARCHAR (nullable)
email: VARCHAR (nullable) — for follow-up
status: VARCHAR — "pending", "reviewed", "verified"
created_at: TIMESTAMP
```

### `articles` table (for educational content)
```
id: UUID (PK)
title: VARCHAR
slug: VARCHAR (unique)
content: TEXT (markdown)
meta_description: VARCHAR
published: BOOLEAN
created_at: TIMESTAMP
updated_at: TIMESTAMP
```

---

## Regulatory Data to Seed

This is the core value of the site. Seed the database with the following regulatory frameworks:

### Federal Regulations Requiring Tamper-Evident Packaging

1. **21 CFR 211.132** — OTC human drug products (the big one)
   - Covers: all OTC drugs for oral, nasal, rectal, ophthalmic, or vaginal use
   - Exemptions: dermatological products, insulin, throat lozenges in individually sealed packages

2. **21 CFR 700.25** — Cosmetic products
   - Covers: liquid oral hygiene (mouthwash), vaginal products, cosmetic skin products marketed with drug claims

3. **FDA Food Safety Modernization Act (FSMA)**
   - Covers: certain food products, especially baby formula (21 CFR 107), dietary supplements

4. **Poison Prevention Packaging Act (PPPA) — 16 CFR 1700**
   - Related but distinct: child-resistant packaging (overlaps with tamper-evident in many products)

5. **Federal Anti-Tampering Act (18 U.S.C. § 1365)**
   - Criminal penalties for tampering — background context for educational content

### Product Categories to Seed (with keywords)

Create entries for at least these categories with 10-20 keywords each:

- OTC Pain Relievers (aspirin, tylenol, advil, ibuprofen, acetaminophen, naproxen, aleve...)
- OTC Cold & Flu (dayquil, nyquil, mucinex, robitussin, theraflu...)
- OTC Allergy (zyrtec, claritin, allegra, benadryl, antihistamine...)
- OTC Digestive (pepto bismol, tums, prilosec, omeprazole, pepcid, laxative...)
- Eye Drops & Solutions (visine, systane, refresh, clear eyes...)
- Contact Lens Solutions (biotrue, opti-free, renu, saline solution...)
- Nasal Sprays (afrin, flonase, nasacort, neti pot solution...)
- Mouthwash & Oral Rinse (listerine, scope, crest, act fluoride...)
- Baby Formula (enfamil, similac, gerber, earth's best...)
- Dietary Supplements (vitamins, fish oil, probiotics, protein powder...)
- Topical Antiseptics (hydrogen peroxide, rubbing alcohol, neosporin...)
- Vaginal Products (monistat, vagisil...)
- First Aid Products (bandages — note: some exempt)

---

## API Endpoints

```
GET  /api/search?q={query}           — Search categories by keyword, return matches
GET  /api/categories                  — List all categories (with optional parent filter)
GET  /api/categories/{slug}           — Get full category detail
GET  /api/seal-types                  — List all seal types
POST /api/reports                     — Submit a problem report
GET  /api/articles                    — List published articles
GET  /api/articles/{slug}             — Get article detail
```

---

## Frontend Pages & Routes

```
/                        — Homepage with search bar, featured categories, hero section
/search?q={query}        — Search results page
/category/{slug}         — Category detail page (the main "answer" page)
/categories              — Browse all categories
/report                  — Report a problem form
/learn                   — Educational content hub
/learn/{slug}            — Individual article page
/about                   — About the project
```

---

## Design & UX Guidelines

- **Clean, trustworthy, authoritative** — think Consumer Reports meets government resource
- Color palette: Blues, whites, greens (trust, safety, health)
- Big, clear typography — this is for everyday consumers, not developers
- Mobile-first responsive design
- The search bar is the hero — make it prominent and inviting
- Category cards should have clear iconography
- The "answer" page (category detail) should feel definitive and reassuring
- Use green checkmarks ✅ and red warnings ⚠️ for visual clarity
- Include a visible disclaimer: "This site is for informational purposes. Always follow manufacturer guidelines and consult official FDA resources for authoritative guidance."

---

## SEO Considerations

- Each category page should have unique meta titles/descriptions targeting searches like:
  - "does [product] need a safety seal"
  - "should [product] have a tamper seal"
  - "[product] missing safety seal what to do"
- Educational articles target informational queries
- Structured data (FAQ schema, HowTo schema) where applicable
- Fast page loads, proper heading hierarchy, semantic HTML

---

## Future Enhancements (NOT for MVP, but design with these in mind)

- **Barcode scanner** — mobile camera UPC scan → auto-lookup category
- **User accounts** — track reports, save products
- **Crowdsourced verification** — community confirms/flags products
- **API for third parties** — let other apps query our data
- **Manufacturer directory** — link to official product safety pages
- **Push notifications** — alerts for FDA recalls related to packaging

---

## Build Order — Phased with Subagents

This project should be built in distinct phases. **Use subagents (via `Task(...)` or the `/task` slash command) to parallelize work within each phase.** Subagents are independent Claude Code instances that can work on isolated pieces simultaneously. Use them aggressively — they're cheap and fast.

### General Subagent Rules

- **Each subagent should have a clear, scoped task** with defined inputs and outputs
- **Subagents should not depend on each other's work within the same phase** — design tasks so they can run in parallel
- **The main agent (you) orchestrates:** kick off subagents, review their output, integrate, then move to the next phase
- **Each subagent task description should include:** what files to create/modify, what the expected output is, and any constraints or patterns to follow
- **After each phase, the main agent should review all output** before proceeding — run tests, verify files exist, check for consistency

---

### Phase 0: Automated Regulatory Data Scraping & Seed Generation

**This is the most critical phase.** Before writing any app code, we need to scrape and compile the regulatory data that powers the entire site. Do NOT manually write seed data — scrape it from authoritative sources and structure it programmatically.

#### Subagent 0A: Scrape FDA CFR Regulations

**Task:** Scrape the tamper-evident packaging regulations from the FDA/eCFR and extract structured data.

**Sources to scrape (use `curl`, `wget`, or Python `requests` + `BeautifulSoup`):**

1. **21 CFR 211.132** — Tamper-evident packaging for OTC drugs
   - URL: `https://www.ecfr.gov/current/title-21/chapter-I/subchapter-C/part-211/subpart-G/section-211.132`
   
2. **21 CFR 700.25** — Tamper-resistant packaging for cosmetics
   - URL: `https://www.ecfr.gov/current/title-21/chapter-I/subchapter-G/part-700/subpart-B/section-700.25`

3. **21 CFR 107** — Infant formula (packaging requirements)
   - URL: `https://www.ecfr.gov/current/title-21/chapter-I/subchapter-B/part-107`

4. **16 CFR 1700** — Poison Prevention Packaging Act (child-resistant + tamper-evident overlap)
   - URL: `https://www.ecfr.gov/current/title-16/chapter-II/subchapter-E/part-1700`

5. **FDA Compliance Policy Guides** — Section 450.500 (tamper-evident packaging guidance)
   - Search and scrape from: `https://www.fda.gov/regulatory-information/search-fda-guidance-documents`

**Output:** Create a file `data/regulations.json` with this structure:
```json
[
  {
    "code": "21 CFR 211.132",
    "title": "Tamper-Evident Packaging Requirements for OTC Human Drug Products",
    "full_text": "...(scraped text)...",
    "summary": "...(generate a plain-English 2-3 sentence summary)...",
    "applies_to": ["otc_oral", "otc_nasal", "otc_ophthalmic", "otc_rectal", "otc_vaginal"],
    "exemptions": ["dermatological", "insulin", "individually_wrapped_lozenges"],
    "source_url": "https://..."
  }
]
```

**Instructions:**
- Use `requests` + `BeautifulSoup` to fetch and parse the eCFR pages
- The eCFR site renders regulation text in structured HTML — extract the actual regulation text
- If a page blocks scraping, fall back to using the eCFR API: `https://www.ecfr.gov/api/versioner/v1/full/{date}/title-{num}.xml`
- Generate plain-English summaries of each regulation section (use your own understanding — you know these regulations)
- Save raw scraped HTML as backup files in `data/raw/` for reference

#### Subagent 0B: Scrape Product Category Data from FDA

**Task:** Build the product category taxonomy with real product examples and keywords by scraping FDA product databases.

**Sources to scrape:**

1. **FDA NDC (National Drug Code) Directory** — for OTC drug product names and categories
   - API: `https://api.fda.gov/drug/ndc.json?search=marketing_category:"OTC"&limit=1000`
   - Use the openFDA API to pull OTC product names, brand names, and categories
   
2. **FDA Product Classification Database** — cosmetics and other products
   - URL: `https://www.fda.gov/industry/regulated-products/product-classification-databases`

3. **openFDA Drug Label API** — for product descriptions and usage categories
   - API: `https://api.fda.gov/drug/label.json?search=openfda.product_type:"OTC"&limit=100`
   - Extract: brand names, generic names, product categories, routes of administration

4. **Dietary Supplement Label Database**
   - URL: `https://dsld.od.nih.gov/`
   - Scrape common supplement brand names for keyword mapping

**Output:** Create `data/categories.json`:
```json
[
  {
    "name": "OTC Oral Pain Relievers",
    "slug": "otc-oral-pain-relievers",
    "description": "Over-the-counter medications taken by mouth for pain relief...",
    "requires_seal": true,
    "regulation_code": "21 CFR 211.132",
    "seal_types": ["foil_inner_seal", "shrink_band", "breakable_cap"],
    "seal_description": "Look for a foil seal under the cap, a plastic shrink band around the cap...",
    "what_to_do": "Do not use the product. Return it to the retailer for a refund...",
    "keywords": ["tylenol", "advil", "ibuprofen", "acetaminophen", "aspirin", "naproxen", "aleve", "excedrin", "motrin", "bayer"],
    "parent_category": "otc-medications"
  }
]
```

**Instructions:**
- Use the openFDA API (it's free, no auth required) to pull real brand names and product names for keyword lists
- Query by route of administration to correctly categorize (oral, ophthalmic, nasal, topical, etc.)
- For each API query, paginate through results to collect comprehensive brand name lists
- Aim for 20-50 keywords per category using real product names from FDA data
- Cross-reference which regulation applies to each category based on the product type and route
- For categories where FDA APIs don't have data (like baby formula brands), use web scraping of retailer category pages (e.g., scrape product listings from public retailer category pages for brand names)

#### Subagent 0C: Scrape Seal Type Visual Data

**Task:** Build the seal types reference data with descriptions.

**Sources:**
1. **FDA Consumer Updates on tamper-evident packaging** — scrape educational content
   - Search: `https://www.fda.gov/consumers` for tamper-evident packaging articles
   
2. **CPSC tamper-resistant packaging resources**
   - URL: `https://www.cpsc.gov/`

**Output:** Create `data/seal_types.json`:
```json
[
  {
    "name": "Foil Inner Seal",
    "slug": "foil-inner-seal",
    "description": "A thin metallic foil sealed to the opening of the container beneath the cap. Must be intact and fully adhered — any peeling, puncture, or absence means the product may have been tampered with.",
    "common_products": ["pill bottles", "liquid medications", "supplements"]
  },
  {
    "name": "Shrink Band",
    "slug": "shrink-band",
    "description": "A plastic band that wraps around the cap and container neck. It must be unbroken and tight. A missing, loose, or torn shrink band indicates possible tampering.",
    "common_products": ["beverages", "sauces", "mouthwash"]
  }
]
```

Define at least these seal types: Foil Inner Seal, Shrink Band/Wrapper, Breakable Cap, Film Wrapper, Sealed Blister Pack, Vacuum Button (jar lids), Tape Seal, Sealed Sachets/Pouches, Glued Carton Flaps.

#### Subagent 0D: Generate Educational Article Content

**Task:** Generate the seed educational articles for the `/learn` section.

**Output:** Create individual markdown files in `data/articles/`:
- `data/articles/what-is-a-safety-seal.md`
- `data/articles/types-of-tamper-evident-packaging.md`
- `data/articles/your-rights-as-a-consumer.md`
- `data/articles/history-of-tamper-evident-packaging.md`
- `data/articles/how-to-report-tampering.md`
- `data/articles/faq.md`

Each file should have YAML frontmatter:
```yaml
---
title: "What is a Safety Seal?"
slug: "what-is-a-safety-seal"
meta_description: "Learn what safety seals are, why they exist, and how they protect consumers from product tampering."
---
```

**Instructions:**
- Write comprehensive, consumer-friendly content (800-1500 words per article)
- Reference the actual regulations scraped in Subagent 0A
- Include the 1982 Tylenol poisoning history as foundational context
- FAQ should cover the 15-20 most common consumer questions about safety seals
- Tone: helpful, empowering, authoritative but accessible

#### Phase 0 Integration (Main Agent)

After all Phase 0 subagents complete:
1. Review all JSON files for consistency and accuracy
2. Cross-reference: every category in `categories.json` should reference a valid regulation in `regulations.json`
3. Cross-reference: every seal type referenced in categories should exist in `seal_types.json`
4. Create the master seed script: `scripts/seed_database.py` that reads all JSON files and populates PostgreSQL
5. Run the seed script and verify data integrity with spot-check queries

---

### Phase 1: Database & Backend API

#### Subagent 1A: Database Setup

**Task:** Set up PostgreSQL schema and migrations.
- Create all tables from the Database Schema section above
- Use Alembic for migrations
- Create `scripts/seed_database.py` that reads from `data/*.json` and populates all tables
- Include indexes on: `product_keywords.keyword`, `product_categories.slug`, `articles.slug`
- Add full-text search index on `product_keywords.keyword` and `product_categories.name`

#### Subagent 1B: FastAPI Application Shell

**Task:** Build the FastAPI backend with all endpoints.
- Set up project structure: `app/`, `app/routers/`, `app/models/`, `app/schemas/`, `app/database.py`
- Implement all API endpoints from the API Endpoints section
- The search endpoint (`/api/search`) should use PostgreSQL `ILIKE` or full-text search to match keywords and category names
- Search should return results ranked by relevance (exact match > partial match > fuzzy)
- Include CORS middleware for frontend development
- Add request validation with Pydantic schemas
- Include basic error handling and 404s

#### Phase 1 Integration (Main Agent)
1. Wire up database connection
2. Run seed script
3. Test all endpoints with curl
4. Verify search returns accurate results for test queries: "tylenol", "eye drops", "baby formula", "mouthwash"

---

### Phase 2: Frontend Application

#### Subagent 2A: React App Shell & Layout

**Task:** Scaffold the React app with routing, layout, and shared components.
- Use Vite + React + Tailwind CSS
- Set up React Router with all routes from the Frontend Pages section
- Create layout: header (logo + nav), footer (disclaimer + links), main content area
- Create shared components: SearchBar, CategoryCard, LoadingSpinner, ErrorState
- Mobile-first responsive layout
- Color palette: primary blue (#1e40af), secondary green (#059669), warm white backgrounds, dark text
- Include the legal disclaimer in the footer on every page

#### Subagent 2B: Homepage & Search

**Task:** Build the homepage and search results page.
- Hero section with large search bar: "Does your product need a safety seal?"
- Quick-access category grid below the hero (top 6-8 categories as cards with icons)
- Search bar connects to `/api/search` with debounced input
- Search results page shows matched categories as cards with ✅/❌ seal status
- Handle: no results, loading state, error state
- Auto-suggest/autocomplete dropdown as user types (optional enhancement)

#### Subagent 2C: Category Detail & Browse Pages

**Task:** Build the category detail page (the core "answer" page) and category browser.
- Category detail page (`/category/{slug}`):
  - Large header with category name and ✅/⚠️ status
  - "This product requires tamper-evident packaging" or "This product may not require..." banner
  - Regulation info section (code, name, plain-English summary)
  - "What to look for" section — lists expected seal types with descriptions
  - "What to do if the seal is missing" section — actionable steps
  - Related categories sidebar/section
  - Link to source regulation
- Category browser (`/categories`):
  - Filterable grid of all categories
  - Filter by: requires seal (yes/no), parent category
  - Search within categories

#### Subagent 2D: Report Form, Educational Pages & SEO

**Task:** Build remaining pages.
- Report form (`/report`):
  - Clean form with fields matching the `reports` table schema
  - Client-side validation
  - Success confirmation message after submission
  - Optional photo upload (store as URL or base64 for MVP)
- Educational hub (`/learn`):
  - Article listing page with cards
  - Individual article pages rendering markdown content
  - Clean reading typography
- About page
- SEO:
  - React Helmet (or equivalent) for dynamic meta tags on every page
  - Each category page: `<title>Does [Category] Need a Safety Seal? | SealCheck</title>`
  - Open Graph tags for social sharing
  - Semantic HTML throughout (proper heading hierarchy, landmarks, alt text)

#### Phase 2 Integration (Main Agent)
1. Connect all frontend pages to backend API
2. Test complete user flows: search → results → detail page
3. Test report submission flow
4. Responsive testing at mobile, tablet, desktop breakpoints
5. Verify all links and routes work
6. Check that educational articles render correctly

---

### Phase 3: Polish & Deploy

#### Subagent 3A: Docker & Deployment Config

**Task:** Dockerize the full stack.
- `Dockerfile` for FastAPI backend
- `Dockerfile` for React frontend (multi-stage build with nginx)
- `docker-compose.yml` with: backend, frontend, postgres, (optional: nginx reverse proxy)
- Environment variable configuration (.env template)
- Health check endpoints
- Database initialization on first run (auto-migrate + seed)

#### Subagent 3B: Final Polish

**Task:** QA pass and finishing touches.
- Loading skeletons/spinners on all async pages
- 404 page
- Error boundaries in React
- Accessibility pass: keyboard navigation, screen reader labels, contrast ratios
- Performance: lazy load images, code split routes
- Favicon and basic branding
- Sitemap.xml generation
- robots.txt

---

## Important Notes

- All regulatory information should be accurate as of current FDA/CPSC guidelines — **scrape from official sources, don't make it up**
- Include clear disclaimers that this is informational, not legal or medical advice
- The tone should be helpful and empowering, not scary — "here's what to look for" not "everything is dangerous"
- Prioritize fast search results — users want a quick answer
- Keep the codebase clean and well-commented for future iteration
- When scraping, respect rate limits — add 1-2 second delays between requests
- If any scraping source blocks requests, fall back to publicly available API endpoints or cached copies
- Store all raw scraped data in `data/raw/` for auditability
