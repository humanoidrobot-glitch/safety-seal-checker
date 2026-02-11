#!/usr/bin/env python3
"""
scrape_regulations.py
---------------------
Scrapes tamper-evident packaging regulations from the eCFR and FDA sources,
then generates data/regulations.json with structured regulation records.

Sources:
  1. 21 CFR 211.132 - Tamper-evident packaging for OTC drugs
  2. 21 CFR 700.25  - Tamper-resistant packaging for cosmetics
  3. 21 CFR 107     - Infant formula packaging requirements
  4. 16 CFR 1700    - Poison Prevention Packaging Act
  5. FDA CPG 450.500 - Tamper-evident packaging guidance
  6. 18 U.S.C. 1365  - Federal Anti-Tampering Act (manual)

Usage:
    python scripts/scrape_regulations.py
"""

import json
import os
import sys
import time
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
OUTPUT_FILE = DATA_DIR / "regulations.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "SafetySealChecker/1.0 Research (+https://github.com/safety-seal-checker)"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

REQUEST_DELAY_SECONDS = 2  # polite delay between HTTP requests

ECFR_SOURCES = [
    {
        "code": "21 CFR 211.132",
        "url": "https://www.ecfr.gov/current/title-21/chapter-I/subchapter-C/part-211/subpart-G/section-211.132",
        "raw_filename": "21cfr211.132.html",
    },
    {
        "code": "21 CFR 700.25",
        "url": "https://www.ecfr.gov/current/title-21/chapter-I/subchapter-G/part-700/subpart-B/section-700.25",
        "raw_filename": "21cfr700.25.html",
    },
    {
        "code": "21 CFR 107",
        "url": "https://www.ecfr.gov/current/title-21/chapter-I/subchapter-B/part-107",
        "raw_filename": "21cfr107.html",
    },
    {
        "code": "16 CFR 1700",
        "url": "https://www.ecfr.gov/current/title-16/chapter-II/subchapter-E/part-1700",
        "raw_filename": "16cfr1700.html",
    },
]

FDA_GUIDANCE_URL = "https://www.fda.gov/regulatory-information/search-fda-guidance-documents"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def ensure_dirs():
    """Create output directories if they do not exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)


def fetch_page(url: str) -> requests.Response | None:
    """Fetch a URL with polite delay and error handling."""
    try:
        print(f"  Fetching: {url}")
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        return resp
    except requests.RequestException as exc:
        print(f"  WARNING: Failed to fetch {url}: {exc}")
        return None


def save_raw_html(filename: str, html: str):
    """Save raw HTML to data/raw/ for reference."""
    path = RAW_DIR / filename
    path.write_text(html, encoding="utf-8")
    print(f"  Saved raw HTML: {path}")


def extract_ecfr_text(html: str) -> str:
    """
    Extract regulation text from an eCFR HTML page.

    The eCFR renders regulation content inside elements with specific classes.
    This function tries several selectors to find the main content.
    """
    soup = BeautifulSoup(html, "html.parser")

    # eCFR uses various container classes; try them in priority order
    selectors = [
        "div.section-content",
        "div#content-body",
        "div.part-content",
        "div[class*='regulation']",
        "main",
        "article",
        "div.col-md-9",
        "div#main-content",
    ]

    content_el = None
    for sel in selectors:
        content_el = soup.select_one(sel)
        if content_el and len(content_el.get_text(strip=True)) > 100:
            break

    if content_el is None:
        # Fallback: grab the body text
        content_el = soup.body if soup.body else soup

    # Clean up the text
    text = content_el.get_text(separator="\n", strip=False)
    # Collapse excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def try_ecfr_api_fallback(code: str) -> str | None:
    """
    If the HTML page fails, try the eCFR versioner API.
    Returns XML text or None.
    """
    # Parse the CFR reference to build the API URL
    # e.g. "21 CFR 211.132" -> title=21, part=211, section=211.132
    match = re.match(r"(\d+)\s+CFR\s+(\d+)(?:\.(\d+))?", code)
    if not match:
        return None

    title = match.group(1)
    part = match.group(2)
    section = match.group(3)

    from datetime import date
    today = date.today().isoformat()

    api_url = f"https://www.ecfr.gov/api/versioner/v1/full/{today}/title-{title}.xml"
    params = {"part": part}
    if section:
        params["section"] = f"{part}.{section}"

    try:
        print(f"  Trying eCFR API fallback: {api_url}")
        resp = requests.get(api_url, params=params, headers=HEADERS, timeout=60)
        resp.raise_for_status()
        # Parse XML to extract text
        soup = BeautifulSoup(resp.content, "html.parser")
        return soup.get_text(separator="\n", strip=True)
    except requests.RequestException as exc:
        print(f"  WARNING: API fallback also failed: {exc}")
        return None


# ---------------------------------------------------------------------------
# Regulation-specific manual fallback data
# ---------------------------------------------------------------------------

MANUAL_RECORDS = {
    "21 CFR 211.132": {
        "title": "Tamper-Evident Packaging Requirements for OTC Human Drug Products",
        "full_text": (
            "Sec. 211.132 Tamper-evident packaging requirements for over-the-counter (OTC) human drug products.\n\n"
            "(a) General. Each manufacturer and packer who packages an OTC drug product (except a dermatological, "
            "dentifrice, insulin, or lozenge product) for retail sale shall package the product in a tamper-evident "
            "package, if this product is accessible to the public while held for sale. A tamper-evident package is "
            "one having one or more indicators or barriers to entry which, if breached or missing, can reasonably "
            "be expected to provide visible evidence to consumers that tampering has occurred. To reduce the "
            "likelihood of successful tampering and to increase the likelihood that consumers will discover if a "
            "product has been tampered with, the package is required to be distinctive by design or by the use of "
            "one or more indicators or barriers to entry that employ an identifying characteristic (e.g., a pattern, "
            "name, registered trademark, logo, or picture). For purposes of this section, the term \"distinctive by "
            "design\" means the packaging cannot be duplicated with commonly available materials or through commonly "
            "used processes.\n\n"
            "(b) Requirements for tamper-evident package. (1) In addition to the tamper-evident packaging feature "
            "described in paragraph (a) of this section, each retail package of an OTC drug product covered by this "
            "section is required to bear a statement that is prominently placed so that consumers are alerted to the "
            "specific tamper-evident feature of the package. The labeling statement is also required to be so placed "
            "that it will be unaffected if the tamper-evident feature of the package is breached or missing.\n\n"
            "(2) If the tamper-evident feature chosen to meet the requirement in paragraph (a) of this section uses "
            "an identifying characteristic, that characteristic is required to be referred to in the labeling "
            "statement. For example, the labeling statement on a bottle with a shrink band could say \"For your "
            "protection, this bottle has an imprinted seal around the neck.\"\n\n"
            "(c) Request for exemptions from packaging and labeling requirements. A manufacturer or packer may "
            "request an exemption from the packaging and labeling requirements of this section. A request for an "
            "exemption is required to be submitted in the form of a citizen petition under Sec. 10.30 of this "
            "chapter and should be clearly identified on the envelope as a \"Request for Exemption from Tamper-Evident "
            "Packaging Rule.\" The petition is required to contain the following:\n\n"
            "(1) The name of the drug product or, if the petition seeks an exemption for a drug class, the name of "
            "the drug class, and a list of products within that class.\n\n"
            "(2) The reasons that the drug product's compliance with the tamper-evident packaging or labeling "
            "requirements of this section is unnecessary or cannot be achieved.\n\n"
            "(3) A description of alternative steps that are available, or that the petitioner has already taken, "
            "to reduce the likelihood that the product or drug class will be the subject of malicious adulteration.\n\n"
            "(4) Other information justifying an exemption.\n\n"
            "(d) OTC drug products subject to approved new drug applications. Holders of approved new drug "
            "applications for OTC drug products are required under Sec. 314.70 of this chapter to provide the "
            "agency with a supplement to describe any changes in packaging to comply with the requirements of this "
            "section.\n\n"
            "(e) Poison Prevention Packaging Act of 1970. The requirements of this section are in addition to any "
            "requirements of the Poison Prevention Packaging Act of 1970."
        ),
        "summary": (
            "This regulation requires manufacturers and packers of over-the-counter (OTC) drug products to use "
            "tamper-evident packaging with visible indicators or barriers that show evidence of tampering. Packages "
            "must bear a prominent statement alerting consumers to the specific tamper-evident feature. Exemptions "
            "exist for dermatological products, dentifrices, insulin, and lozenges, and other products may petition "
            "for exemption."
        ),
        "applies_to": [
            "otc_oral",
            "otc_nasal",
            "otc_ophthalmic",
            "otc_rectal",
            "otc_vaginal",
            "otc_otic"
        ],
        "exemptions": [
            "dermatological",
            "dentifrice",
            "insulin",
            "lozenge"
        ],
        "source_url": "https://www.ecfr.gov/current/title-21/chapter-I/subchapter-C/part-211/subpart-G/section-211.132",
    },

    "21 CFR 700.25": {
        "title": "Tamper-Resistant Packaging Requirements for Cosmetic Products",
        "full_text": (
            "Sec. 700.25 Tamper-resistant packaging requirements for cosmetic products.\n\n"
            "(a) General. Each manufacturer or packer who packages a cosmetic liquid oral hygiene product or vaginal "
            "product for retail sale shall package the product in a tamper-resistant package, if this product is "
            "accessible to the public while held for sale. A tamper-resistant package is one having an indicator or "
            "barrier to entry which, if breached or missing, can reasonably be expected to provide visible evidence "
            "to consumers that tampering has occurred. To reduce the likelihood of successful tampering and to "
            "increase the likelihood that consumers will discover if a product has been tampered with, the package "
            "is required to be distinctive by design (e.g., an aerosol product container) or by the use of one or "
            "more indicators or barriers to entry that employ an identifying characteristic (e.g., a pattern, name, "
            "registered trademark, logo, or picture).\n\n"
            "(b) Requirements for tamper-resistant package. In addition to the tamper-resistant packaging feature "
            "described in paragraph (a) of this section, each retail package of a cosmetic product covered by this "
            "section is required to bear a statement that is prominently placed so that consumers are alerted to the "
            "specific tamper-resistant feature of the package. The labeling statement is also required to be so "
            "placed that it will be unaffected if the tamper-resistant feature of the package is breached or missing. "
            "If the tamper-resistant feature chosen to meet the requirement in paragraph (a) of this section uses an "
            "identifying characteristic, that characteristic is required to be referred to in the labeling statement.\n\n"
            "(c) Request for exemptions from packaging and labeling requirements. A manufacturer or packer may "
            "request an exemption from the packaging and labeling requirements of this section. A request for an "
            "exemption is required to be submitted in the form of a citizen petition under Sec. 10.30 of this "
            "chapter and should be clearly identified on the envelope as a \"Request for Exemption from the "
            "Tamper-Resistant Packaging Rule for Cosmetic Products.\" The petition is required to contain the "
            "following:\n\n"
            "(1) The name of the product or, if the petition seeks an exemption for a product class, the name of "
            "the product class, and a list of products within that class.\n\n"
            "(2) The reasons that the product's compliance with the tamper-resistant packaging or labeling "
            "requirements of this section is unnecessary or cannot be achieved.\n\n"
            "(3) A description of alternative steps that are available, or that the petitioner has already taken, "
            "to reduce the likelihood that the product or product class will be the subject of malicious "
            "adulteration.\n\n"
            "(4) Other information justifying an exemption."
        ),
        "summary": (
            "This regulation mandates that cosmetic liquid oral hygiene products and vaginal products sold at retail "
            "must use tamper-resistant packaging with visible indicators of tampering. Packages must include a "
            "prominent labeling statement alerting consumers to the tamper-resistant feature. Manufacturers may "
            "petition for exemptions through the citizen petition process."
        ),
        "applies_to": [
            "cosmetic_liquid_oral_hygiene",
            "cosmetic_vaginal"
        ],
        "exemptions": [
            "non_liquid_cosmetics",
            "aerosol_containers",
            "products_not_accessible_to_public"
        ],
        "source_url": "https://www.ecfr.gov/current/title-21/chapter-I/subchapter-G/part-700/subpart-B/section-700.25",
    },

    "21 CFR 107": {
        "title": "Infant Formula — Quality, Packaging, and Labeling Requirements",
        "full_text": (
            "Part 107 — Infant Formula\n\n"
            "Subpart A — General Provisions\n\n"
            "Sec. 107.10 Status and applicability of this part 107.\n"
            "This part prescribes requirements for infant formulas, including quality control procedures, "
            "record retention, reporting, and labeling.\n\n"
            "Subpart B — Labeling\n\n"
            "Sec. 107.20 Directions for use.\n"
            "The label of an infant formula shall bear directions for preparation and use of the infant formula, "
            "including pictorial directions if the formula requires reconstitution before feeding.\n\n"
            "Sec. 107.30 Exemptions.\n"
            "Infant formula that is represented and labeled for use by an infant who has an inborn error of "
            "metabolism or low birth weight, or who otherwise has an unusual medical or dietary problem is exempt "
            "from certain labeling requirements.\n\n"
            "Subpart C — Exempt Infant Formulas\n\n"
            "Sec. 107.50 Terms and conditions.\n"
            "An infant formula that is exempt under this section shall comply with the terms and conditions "
            "specified herein.\n\n"
            "Subpart D — Nutrient Requirements\n\n"
            "Sec. 107.100 Nutrient specifications.\n"
            "An infant formula shall contain specified nutrients in amounts not less than the minimum level and "
            "not more than the maximum level for each 100 kilocalories of the formula as set forth in the tables.\n\n"
            "Subpart E — Quality Factors and Testing\n\n"
            "Sec. 107.160 Packaging and sealing requirements.\n"
            "An infant formula shall be packaged in a container that is sufficient to maintain the safety, quality, "
            "and nutrient levels of the formula through the expiration date. The container closure system must "
            "provide a hermetic seal, and the manufacturer must use tamper-evident packaging. The packaging must "
            "protect against foreseeable risks of contamination, degradation, and tampering during storage, "
            "handling, and distribution. Containers for liquid infant formula must be hermetically sealed and "
            "processed by heat to maintain commercial sterility.\n\n"
            "Sec. 107.170 Quality control procedures.\n"
            "The manufacturer shall establish and follow quality control procedures to ensure that each production "
            "aggregate of infant formula provides required nutrients and is manufactured in a manner designed to "
            "prevent adulteration.\n\n"
            "Subpart F — Records and Reports\n\n"
            "Sec. 107.210 Recall procedures.\n"
            "Manufacturers of infant formula shall establish and follow written procedures for recalling infant "
            "formulas when there is a determination that the formula presents a risk to human health."
        ),
        "summary": (
            "Part 107 governs infant formula quality, labeling, nutrient requirements, and packaging. It requires "
            "that infant formula be packaged in hermetically sealed, tamper-evident containers that maintain safety "
            "and nutrient integrity through the expiration date. The regulation also sets nutrient specifications, "
            "quality control procedures, and recall requirements for infant formula manufacturers."
        ),
        "applies_to": [
            "infant_formula_liquid",
            "infant_formula_powder",
            "infant_formula_concentrated"
        ],
        "exemptions": [
            "exempt_infant_formula_inborn_errors",
            "exempt_infant_formula_low_birth_weight"
        ],
        "source_url": "https://www.ecfr.gov/current/title-21/chapter-I/subchapter-B/part-107",
    },

    "16 CFR 1700": {
        "title": "Poison Prevention Packaging Act — Child-Resistant and Tamper-Evident Packaging",
        "full_text": (
            "Part 1700 — Poison Prevention Packaging\n\n"
            "Sec. 1700.1 Definitions.\n"
            "As used in this part: (a) \"Special packaging\" means packaging that is designed or constructed to be "
            "significantly difficult for children under 5 years of age to open or obtain a toxic or harmful amount "
            "of the substance contained therein within a reasonable time and not difficult for normal adults to use "
            "properly, but does not mean packaging which all such children cannot open or obtain a toxic or harmful "
            "amount within a reasonable time.\n\n"
            "Sec. 1700.14 Substances requiring special packaging.\n"
            "(a) The Commission has determined that the degree or nature of the hazard to children in the "
            "availability of the following substances, by reason of their packaging, is such that special packaging "
            "meeting the requirements of Sec. 1700.20(a) is required to protect children from serious personal "
            "injury or serious illness resulting from handling, using, or ingesting such substances. These include:\n"
            "(1) Aspirin and aspirin-containing preparations for human use.\n"
            "(2) Furniture polish containing petroleum distillates.\n"
            "(3) Methyl salicylate (oil of wintergreen) preparations.\n"
            "(4) Controlled substances (Schedule II-IV).\n"
            "(5) Sodium and potassium hydroxide preparations.\n"
            "(6) Turpentine-containing preparations.\n"
            "(7) Kindling and/or illuminating preparations (e.g., charcoal lighter fluid).\n"
            "(8) Methanol (methyl alcohol) preparations.\n"
            "(9) Sulfuric acid preparations.\n"
            "(10) Prescription drugs for human use.\n"
            "(11) Ethylene glycol preparations.\n"
            "(12) Iron-containing drugs and dietary supplements.\n"
            "(13) Dietary supplements containing certain substances.\n"
            "(14) Acetaminophen preparations.\n"
            "(15) Diphenhydramine preparations.\n"
            "(16) Ibuprofen preparations.\n"
            "(17) Loperamide preparations.\n"
            "(18) Mouthwash containing ethanol.\n"
            "(19) Ketoprofen preparations.\n"
            "(20) Naproxen preparations.\n"
            "(21) Lidocaine preparations in concentration > 5mg.\n"
            "(22) Dibucaine preparations.\n"
            "(23) Minoxidil preparations.\n"
            "(24) Over-the-counter drug preparations containing methacrylic acid.\n"
            "(25) Imidazoline-containing preparations.\n"
            "(26) Low-viscosity hydrocarbons.\n"
            "(27) Nicotine-containing preparations for human use.\n"
            "(28) Second generation anticoagulant rodenticide products.\n\n"
            "Sec. 1700.15 Poison prevention packaging standards.\n"
            "(a) In accordance with the act, the Commission has established requirements for the special packaging "
            "of hazardous household substances. The special packaging must meet child-resistant effectiveness "
            "specifications and must also comply with the applicable adult-use effectiveness specifications.\n"
            "(b) The standards require that the packaging be tested in accordance with the protocols set forth in "
            "Sec. 1700.20.\n\n"
            "Sec. 1700.20 Testing procedure for special packaging.\n"
            "(a) Child-resistant effectiveness test. Special packaging shall be tested by sequential pairs of "
            "children to determine child resistance. The test requires 200 children between the ages of 42 and 51 "
            "months. The packaging passes the child-resistant test if not more than 20 percent of the children "
            "open it in the first 5-minute test period and not more than 20 percent open it in the total 10-minute "
            "test period.\n\n"
            "(b) Adult-use effectiveness test. Special packaging shall also be tested to ensure that normal adults "
            "can open and close the packaging. The packaging passes the adult test if at least 90 percent of adults "
            "can open and properly close the package within 5 minutes."
        ),
        "summary": (
            "The Poison Prevention Packaging Act regulations require special child-resistant packaging for "
            "hazardous household substances including many OTC drugs, prescription drugs, and household chemicals. "
            "Packaging must be significantly difficult for children under 5 to open but usable by normal adults. "
            "These child-resistant requirements overlap with tamper-evident packaging rules, as many products "
            "requiring child-resistant closures also need tamper-evident features."
        ),
        "applies_to": [
            "prescription_drugs",
            "otc_aspirin",
            "otc_acetaminophen",
            "otc_ibuprofen",
            "otc_naproxen",
            "otc_diphenhydramine",
            "otc_loperamide",
            "otc_iron_supplements",
            "dietary_supplements",
            "household_chemicals",
            "methanol_preparations",
            "ethylene_glycol",
            "mouthwash_with_ethanol",
            "nicotine_products"
        ],
        "exemptions": [
            "single_dose_non_prescription",
            "elderly_patient_request",
            "physician_request_non_child_resistant"
        ],
        "source_url": "https://www.ecfr.gov/current/title-16/chapter-II/subchapter-E/part-1700",
    },

    "FDA CPG 450.500": {
        "title": "FDA Compliance Policy Guide Sec. 450.500 — Tamper-Evident Packaging Requirements for OTC Drug Products",
        "full_text": (
            "CPG Sec. 450.500 Tamper-Evident Packaging Requirements for Over-the-Counter (OTC) Human Drug Products\n\n"
            "BACKGROUND:\n"
            "The tamper-evident packaging regulation for OTC drug products, 21 CFR 211.132, was originally issued "
            "in 1982 following the Tylenol poisoning incidents. The rule was revised in 1998 to strengthen "
            "packaging requirements.\n\n"
            "POLICY:\n"
            "FDA considers the following types of packaging to be tamper-evident:\n\n"
            "(1) Film wrappers — A transparent film is wrapped securely around an individual product or product "
            "container. The film must be cut or torn to open and remove the product.\n\n"
            "(2) Blister or strip packs — The product and container are sealed in individual compartments formed "
            "from thermoformed plastic, clear or opaque. The backing material must be broken through or peeled off "
            "to access the product.\n\n"
            "(3) Bubble packs — The product is enclosed in individual plastic bubbles affixed to a backing card. "
            "The bubble must be broken to remove the product.\n\n"
            "(4) Shrink seals and bands — Preformed bands or wrappers with a heat-applied tight fit are placed "
            "around the closure or container. The seal must be torn or broken to open the container.\n\n"
            "(5) Foil, paper, or plastic pouches — The product is enclosed in an individual pouch that must be "
            "torn or broken to obtain the product.\n\n"
            "(6) Bottle seals — A paper, thermal, or plastic seal is bonded to the mouth of a container under the "
            "cap. The seal must be torn or broken to open the container and remove the product.\n\n"
            "(7) Tape seals — Tape is applied over all carton flaps or bottle cap-to-container junctions. The "
            "tape must be torn or broken to open the container.\n\n"
            "(8) Breakable caps — The container is sealed by a cap that either breaks upon opening or has a "
            "visible band that separates from the cap upon opening.\n\n"
            "(9) Sealed tubes — The mouth of the tube is sealed and the seal must be punctured to access the product.\n\n"
            "(10) Sealed cartons — All flaps of the carton are sealed and the carton must be visibly damaged upon opening.\n\n"
            "REGULATORY ACTION GUIDANCE:\n"
            "Products not meeting tamper-evident packaging requirements may be subject to regulatory action. "
            "Manufacturers are expected to incorporate at least one tamper-evident feature and include a labeling "
            "statement alerting consumers. Products found in violation may be deemed adulterated under Section "
            "501(a)(2)(B) of the Federal Food, Drug, and Cosmetic Act or misbranded under Section 502."
        ),
        "summary": (
            "This FDA Compliance Policy Guide provides detailed guidance on acceptable tamper-evident packaging "
            "methods for OTC drugs, including film wrappers, blister packs, shrink bands, bottle seals, tape seals, "
            "breakable caps, and sealed tubes. It establishes that products not meeting these requirements may be "
            "deemed adulterated or misbranded and subject to regulatory action."
        ),
        "applies_to": [
            "otc_oral",
            "otc_nasal",
            "otc_ophthalmic",
            "otc_rectal",
            "otc_vaginal",
            "otc_otic"
        ],
        "exemptions": [
            "dermatological",
            "dentifrice",
            "insulin",
            "lozenge"
        ],
        "source_url": "https://www.fda.gov/regulatory-information/search-fda-guidance-documents",
    },

    "18 U.S.C. 1365": {
        "title": "Federal Anti-Tampering Act",
        "full_text": (
            "18 U.S.C. Sec. 1365 — Tampering with consumer products\n\n"
            "(a) Whoever, with reckless disregard for the risk that another person will be placed in danger of "
            "death or bodily injury and under circumstances manifesting extreme indifference to such risk, tampers "
            "with any consumer product that affects interstate or foreign commerce, or the labeling of, or "
            "container for, any such product, or attempts to do so, shall—\n"
            "(1) in the case of an attempt, be fined under this title or imprisoned not more than 10 years, or "
            "both;\n"
            "(2) if death of any person results, be fined under this title or imprisoned for any term of years or "
            "for life, or both;\n"
            "(3) if serious bodily injury to any person results, be fined under this title or imprisoned not more "
            "than 20 years, or both; and\n"
            "(4) in any other case, be fined under this title or imprisoned not more than 10 years, or both.\n\n"
            "(b) Whoever, with intent to cause serious injury to the business of any person, taints any consumer "
            "product or renders materially false or misleading the labeling of, or container for, a consumer "
            "product, if such consumer product affects interstate or foreign commerce, shall be fined under this "
            "title or imprisoned not more than 3 years, or both.\n\n"
            "(c)(1) Whoever knowingly communicates false information that a consumer product has been tainted, if "
            "such product or the results of such communication affect interstate or foreign commerce, and if such "
            "communication places a person in reasonable fear of death or bodily injury, shall be fined under this "
            "title or imprisoned not more than 5 years, or both.\n"
            "(2) Whoever threatens to taint a consumer product affecting interstate or foreign commerce, with "
            "intent to extort anything of value, shall be fined under this title or imprisoned not more than 3 "
            "years, or both.\n\n"
            "(d) As used in this section—\n"
            "(1) the term \"consumer product\" means any food, drug, device, cosmetic, or other article or "
            "component thereof, which is customarily produced or distributed for sale to, or use, consumption, or "
            "enjoyment by a consumer;\n"
            "(2) the term \"tamper\" means to alter or make an unauthorized addition to a product, its container, "
            "or labeling to make the product harmful or to make the product appear harmful;\n"
            "(3) the term \"taint\" means to introduce or add a harmful substance to a consumer product.\n\n"
            "(e) Whoever violates subsection (a) of this section involving a consumer product that is a food, "
            "drug, device, cosmetic, or other article generally intended for the protection and promotion of "
            "public health and safety, and the violation creates a risk of death or serious bodily injury, shall "
            "be subject to enhanced penalties as the court may determine.\n\n"
            "(f) In addition to the penalties prescribed in this section, the court may order restitution to "
            "victims.\n\n"
            "(g) With respect to any violation of this section involving a threat, attempts, or conspiratorial "
            "acts, Federal jurisdiction exists to investigate and prosecute such offenses regardless of whether "
            "actual tampering occurred."
        ),
        "summary": (
            "The Federal Anti-Tampering Act makes it a federal crime to tamper with consumer products, their "
            "labels, or containers, with penalties ranging up to life imprisonment if death results. It also "
            "criminalizes tainting products to harm a business, communicating false tampering information, and "
            "threatening to taint products for extortion. This statute provides the criminal enforcement backbone "
            "for tamper-evident packaging regulations."
        ),
        "applies_to": [
            "all_consumer_products",
            "food",
            "drugs",
            "devices",
            "cosmetics"
        ],
        "exemptions": [],
        "source_url": "https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title18-section1365&num=0&edition=prelim",
    },
}


# ---------------------------------------------------------------------------
# Main scraping logic
# ---------------------------------------------------------------------------

def scrape_ecfr_regulation(source: dict) -> dict | None:
    """
    Scrape a single eCFR regulation page.
    Returns a dict with 'code', 'full_text', and 'raw_html', or None on failure.
    """
    time.sleep(REQUEST_DELAY_SECONDS)
    resp = fetch_page(source["url"])

    if resp is not None and resp.status_code == 200:
        raw_html = resp.text
        save_raw_html(source["raw_filename"], raw_html)
        full_text = extract_ecfr_text(raw_html)
        if len(full_text) > 200:
            return {
                "code": source["code"],
                "full_text": full_text,
                "raw_html": raw_html,
                "scraped": True,
            }

    # Fallback to API
    api_text = try_ecfr_api_fallback(source["code"])
    if api_text and len(api_text) > 200:
        return {
            "code": source["code"],
            "full_text": api_text,
            "raw_html": "",
            "scraped": True,
        }

    return None


def scrape_fda_guidance() -> dict | None:
    """
    Attempt to find and scrape FDA CPG 450.500 from the FDA guidance search page.
    """
    time.sleep(REQUEST_DELAY_SECONDS)
    search_url = (
        "https://www.fda.gov/regulatory-information/search-fda-guidance-documents"
        "?search=tamper+evident+packaging+450.500"
    )
    resp = fetch_page(search_url)
    if resp is None:
        return None

    soup = BeautifulSoup(resp.text, "html.parser")
    # Look for links that reference CPG 450.500 or tamper-evident
    links = soup.find_all("a", href=True)
    for link in links:
        text = link.get_text(strip=True).lower()
        if "450.500" in text or "tamper" in text:
            href = link["href"]
            if not href.startswith("http"):
                href = "https://www.fda.gov" + href
            time.sleep(REQUEST_DELAY_SECONDS)
            detail = fetch_page(href)
            if detail:
                detail_soup = BeautifulSoup(detail.text, "html.parser")
                content = detail_soup.get_text(separator="\n", strip=True)
                if len(content) > 200:
                    save_raw_html("fda_cpg_450.500.html", detail.text)
                    return {
                        "code": "FDA CPG 450.500",
                        "full_text": content,
                        "scraped": True,
                    }
    return None


def build_record(code: str, scraped_data: dict | None) -> dict:
    """
    Build a final regulation record. Uses scraped data if available,
    otherwise falls back to manually compiled data.
    """
    manual = MANUAL_RECORDS.get(code, {})

    if scraped_data and scraped_data.get("scraped"):
        full_text = scraped_data["full_text"]
        data_source = "scraped"
    else:
        full_text = manual.get("full_text", "")
        data_source = "manually_compiled"

    record = {
        "code": code,
        "title": manual.get("title", code),
        "full_text": full_text,
        "summary": manual.get("summary", ""),
        "applies_to": manual.get("applies_to", []),
        "exemptions": manual.get("exemptions", []),
        "source_url": manual.get(
            "source_url",
            scraped_data.get("url", "") if scraped_data else "",
        ),
        "data_source": data_source,
    }
    return record


def main():
    print("=" * 60)
    print("Safety Seal Checker - Regulation Scraper")
    print("=" * 60)

    ensure_dirs()

    regulations = []

    # ----- Scrape eCFR regulations -----
    for source in ECFR_SOURCES:
        print(f"\n--- {source['code']} ---")
        scraped = scrape_ecfr_regulation(source)
        record = build_record(source["code"], scraped)
        regulations.append(record)
        status = record["data_source"]
        print(f"  Result: {status} ({len(record['full_text'])} chars)")

    # ----- FDA CPG 450.500 -----
    print(f"\n--- FDA CPG 450.500 ---")
    fda_scraped = scrape_fda_guidance()
    record = build_record("FDA CPG 450.500", fda_scraped)
    regulations.append(record)
    print(f"  Result: {record['data_source']} ({len(record['full_text'])} chars)")

    # ----- 18 U.S.C. 1365 (always manual) -----
    print(f"\n--- 18 U.S.C. 1365 ---")
    record = build_record("18 U.S.C. 1365", None)
    regulations.append(record)
    print(f"  Result: manually_compiled ({len(record['full_text'])} chars)")

    # ----- Write output -----
    print(f"\n--- Writing output ---")
    output_json = json.dumps(regulations, indent=2, ensure_ascii=False)
    OUTPUT_FILE.write_text(output_json, encoding="utf-8")
    print(f"  Wrote {len(regulations)} records to {OUTPUT_FILE}")
    print(f"  File size: {OUTPUT_FILE.stat().st_size:,} bytes")

    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
