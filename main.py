"""
Google Maps Lead Enrichment Actor
==================================
Input:  Google Maps place objects (name, address, phone, website, etc.)
Output: Enriched leads with emails, social media, contact info

Apify Lead Generation category — highest revenue on the platform.
"""

import asyncio
import json
import os
import re
import sys
from urllib.parse import urlparse

try:
    from Apify import Apify  # type: ignore
except ImportError:
    Apify = None

# ── Email/Phone/Social extraction patterns ─────────────────────────────────

EMAIL_RE   = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')
PHONE_RE   = re.compile(r'\+?[\d\s\-().]{7,20}\d')
SOCIAL_RE  = re.compile(
    r'(facebook|instagram|linkedin|twitter|youtube|tiktok|github|weixin|wechat)'
    r'[\./=?\w\-]*[a-zA-Z0-9]', re.IGNORECASE
)
URL_RE     = re.compile(r'https?://[^\s<>"{}|\\^`\[\]]+')


# ── Core enrichment logic ───────────────────────────────────────────────────

async def fetch_page_text(session, url: str, timeout: int = 10) -> str:
    """Fetch raw HTML text from a URL."""
    try:
        import httpx
        async with httpx.AsyncClient(follow_redirects=True, timeout=timeout) as client:
            resp = await client.get(url, headers={
                "User-Agent": "Mozilla/5.0 (compatible; GoogleMapsLeadEnricher/1.0)"
            })
            return resp.text
    except Exception:
        return ""


def extract_emails(text: str) -> list[str]:
    seen, out = set(), []
    for e in EMAIL_RE.findall(text):
        e = e.lower()
        if e not in seen and not e.startswith('noreply'):
            seen.add(e); out.append(e)
    return out[:10]


def extract_phones(text: str) -> list[str]:
    seen, out = set(), []
    for p in PHONE_RE.findall(text):
        clean = re.sub(r'[^\d+]', '', p)
        if len(clean) >= 7 and clean not in seen:
            seen.add(clean); out.append(p.strip())
    return out[:5]


def extract_social(text: str) -> dict[str, str]:
    social = {}
    for m in SOCIAL_RE.finditer(text):
        domain = m.group(1).lower()
        url = m.group(0)
        if domain == "weixin" or domain == "wechat":
            social["wechat"] = url
        elif domain not in social:
            social[domain] = url
    return social


def extract_website_from_google_maps(gm_data: dict) -> str | None:
    """Get website URL from Google Maps place data."""
    # Try various common field names
    for key in ("website", "url", "web", "site"):
        val = gm_data.get(key) or gm_data.get("websiteUrl") or gm_data.get("raw", {}).get(key)
        if val and val.startswith("http"):
            return val
    return None


async def enrich_place(session, place: dict, level: str) -> dict:
    """Enrich a single Google Maps place record."""
    enriched = {**place}

    website = extract_website_from_google_maps(place)
    enriched["enriched"] = {}

    if website:
        text = await fetch_page_text(session, website)
        emails = extract_emails(text) if text else []
        phones = extract_phones(text) if text else []
        social = extract_social(text) if text else {}

        enriched["enriched"]["website"] = website
        enriched["enriched"]["emails"] = emails
        enriched["enriched"]["phones"] = phones
        enriched["enriched"]["socialMedia"] = social
    else:
        enriched["enriched"]["website"] = None
        enriched["enriched"]["emails"] = []
        enriched["enriched"]["phones"] = (
            [place.get("phone"), place.get("mobilePhone")]
            if place.get("phone") or place.get("mobilePhone") else []
        )
        enriched["enriched"]["socialMedia"] = {}

    # Summary score
    score = 0
    if enriched["enriched"].get("website"): score += 25
    if enriched["enriched"].get("emails"):   score += 35
    if enriched["enriched"].get("phones"):   score += 20
    if enriched["enriched"].get("socialMedia"): score += 20
    enriched["enriched"]["leadScore"] = score

    return enriched


async def enrich_batch(places: list[dict], level: str, apify_client) -> list[dict]:
    """Enrich all places concurrently with controlled concurrency."""
    import httpx

    semaphore = asyncio.Semaphore(5)  # Max 5 concurrent website fetches

    async def bounded_enrich(session, place):
        async with semaphore:
            return await enrich_place(session, place, level)

    async with httpx.AsyncClient(follow_redirects=True, timeout=15) as session:
        tasks = [bounded_enrich(session, p) for p in places]
        return await asyncio.gather(*tasks)


# ── Apify Actor entry point ─────────────────────────────────────────────────

async def main():
    input_data = {}
    # Try environment variable first (Apify platform sets this)
    if os.getenv("APIFY_INPUT"):
        try:
            input_data = json.loads(os.getenv("APIFY_INPUT"))
        except Exception:
            pass
    # Fallback to stdin (for local testing or direct invocation)
    if not input_data:
        try:
            stdin_content = sys.stdin.read()
            if stdin_content.strip():
                input_data = json.loads(stdin_content)
        except Exception:
            pass

    places = input_data.get("googleMapsData", [])
    level  = input_data.get("enrichmentLevel", "basic")

    if not places:
        print(json.dumps({"error": "No googleMapsData provided"}))
        sys.exit(1)

    results = await enrich_batch(places, level, None)

    # Save to default dataset (if Apify SDK is available)
    if os.getenv("APIFY_TOKEN"):
        try:
            from Apify import Apify
            actor = Apify()
            await actor.push_data(results)
        except Exception:
            pass

    print(json.dumps({"status": "ok", "inputCount": len(places), "outputCount": len(results)}, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
