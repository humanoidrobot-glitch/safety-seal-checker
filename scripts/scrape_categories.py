#!/usr/bin/env python3
"""
scrape_categories.py - Build product category taxonomy with real product names
by querying openFDA APIs.

Queries:
  - openFDA Drug NDC API (OTC monograph products)
  - openFDA Drug Label API (OTC labels by route of administration)

Outputs:
  - data/categories.json           (final taxonomy)
  - data/raw/fda_ndc_otc_*.json    (raw NDC responses)
  - data/raw/fda_label_*.json      (raw label responses)
"""

import json
import os
import re
import time
import requests
from pathlib import Path
from collections import defaultdict

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"

RAW_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# FDA API helpers
# ---------------------------------------------------------------------------
BASE_NDC = "https://api.fda.gov/drug/ndc.json"
BASE_LABEL = "https://api.fda.gov/drug/label.json"

DELAY = 1.0  # seconds between requests


def fda_get(url, params, label=""):
    """Issue a GET to openFDA; return parsed JSON or None on error."""
    print(f"  [API] {label or url}  params={params}")
    try:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.HTTPError as exc:
        print(f"    HTTP error: {exc}")
        return None
    except Exception as exc:
        print(f"    Error: {exc}")
        return None


def save_raw(data, filename):
    """Persist raw API response to data/raw/."""
    path = RAW_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"    -> saved {path}")


def extract_brand_names_ndc(results):
    """Pull brand_name / proprietary_name from NDC results."""
    names = set()
    for item in results:
        for key in ("brand_name", "proprietary_name"):
            val = item.get(key)
            if val:
                names.add(val.strip())
        # also grab generic_name
        gn = item.get("generic_name")
        if gn:
            names.add(gn.strip())
    return names


def extract_brand_names_label(results):
    """Pull brand names and generic names from Label results."""
    names = set()
    for item in results:
        openfda = item.get("openfda", {})
        for key in ("brand_name", "generic_name"):
            vals = openfda.get(key, [])
            if isinstance(vals, list):
                for v in vals:
                    names.add(v.strip())
            elif isinstance(vals, str):
                names.add(vals.strip())
    return names


# ---------------------------------------------------------------------------
# Query functions
# ---------------------------------------------------------------------------

def query_ndc_otc(skip=0, limit=100, extra_search=""):
    """Query NDC API for OTC monograph products."""
    search = 'marketing_category:"OTC MONOGRAPH FINAL"'
    if extra_search:
        search += f" AND {extra_search}"
    params = {"search": search, "limit": limit, "skip": skip}
    return fda_get(BASE_NDC, params, label=f"NDC OTC skip={skip}")


def query_ndc_otc_not_final(skip=0, limit=100, extra_search=""):
    search = 'marketing_category:"OTC MONOGRAPH NOT FINAL"'
    if extra_search:
        search += f" AND {extra_search}"
    params = {"search": search, "limit": limit, "skip": skip}
    return fda_get(BASE_NDC, params, label=f"NDC OTC-NF skip={skip}")


def query_label_by_route(route, skip=0, limit=100):
    """Query Label API for OTC products by route of administration."""
    search = f'openfda.route:"{route}" AND openfda.product_type:"OTC"'
    params = {"search": search, "limit": limit, "skip": skip}
    return fda_get(BASE_LABEL, params, label=f"Label route={route} skip={skip}")


def query_label_general_otc(skip=0, limit=100):
    search = 'openfda.product_type:"OTC"'
    params = {"search": search, "limit": limit, "skip": skip}
    return fda_get(BASE_LABEL, params, label=f"Label OTC skip={skip}")


def paginate_label_route(route, max_pages=5, limit=100):
    """Paginate through Label API for a given route, return all brand names."""
    all_names = set()
    all_results = []
    for page in range(max_pages):
        skip = page * limit
        data = query_label_by_route(route, skip=skip, limit=limit)
        time.sleep(DELAY)
        if data is None:
            break
        results = data.get("results", [])
        if not results:
            break
        all_results.extend(results)
        names = extract_brand_names_label(results)
        all_names.update(names)
        total = data.get("meta", {}).get("results", {}).get("total", 0)
        if skip + limit >= total:
            break
    return all_names, all_results


def paginate_ndc(query_fn, max_pages=5, limit=100):
    """Paginate through NDC API, return all brand names."""
    all_names = set()
    all_results = []
    for page in range(max_pages):
        skip = page * limit
        data = query_fn(skip=skip, limit=limit)
        time.sleep(DELAY)
        if data is None:
            break
        results = data.get("results", [])
        if not results:
            break
        all_results.extend(results)
        names = extract_brand_names_ndc(results)
        all_names.update(names)
        total = data.get("meta", {}).get("results", {}).get("total", 0)
        if skip + limit >= total:
            break
    return all_names, all_results


# ---------------------------------------------------------------------------
# Name-cleaning helpers
# ---------------------------------------------------------------------------

def clean_name(name):
    """Lowercase, strip dosage info, trim."""
    n = name.lower().strip()
    # remove dosage patterns like "500 mg", "200mg/5ml", etc.
    n = re.sub(r'\d+\s*(mg|ml|mcg|g|%|iu|oz|fl\.?\s*oz|grain|grams?)\b.*', '', n)
    # remove trailing punctuation / whitespace
    n = n.strip(" -–,;:/()[]")
    return n


def dedupe_keywords(raw_names):
    """Deduplicate and clean a set of raw brand/generic names; return sorted list."""
    seen = set()
    out = []
    for raw in raw_names:
        c = clean_name(raw)
        if not c or len(c) < 2:
            continue
        if c in seen:
            continue
        seen.add(c)
        out.append(c)
    return sorted(out)


# ---------------------------------------------------------------------------
# Keyword classification helpers
# ---------------------------------------------------------------------------

# Manually curated mapping of common ingredient / brand fragments to categories.
# We'll use this to filter the FDA names into the right buckets.

ORAL_PAIN_TERMS = {
    "acetaminophen", "ibuprofen", "naproxen", "aspirin", "pain reliever",
    "pain relief", "headache", "tylenol", "advil", "motrin", "aleve",
    "excedrin", "bayer", "anacin", "bufferin", "midol", "goody",
    "bc powder", "vanquish", "ecotrin", "st. joseph", "pamprin",
    "analgesic", "arthritis", "fever reducer", "fever",
}

COLD_FLU_TERMS = {
    "cold", "flu", "cough", "congestion", "dayquil", "nyquil",
    "mucinex", "robitussin", "theraflu", "delsym", "sudafed",
    "tussin", "vicks", "coricidin", "triaminic", "dimetapp",
    "guaifenesin", "dextromethorphan", "phenylephrine",
    "pseudoephedrine", "expectorant", "decongestant",
    "chest congestion", "sinus", "bronchial",
}

ALLERGY_TERMS = {
    "allergy", "antihistamine", "cetirizine", "loratadine",
    "fexofenadine", "diphenhydramine", "zyrtec", "claritin",
    "allegra", "benadryl", "xyzal", "levocetirizine",
    "hay fever", "allergies", "chlorpheniramine",
}

DIGESTIVE_TERMS = {
    "antacid", "acid reducer", "heartburn", "omeprazole", "famotidine",
    "ranitidine", "bismuth", "pepto", "tums", "prilosec", "pepcid",
    "laxative", "stool softener", "constipation", "imodium",
    "dulcolax", "miralax", "gas-x", "simethicone", "zantac",
    "maalox", "mylanta", "gaviscon", "nexium", "prevacid",
    "calcium carbonate", "magnesium hydroxide", "fiber",
    "metamucil", "benefiber", "colace", "docusate", "senokot",
    "senna", "phillips", "kaopectate", "diarrhea", "nausea",
    "digestive", "stomach", "indigestion", "bloating",
}

EYE_DROP_TERMS = {
    "eye drop", "ophthalmic", "visine", "systane", "refresh",
    "clear eyes", "rohto", "lumify", "tears", "redness relief",
    "dry eye", "artificial tears", "eye wash", "eye rinse",
    "similasan eye", "ocusoft", "genteal", "theratears",
    "ketotifen", "naphazoline", "tetrahydrozoline",
    "eye allergy", "eye itch",
}

CONTACT_LENS_TERMS = {
    "contact lens", "contact solution", "biotrue", "opti-free",
    "renu", "saline", "bausch", "lomb", "lens care",
    "multipurpose solution", "boston", "clear care",
    "puremoist", "aquify", "complete",
}

NASAL_TERMS = {
    "nasal", "nasal spray", "afrin", "flonase", "nasacort",
    "neti pot", "rhinocort", "oxymetazoline", "saline nasal",
    "sinus rinse", "neilmed", "zicam nasal", "fluticasone",
    "triamcinolone", "budesonide", "xhance",
    "nasal decongestant", "nose spray",
}

MOUTHWASH_TERMS = {
    "mouthwash", "mouth rinse", "oral rinse", "antiseptic rinse",
    "listerine", "scope", "crest", "act fluoride", "colgate",
    "therabreath", "biotene", "chlorhexidine", "cetylpyridinium",
    "fluoride rinse", "breath", "plax", "oral-b",
}

SLEEP_AID_TERMS = {
    "sleep", "sleep aid", "melatonin", "zzzquil", "unisom",
    "tylenol pm", "advil pm", "nytol", "sominex",
    "doxylamine", "diphenhydramine sleep", "nighttime sleep",
    "insomnia",
}

TOPICAL_ANTISEPTIC_TERMS = {
    "hydrogen peroxide", "rubbing alcohol", "isopropyl", "neosporin",
    "betadine", "bacitracin", "povidone-iodine", "antiseptic",
    "first aid antibiotic", "triple antibiotic", "bactine",
    "mercurochrome", "hibiclens", "chlorhexidine topical",
    "wound care", "topical antibiotic",
}

TOPICAL_GENERAL_TERMS = {
    "hydrocortisone", "calamine", "anti-itch", "cortisone",
    "bengay", "icy hot", "biofreeze", "salonpas", "lidocaine",
    "camphor", "menthol topical", "capsaicin", "gold bond",
    "lanacane", "cortizone", "caladryl",
}


def classify_name(name):
    """Return a set of category slugs that a product name might belong to."""
    n = name.lower()
    cats = set()
    for term in ORAL_PAIN_TERMS:
        if term in n:
            cats.add("otc-oral-pain-relievers")
            break
    for term in COLD_FLU_TERMS:
        if term in n:
            cats.add("otc-cold-and-flu")
            break
    for term in ALLERGY_TERMS:
        if term in n:
            cats.add("otc-allergy")
            break
    for term in DIGESTIVE_TERMS:
        if term in n:
            cats.add("otc-digestive")
            break
    for term in EYE_DROP_TERMS:
        if term in n:
            cats.add("eye-drops-and-solutions")
            break
    for term in CONTACT_LENS_TERMS:
        if term in n:
            cats.add("contact-lens-solutions")
            break
    for term in NASAL_TERMS:
        if term in n:
            cats.add("nasal-sprays")
            break
    for term in MOUTHWASH_TERMS:
        if term in n:
            cats.add("mouthwash-and-oral-rinse")
            break
    for term in SLEEP_AID_TERMS:
        if term in n:
            cats.add("otc-sleep-aids")
            break
    for term in TOPICAL_ANTISEPTIC_TERMS:
        if term in n:
            cats.add("topical-antiseptics")
            break
    for term in TOPICAL_GENERAL_TERMS:
        if term in n:
            cats.add("topical-antiseptics")  # fold into antiseptics / first-aid
            break
    return cats


# ---------------------------------------------------------------------------
# Main scraping logic
# ---------------------------------------------------------------------------

def scrape_all():
    """Run all API queries and return categorized keyword sets."""

    category_names = defaultdict(set)  # slug -> set of raw names

    # ------------------------------------------------------------------
    # 1. NDC API — OTC Monograph Final + Not Final
    # ------------------------------------------------------------------
    print("\n=== NDC OTC Monograph Final ===")
    ndc_final_names, ndc_final_results = paginate_ndc(query_ndc_otc, max_pages=5)
    save_raw(ndc_final_results, "fda_ndc_otc_final.json")

    print("\n=== NDC OTC Monograph Not Final ===")
    ndc_nf_names, ndc_nf_results = paginate_ndc(query_ndc_otc_not_final, max_pages=5)
    save_raw(ndc_nf_results, "fda_ndc_otc_not_final.json")

    all_ndc_names = ndc_final_names | ndc_nf_names
    print(f"\n  Total unique NDC names: {len(all_ndc_names)}")

    # Classify NDC names
    for name in all_ndc_names:
        cats = classify_name(name)
        for cat in cats:
            category_names[cat].add(name)

    # ------------------------------------------------------------------
    # 2. Label API — by route
    # ------------------------------------------------------------------
    routes = ["ORAL", "OPHTHALMIC", "NASAL", "TOPICAL", "RECTAL", "VAGINAL", "DENTAL"]
    route_map = {
        "ORAL": ["otc-oral-pain-relievers", "otc-cold-and-flu", "otc-allergy",
                  "otc-digestive", "otc-sleep-aids"],
        "OPHTHALMIC": ["eye-drops-and-solutions"],
        "NASAL": ["nasal-sprays"],
        "TOPICAL": ["topical-antiseptics"],
        "DENTAL": ["mouthwash-and-oral-rinse"],
        "RECTAL": ["otc-digestive"],
        "VAGINAL": ["vaginal-products"],
    }

    for route in routes:
        print(f"\n=== Label route={route} ===")
        names, results = paginate_label_route(route, max_pages=4)
        save_raw(results, f"fda_label_{route.lower()}.json")
        print(f"  Unique names for {route}: {len(names)}")

        # Try to classify each name
        for name in names:
            cats = classify_name(name)
            if cats:
                for cat in cats:
                    category_names[cat].add(name)
            else:
                # Fall back to route-based assignment
                default_cats = route_map.get(route, [])
                for cat in default_cats:
                    category_names[cat].add(name)

    # ------------------------------------------------------------------
    # 3. General OTC label query (first 3 pages)
    # ------------------------------------------------------------------
    print("\n=== Label general OTC ===")
    general_names = set()
    general_results = []
    for page in range(3):
        data = query_label_general_otc(skip=page * 100)
        time.sleep(DELAY)
        if not data:
            break
        results = data.get("results", [])
        if not results:
            break
        general_results.extend(results)
        general_names.update(extract_brand_names_label(results))
    save_raw(general_results, "fda_label_otc_general.json")

    for name in general_names:
        cats = classify_name(name)
        for cat in cats:
            category_names[cat].add(name)

    return category_names


# ---------------------------------------------------------------------------
# Supplemental well-known brand keywords (non-FDA-API sources)
# ---------------------------------------------------------------------------

SUPPLEMENTAL_KEYWORDS = {
    "otc-oral-pain-relievers": [
        "tylenol", "advil", "motrin", "aleve", "excedrin", "bayer aspirin",
        "anacin", "bufferin", "ecotrin", "midol", "pamprin", "goody's powder",
        "bc powder", "vanquish", "st. joseph aspirin", "equate pain reliever",
        "kirkland ibuprofen", "up & up acetaminophen", "cvs health ibuprofen",
        "walgreens pain reliever", "acetaminophen", "ibuprofen", "naproxen sodium",
        "aspirin", "pain reliever", "fever reducer", "headache relief",
        "arthritis pain", "back pain relief", "menstrual pain relief",
        "migraine relief", "extra strength", "rapid release",
    ],
    "otc-cold-and-flu": [
        "dayquil", "nyquil", "mucinex", "robitussin", "theraflu", "delsym",
        "sudafed", "vicks vaporub", "vicks vaposteam", "coricidin hbp",
        "triaminic", "dimetapp", "alka-seltzer plus", "contac", "dristan",
        "zicam", "oscillococcinum", "cold-eeze", "airborne",
        "emergen-c", "halls", "ricola", "cepacol", "chloraseptic",
        "equate cold and flu", "cough suppressant", "expectorant",
        "chest congestion relief", "sinus relief", "guaifenesin",
        "dextromethorphan", "phenylephrine", "pseudoephedrine",
        "nighttime cold", "daytime cold", "severe cold",
    ],
    "otc-allergy": [
        "zyrtec", "claritin", "allegra", "benadryl", "xyzal",
        "cetirizine", "loratadine", "fexofenadine", "diphenhydramine",
        "levocetirizine", "chlor-trimeton", "tavist", "drixoral",
        "alavert", "equate allergy", "cvs allergy relief",
        "kirkland allerclear", "costco allergy", "walgreens wal-zyr",
        "antihistamine", "hay fever relief", "indoor allergies",
        "outdoor allergies", "seasonal allergy", "allergy relief",
        "non-drowsy allergy", "24-hour allergy", "children's allergy",
    ],
    "otc-digestive": [
        "pepto-bismol", "tums", "prilosec otc", "pepcid ac", "imodium",
        "dulcolax", "miralax", "gas-x", "zantac", "nexium",
        "prevacid", "maalox", "mylanta", "gaviscon", "rolaids",
        "phillips milk of magnesia", "kaopectate", "metamucil",
        "benefiber", "colace", "senokot", "ex-lax", "citrucel",
        "emetrol", "dramamine", "bonine", "omeprazole",
        "famotidine", "calcium carbonate", "simethicone",
        "bismuth subsalicylate", "docusate sodium",
        "acid reducer", "heartburn relief", "antacid",
        "laxative", "stool softener", "anti-diarrheal",
        "anti-gas", "digestive aid", "stomach relief",
        "equate omeprazole", "kirkland omeprazole",
    ],
    "eye-drops-and-solutions": [
        "visine", "systane", "refresh tears", "clear eyes",
        "rohto", "lumify", "similasan", "ocusoft", "genteal",
        "theratears", "blink tears", "soothe xp", "naphcon-a",
        "opcon-a", "alaway", "zaditor", "pataday", "lastacaft",
        "artificial tears", "dry eye drops", "redness reliever",
        "eye allergy drops", "lubricant eye drops", "eye wash",
        "ketotifen eye drops", "preservative-free tears",
        "equate eye drops", "cvs eye drops",
    ],
    "contact-lens-solutions": [
        "biotrue", "opti-free", "renu", "bausch + lomb",
        "clear care", "complete", "aquify", "boston advance",
        "boston simplus", "puremoist", "revitalens",
        "saline solution", "multipurpose solution",
        "contact lens cleaner", "hydrogen peroxide solution",
        "lens rewetting drops", "contact lens case",
    ],
    "nasal-sprays": [
        "afrin", "flonase", "nasacort", "rhinocort", "neilmed",
        "zicam nasal", "oxymetazoline", "saline nasal spray",
        "arm & hammer nasal", "simply saline", "xlear",
        "ayr saline", "sinex", "neo-synephrine", "mucinex sinus",
        "fluticasone propionate", "triamcinolone acetonide",
        "budesonide nasal", "cromolyn sodium nasal",
        "nasal decongestant spray", "nasal saline rinse",
        "sinus rinse kit", "neti pot solution",
        "equate nasal spray", "cvs nasal spray",
    ],
    "mouthwash-and-oral-rinse": [
        "listerine", "scope", "crest pro-health rinse", "act fluoride rinse",
        "colgate total mouthwash", "therabreath", "biotene",
        "oral-b mouth rinse", "tom's of maine mouthwash",
        "jason mouthwash", "closys", "smartmouth",
        "cetylpyridinium chloride", "chlorhexidine rinse",
        "fluoride mouthwash", "antiseptic mouthwash",
        "whitening mouthwash", "alcohol-free mouthwash",
        "dry mouth rinse", "sensitive mouth rinse",
        "equate mouthwash", "cvs antiseptic rinse",
    ],
    "baby-formula": [
        "enfamil", "similac", "gerber good start", "earth's best organic",
        "kirkland signature formula", "up & up infant formula",
        "parents choice formula", "happy baby organic",
        "bobbie organic formula", "burt's bees baby formula",
        "enfamil neuropro", "enfamil gentlease", "enfamil a.r.",
        "similac pro-advance", "similac pro-sensitive",
        "similac alimentum", "similac 360 total care",
        "gerber good start gentlepro", "gerber good start soothe",
        "infant formula", "baby formula", "toddler formula",
        "soy formula", "hypoallergenic formula", "organic formula",
        "powder formula", "ready-to-feed formula", "liquid concentrate formula",
        "european formula", "hipp formula", "holle formula",
        "baby's only organic", "kabrita goat milk formula",
    ],
    "dietary-supplements": [
        "centrum", "nature made", "nature's bounty", "one a day",
        "garden of life", "nordic naturals", "now foods",
        "solgar", "new chapter", "megafood", "rainbow light",
        "alive!", "vitafusion", "smarty pants", "olly",
        "ritual", "care/of", "persona", "hum nutrition",
        "fish oil", "omega-3", "probiotics", "vitamin d",
        "vitamin c", "multivitamin", "calcium", "iron",
        "magnesium", "zinc", "b-complex", "b12",
        "folic acid", "biotin", "turmeric", "elderberry",
        "echinacea", "melatonin supplement", "protein powder",
        "collagen peptides", "fiber supplement", "probiotic",
        "prebiotic", "coq10", "glucosamine", "vitamin e",
        "kirkland daily multi", "equate multivitamin",
        "cvs health vitamin", "walgreens vitamin",
    ],
    "topical-antiseptics": [
        "neosporin", "betadine", "bacitracin", "bactine",
        "hydrogen peroxide", "isopropyl alcohol", "rubbing alcohol",
        "povidone-iodine", "hibiclens", "band-aid antiseptic",
        "triple antibiotic ointment", "polysporin",
        "curad antiseptic", "medi-first antiseptic",
        "benzalkonium chloride", "chlorhexidine wash",
        "wound cleanser", "antiseptic wipe", "iodine solution",
        "first aid antiseptic spray", "antiseptic hand wash",
        "equate triple antibiotic", "cvs antiseptic",
    ],
    "vaginal-products": [
        "monistat", "vagisil", "summer's eve", "rephresh",
        "replens", "vagistat", "femstat", "gyne-lotrimin",
        "azo yeast plus", "boric acid suppository",
        "miconazole vaginal", "clotrimazole vaginal",
        "tioconazole vaginal", "vaginal moisturizer",
        "vaginal wash", "feminine wash", "feminine wipes",
        "ph balance wash", "vaginal antifungal",
        "yeast infection treatment", "vaginal cream",
    ],
    "first-aid-products": [
        "band-aid", "nexcare", "curad", "ace bandage",
        "3m steri-strip", "butterfly closures", "gauze",
        "medical tape", "elastic bandage", "burn gel",
        "burn cream", "calamine lotion", "hydrocortisone cream",
        "cortisone 10", "benadryl cream", "after bite",
        "sting relief", "first aid kit", "wound care",
        "adhesive bandage", "sterile pad", "rolled gauze",
        "tegaderm", "moleskin", "liquid bandage",
        "new-skin liquid bandage", "dermabond",
    ],
    "otc-sleep-aids": [
        "zzzquil", "unisom", "tylenol pm", "advil pm",
        "nytol", "sominex", "simply sleep", "benadryl sleep",
        "melatonin", "natrol melatonin", "olly sleep",
        "vicks zzzquil", "kirkland sleep aid",
        "equate sleep aid", "cvs sleep aid",
        "doxylamine succinate", "diphenhydramine hcl",
        "nighttime sleep aid", "sleep gummies",
        "sleep tablets", "sleep caplets",
        "non-habit forming sleep aid", "natural sleep aid",
        "valerian root", "chamomile sleep",
    ],
    "cosmetics-with-drug-claims": [
        "neutrogena acne wash", "clean & clear", "proactiv",
        "differin gel", "la roche-posay effaclar",
        "cerave acne foaming cream cleanser", "panoxyl",
        "oxy acne wash", "stridex pads", "clearasil",
        "coppertone", "banana boat", "neutrogena sunscreen",
        "aveeno sunscreen", "cetaphil sunscreen",
        "eucerin sunscreen", "blue lizard", "supergoop",
        "elta md", "sun bum", "hawaiian tropic",
        "benzoyl peroxide wash", "salicylic acid cleanser",
        "medicated face wash", "acne treatment",
        "acne spot treatment", "sunscreen spf",
        "mineral sunscreen", "sport sunscreen",
        "baby sunscreen", "face sunscreen",
        "anti-dandruff shampoo", "head & shoulders",
        "nizoral", "selsun blue", "t/gel",
    ],
}


# ---------------------------------------------------------------------------
# Build final category objects
# ---------------------------------------------------------------------------

CATEGORY_DEFINITIONS = [
    # ---- Parent categories ----
    {
        "name": "OTC Medications",
        "slug": "otc-medications",
        "description": "Over-the-counter medications regulated by the FDA that require tamper-evident packaging under 21 CFR 211.132.",
        "is_parent": True,
        "requires_seal": True,
        "regulation_code": "21 CFR 211.132",
        "seal_types": [],
        "seal_description": "",
        "what_to_do": "",
        "keywords": [],
        "parent_category": None,
    },
    {
        "name": "Eye & Vision Care",
        "slug": "eye-and-vision-care",
        "description": "Products for eye health and vision correction, including medicated drops and contact lens care solutions.",
        "is_parent": True,
        "requires_seal": True,
        "regulation_code": "21 CFR 211.132",
        "seal_types": [],
        "seal_description": "",
        "what_to_do": "",
        "keywords": [],
        "parent_category": None,
    },
    {
        "name": "Oral Care",
        "slug": "oral-care",
        "description": "Products for oral hygiene including mouthwashes and rinses that may contain active drug ingredients.",
        "is_parent": True,
        "requires_seal": True,
        "regulation_code": "21 CFR 700.25",
        "seal_types": [],
        "seal_description": "",
        "what_to_do": "",
        "keywords": [],
        "parent_category": None,
    },
    {
        "name": "Baby & Infant",
        "slug": "baby-and-infant",
        "description": "Products designed for infant nutrition and care, subject to strict FDA safety requirements.",
        "is_parent": True,
        "requires_seal": True,
        "regulation_code": "21 CFR 107",
        "seal_types": [],
        "seal_description": "",
        "what_to_do": "",
        "keywords": [],
        "parent_category": None,
    },
    {
        "name": "Health & Wellness",
        "slug": "health-and-wellness",
        "description": "Dietary supplements, vitamins, and wellness products regulated under DSHEA and FSMA.",
        "is_parent": True,
        "requires_seal": True,
        "regulation_code": "DSHEA / FSMA",
        "seal_types": [],
        "seal_description": "",
        "what_to_do": "",
        "keywords": [],
        "parent_category": None,
    },
    {
        "name": "Personal Care",
        "slug": "personal-care",
        "description": "Personal care products including feminine hygiene items and cosmetics with drug claims.",
        "is_parent": True,
        "requires_seal": True,
        "regulation_code": "21 CFR 700.25",
        "seal_types": [],
        "seal_description": "",
        "what_to_do": "",
        "keywords": [],
        "parent_category": None,
    },
    {
        "name": "First Aid",
        "slug": "first-aid",
        "description": "First aid supplies and topical antiseptic products for treating minor wounds and injuries.",
        "is_parent": True,
        "requires_seal": True,
        "regulation_code": "21 CFR 211.132",
        "seal_types": [],
        "seal_description": "",
        "what_to_do": "",
        "keywords": [],
        "parent_category": None,
    },

    # ---- Child categories ----
    {
        "name": "OTC Oral Pain Relievers",
        "slug": "otc-oral-pain-relievers",
        "description": "Over-the-counter medications taken by mouth for pain relief, fever reduction, and anti-inflammatory use. Includes common analgesics such as acetaminophen, ibuprofen, naproxen, and aspirin products.",
        "is_parent": False,
        "requires_seal": True,
        "regulation_code": "21 CFR 211.132",
        "seal_types": ["foil_inner_seal", "shrink_band", "breakable_cap", "sealed_blister_pack", "film_wrapper"],
        "seal_description": "Look for a foil seal under the cap, a plastic shrink band around the cap-bottle junction, a breakable cap ring that snaps off on first opening, or sealed blister packs for individually packaged doses. Bottles may also have a film wrapper around the outside.",
        "what_to_do": "Do not use the product. Return it to the retailer for a full refund. If you suspect intentional tampering, report it to the FDA MedWatch program at 1-800-FDA-1088 and contact local law enforcement. Keep the product as evidence.",
        "keywords": [],  # filled from FDA + supplemental
        "parent_category": "otc-medications",
    },
    {
        "name": "OTC Cold & Flu",
        "slug": "otc-cold-and-flu",
        "description": "Over-the-counter medications for treating symptoms of the common cold and influenza, including cough suppressants, expectorants, decongestants, and multi-symptom relief formulas.",
        "is_parent": False,
        "requires_seal": True,
        "regulation_code": "21 CFR 211.132",
        "seal_types": ["foil_inner_seal", "shrink_band", "breakable_cap", "sealed_blister_pack", "sealed_sachet"],
        "seal_description": "Check for a foil or plastic inner seal under the cap, a shrink band around the cap-bottle junction, or sealed individual dose packets. Liquid formulas typically have a foil seal under the cap and a shrink band. Powder packets come in sealed sachets.",
        "what_to_do": "Do not use the product. Return it to the retailer for a full refund. If you suspect intentional tampering, report it to the FDA MedWatch program at 1-800-FDA-1088 and contact local law enforcement. Keep the product as evidence.",
        "keywords": [],
        "parent_category": "otc-medications",
    },
    {
        "name": "OTC Allergy",
        "slug": "otc-allergy",
        "description": "Over-the-counter antihistamines and allergy relief medications, including non-drowsy and 24-hour formulas for treating seasonal and year-round allergies.",
        "is_parent": False,
        "requires_seal": True,
        "regulation_code": "21 CFR 211.132",
        "seal_types": ["foil_inner_seal", "shrink_band", "breakable_cap", "sealed_blister_pack", "film_wrapper"],
        "seal_description": "Look for a foil seal under the cap, a shrink band around the cap-bottle junction, a breakable cap ring, or sealed blister packs. Tablets are often sold in sealed blister packs inside a cardboard carton.",
        "what_to_do": "Do not use the product. Return it to the retailer for a full refund. If you suspect intentional tampering, report it to the FDA MedWatch program at 1-800-FDA-1088 and contact local law enforcement. Keep the product as evidence.",
        "keywords": [],
        "parent_category": "otc-medications",
    },
    {
        "name": "OTC Digestive",
        "slug": "otc-digestive",
        "description": "Over-the-counter digestive health products including antacids, acid reducers, anti-diarrheals, laxatives, stool softeners, and anti-gas medications.",
        "is_parent": False,
        "requires_seal": True,
        "regulation_code": "21 CFR 211.132",
        "seal_types": ["foil_inner_seal", "shrink_band", "breakable_cap", "sealed_blister_pack", "sealed_sachet"],
        "seal_description": "Check for a foil seal under the cap, a shrink band around the bottle cap, or sealed blister packs. Chewable tablets like Tums often have a foil seal under the cap. Liquid products like Pepto-Bismol have both a shrink band and an inner seal.",
        "what_to_do": "Do not use the product. Return it to the retailer for a full refund. If you suspect intentional tampering, report it to the FDA MedWatch program at 1-800-FDA-1088 and contact local law enforcement. Keep the product as evidence.",
        "keywords": [],
        "parent_category": "otc-medications",
    },
    {
        "name": "Eye Drops & Solutions",
        "slug": "eye-drops-and-solutions",
        "description": "Over-the-counter ophthalmic products including artificial tears, redness relievers, allergy eye drops, and eye washes. These products are applied directly to the eye and require strict tamper-evident packaging.",
        "is_parent": False,
        "requires_seal": True,
        "regulation_code": "21 CFR 211.132",
        "seal_types": ["shrink_band", "breakable_cap", "tape_seal", "film_wrapper"],
        "seal_description": "Look for a shrink band or tamper-evident seal around the cap, a sealed tip that must be punctured or twisted off before first use, or a film wrapper around the entire box. Many single-use vials come in sealed foil pouches.",
        "what_to_do": "Do not use the product. Eye products are especially sensitive to contamination. Return it to the retailer for a full refund. If you suspect intentional tampering, report it to the FDA MedWatch program at 1-800-FDA-1088 and contact local law enforcement.",
        "keywords": [],
        "parent_category": "eye-and-vision-care",
    },
    {
        "name": "Contact Lens Solutions",
        "slug": "contact-lens-solutions",
        "description": "Multipurpose solutions, saline solutions, and hydrogen peroxide-based systems for cleaning, disinfecting, and storing contact lenses.",
        "is_parent": False,
        "requires_seal": True,
        "regulation_code": "21 CFR 211.132",
        "seal_types": ["shrink_band", "breakable_cap", "foil_inner_seal", "film_wrapper"],
        "seal_description": "Check for a shrink band around the cap, a breakable cap ring, or a foil seal under the cap. The bottle tip should be sealed and require piercing before first use. The outer carton may have sealed flaps.",
        "what_to_do": "Do not use the product. Contact lens solutions must remain sterile. Return it to the retailer for a full refund. If you suspect intentional tampering, report it to the FDA MedWatch program at 1-800-FDA-1088 and contact local law enforcement.",
        "keywords": [],
        "parent_category": "eye-and-vision-care",
    },
    {
        "name": "Nasal Sprays",
        "slug": "nasal-sprays",
        "description": "Over-the-counter nasal sprays and rinses including decongestant sprays, steroid nasal sprays for allergies, and saline rinse solutions.",
        "is_parent": False,
        "requires_seal": True,
        "regulation_code": "21 CFR 211.132",
        "seal_types": ["shrink_band", "breakable_cap", "tape_seal", "film_wrapper"],
        "seal_description": "Look for a shrink band around the cap or nozzle, a breakable safety clip, or a sealed box with glued flaps. The spray nozzle tip may have a protective cover that must be removed before first use.",
        "what_to_do": "Do not use the product. Return it to the retailer for a full refund. If you suspect intentional tampering, report it to the FDA MedWatch program at 1-800-FDA-1088 and contact local law enforcement. Keep the product as evidence.",
        "keywords": [],
        "parent_category": "otc-medications",
    },
    {
        "name": "Mouthwash & Oral Rinse",
        "slug": "mouthwash-and-oral-rinse",
        "description": "Mouthwashes and oral rinses including antiseptic, fluoride, and therapeutic formulas. Products containing active drug ingredients (e.g., cetylpyridinium chloride, fluoride) are regulated as OTC drugs or cosmetics with drug claims.",
        "is_parent": False,
        "requires_seal": True,
        "regulation_code": "21 CFR 700.25",
        "seal_types": ["shrink_band", "breakable_cap", "foil_inner_seal", "film_wrapper"],
        "seal_description": "Check for a shrink band around the cap-bottle junction, a breakable cap ring that snaps on first opening, or a foil inner seal under the cap. The product should show clear evidence of first-opening indicators.",
        "what_to_do": "Do not use the product. Return it to the retailer for a full refund. If the product appears to have been opened or tampered with, report it to the FDA at 1-800-FDA-1088 or your local consumer protection agency.",
        "keywords": [],
        "parent_category": "oral-care",
    },
    {
        "name": "Baby Formula",
        "slug": "baby-formula",
        "description": "Infant formula products including powder, liquid concentrate, and ready-to-feed formulations. Baby formula is subject to the most stringent tamper-evident packaging requirements under 21 CFR 107.",
        "is_parent": False,
        "requires_seal": True,
        "regulation_code": "21 CFR 107",
        "seal_types": ["foil_inner_seal", "vacuum_button", "shrink_band", "glued_carton_flaps", "film_wrapper"],
        "seal_description": "Powder canisters should have a foil inner seal under the lid. Ready-to-feed bottles have a sealed cap and may have a vacuum-sealed pop button on the lid. Liquid concentrate cans are vacuum sealed. Cartons should have intact, sealed flaps.",
        "what_to_do": "Do NOT use the product. Baby formula tampering is extremely dangerous. Return it to the retailer immediately. Report suspected tampering to the FDA at 1-800-FDA-1088 AND local law enforcement. Seek medical attention if any formula with a broken seal was already fed to an infant.",
        "keywords": [],
        "parent_category": "baby-and-infant",
    },
    {
        "name": "Dietary Supplements",
        "slug": "dietary-supplements",
        "description": "Vitamins, minerals, herbal products, amino acids, probiotics, and other dietary supplement products. Regulated under DSHEA (Dietary Supplement Health and Education Act) and FSMA (Food Safety Modernization Act).",
        "is_parent": False,
        "requires_seal": True,
        "regulation_code": "DSHEA / FSMA",
        "seal_types": ["foil_inner_seal", "shrink_band", "breakable_cap", "sealed_blister_pack", "sealed_sachet"],
        "seal_description": "Look for a foil seal under the cap (most common), a shrink band around the cap-bottle junction, or a sealed cotton plug inside the bottle. Softgels and capsules often have a foil inner seal. Individual packets come in sealed sachets.",
        "what_to_do": "Do not use the product. Return it to the retailer for a full refund. If you suspect intentional tampering, report it to the FDA MedWatch program at 1-800-FDA-1088 and contact local law enforcement.",
        "keywords": [],
        "parent_category": "health-and-wellness",
    },
    {
        "name": "Topical Antiseptics",
        "slug": "topical-antiseptics",
        "description": "Topical antiseptic products for cleaning and disinfecting minor cuts, scrapes, and burns. Includes hydrogen peroxide, rubbing alcohol, antibiotic ointments, and antiseptic sprays.",
        "is_parent": False,
        "requires_seal": True,
        "regulation_code": "21 CFR 211.132",
        "seal_types": ["foil_inner_seal", "shrink_band", "breakable_cap", "tape_seal"],
        "seal_description": "Check for a foil seal under the cap, a shrink band around the cap-bottle junction, or a sealed tube tip that must be punctured before first use. Ointment tubes typically have a sealed tip covered by the cap.",
        "what_to_do": "Do not use the product. Return it to the retailer for a full refund. If you suspect intentional tampering, report it to the FDA MedWatch program at 1-800-FDA-1088 and contact local law enforcement.",
        "keywords": [],
        "parent_category": "first-aid",
    },
    {
        "name": "Vaginal Products",
        "slug": "vaginal-products",
        "description": "Over-the-counter vaginal health products including antifungal treatments, moisturizers, and feminine hygiene washes. Drug products are regulated under 21 CFR 211.132; cosmetic products under 21 CFR 700.25.",
        "is_parent": False,
        "requires_seal": True,
        "regulation_code": "21 CFR 211.132 / 21 CFR 700.25",
        "seal_types": ["foil_inner_seal", "shrink_band", "sealed_blister_pack", "film_wrapper", "glued_carton_flaps"],
        "seal_description": "Look for sealed individual applicators in blister packs, a shrink band around the tube cap, sealed carton flaps, or a foil inner seal under the cap of wash/rinse products.",
        "what_to_do": "Do not use the product. Return it to the retailer for a full refund. If you suspect intentional tampering, report it to the FDA MedWatch program at 1-800-FDA-1088 and contact local law enforcement.",
        "keywords": [],
        "parent_category": "personal-care",
    },
    {
        "name": "First Aid Products",
        "slug": "first-aid-products",
        "description": "General first aid supplies including adhesive bandages, gauze, medical tape, burn treatments, and anti-itch creams. Note: some basic first aid supplies like plain bandages may be exempt from tamper-evident requirements, but medicated products are not.",
        "is_parent": False,
        "requires_seal": True,
        "regulation_code": "21 CFR 211.132",
        "seal_types": ["film_wrapper", "sealed_blister_pack", "shrink_band", "tape_seal", "glued_carton_flaps"],
        "seal_description": "Look for individually sealed sterile packages, a sealed outer wrapper, sealed blister packs, or intact sealed carton flaps. Sterile products should have sealed pouches that indicate if they have been opened.",
        "what_to_do": "Do not use the product if any sterile packaging appears compromised. Return it to the retailer for a refund. For medicated first aid products with broken seals, report to the FDA MedWatch program at 1-800-FDA-1088.",
        "keywords": [],
        "parent_category": "first-aid",
    },
    {
        "name": "OTC Sleep Aids",
        "slug": "otc-sleep-aids",
        "description": "Over-the-counter sleep aids including antihistamine-based products (diphenhydramine, doxylamine) and melatonin supplements to help with occasional sleeplessness.",
        "is_parent": False,
        "requires_seal": True,
        "regulation_code": "21 CFR 211.132",
        "seal_types": ["foil_inner_seal", "shrink_band", "breakable_cap", "sealed_blister_pack"],
        "seal_description": "Look for a foil seal under the cap, a plastic shrink band around the cap-bottle junction, or sealed blister packs. Liquid sleep aids (like ZzzQuil) have a foil seal under the cap and a shrink band.",
        "what_to_do": "Do not use the product. Return it to the retailer for a full refund. If you suspect intentional tampering, report it to the FDA MedWatch program at 1-800-FDA-1088 and contact local law enforcement.",
        "keywords": [],
        "parent_category": "otc-medications",
    },
    {
        "name": "Cosmetics with Drug Claims",
        "slug": "cosmetics-with-drug-claims",
        "description": "Personal care products that make therapeutic claims, including medicated acne washes, sunscreens with SPF ratings, and anti-dandruff shampoos. These are regulated as both cosmetics and drugs.",
        "is_parent": False,
        "requires_seal": True,
        "regulation_code": "21 CFR 700.25 / 21 CFR 211.132",
        "seal_types": ["shrink_band", "foil_inner_seal", "tape_seal", "film_wrapper", "glued_carton_flaps"],
        "seal_description": "Check for a shrink band around the cap, a foil seal under the cap or pump, sealed carton flaps, or a protective film wrapper. Tubes may have a sealed tip that must be punctured. Sunscreens often have a foil inner seal.",
        "what_to_do": "Do not use the product. Return it to the retailer for a full refund. If you suspect intentional tampering, report it to the FDA at 1-800-FDA-1088 or contact your local consumer protection agency.",
        "keywords": [],
        "parent_category": "personal-care",
    },
]


# ---------------------------------------------------------------------------
# Assemble final output
# ---------------------------------------------------------------------------

def build_categories(fda_category_names):
    """Merge FDA-scraped names with supplemental keywords and build output."""
    categories = []

    for cat_def in CATEGORY_DEFINITIONS:
        slug = cat_def["slug"]
        cat = dict(cat_def)  # shallow copy

        if cat.get("is_parent"):
            # Parent categories don't have keywords
            del cat["is_parent"]
            categories.append(cat)
            continue

        del cat["is_parent"]

        # Combine FDA-scraped brand names with supplemental keywords
        fda_names = fda_category_names.get(slug, set())
        supplemental = set(SUPPLEMENTAL_KEYWORDS.get(slug, []))

        # Clean FDA names
        cleaned_fda = set()
        for name in fda_names:
            c = clean_name(name)
            if c and len(c) >= 2:
                cleaned_fda.add(c)

        # Merge and deduplicate
        all_keywords = cleaned_fda | {k.lower().strip() for k in supplemental}

        # Remove overly generic or too-long entries
        filtered = set()
        for kw in all_keywords:
            if len(kw) < 2:
                continue
            if len(kw) > 60:
                continue
            filtered.add(kw)

        cat["keywords"] = sorted(filtered)
        categories.append(cat)

    return categories


def main():
    print("=" * 60)
    print("Safety Seal Checker - Category Taxonomy Builder")
    print("Scraping openFDA APIs for real product brand names...")
    print("=" * 60)

    # Scrape FDA APIs
    fda_category_names = scrape_all()

    # Report what we found
    print("\n" + "=" * 60)
    print("FDA API Scraping Results:")
    for slug, names in sorted(fda_category_names.items()):
        print(f"  {slug}: {len(names)} raw names")

    # Build categories
    categories = build_categories(fda_category_names)

    # Report keyword counts
    print("\nFinal Category Keyword Counts:")
    for cat in categories:
        kw_count = len(cat.get("keywords", []))
        if kw_count > 0:
            print(f"  {cat['slug']}: {kw_count} keywords")

    # Write output
    output_path = DATA_DIR / "categories.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(categories, f, indent=2, ensure_ascii=False)
    print(f"\nWrote {output_path}")
    print(f"Total categories: {len(categories)}")
    print("Done!")


if __name__ == "__main__":
    main()
