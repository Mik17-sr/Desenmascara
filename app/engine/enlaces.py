"""Revisión 3 · El detective de enlaces: official site, look-alikes, domain age and reputation lists.

Links are never opened: only the domain name is compared and its public registration (RDAP)
is queried, with a short timeout, on a fixed host. With a key, the link text is also looked up
in Google Safe Browsing and URLhaus, again on fixed hosts.
"""

import asyncio
import re
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urlsplit

import httpx

from app.core.config import settings

RDAP_URL = "https://rdap.org/domain/{}"
RDAP_TIMEOUT = httpx.Timeout(2.5, connect=1.5)
SAFE_BROWSING_URL = "https://safebrowsing.googleapis.com/v4/threatMatches:find"
URLHAUS_URL = "https://urlhaus-api.abuse.ch/v1/url/"
SECOND_LEVEL_SUFFIXES = {"com.co", "gov.co", "org.co", "edu.co", "net.co", "mil.co", "nom.co", "co.uk", "com.mx", "com.ar", "com.br"}
HOMOGLYPHS = str.maketrans({"0": "o", "1": "l", "3": "e", "4": "a", "5": "s", "7": "t", "@": "a"})
_age_cache: dict[str, tuple[float, "DomainAge"]] = {}


@dataclass
class LinkCheck:
    url: str
    dominio: str
    oficial_de: str | None = None
    imita_a: str | None = None
    punycode: bool = False


@dataclass
class DomainAge:
    dominio: str
    registrado: bool | None  # None: the registry did not answer in time
    dias: int | None = None


def registered_domain(host: str) -> str:
    host = host.lower().rstrip(".").removeprefix("www.")
    parts = host.split(".")
    if len(parts) >= 3 and ".".join(parts[-2:]) in SECOND_LEVEL_SUFFIXES:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:])


def _skeleton(label: str) -> str:
    """'bancoandin0' -> 'bancoandino': undoes the usual character swaps."""
    swapped = label.lower().translate(HOMOGLYPHS).replace("rn", "m").replace("vv", "w")
    return re.sub(r"[^a-z]", "", swapped)


def levenshtein(a: str, b: str) -> int:
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        current = [i]
        for j, cb in enumerate(b, 1):
            current.append(min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + (ca != cb)))
        previous = current
    return previous[-1]


def _looks_alike(label: str, brand: str) -> bool:
    if len(brand) < 5:  # "dian", "bbva", "itau": only as a whole word or at the start, so meridian.com is not the DIAN
        words = re.split(r"[-_]", label)
        return label.startswith(brand) or _skeleton(brand) in {_skeleton(w) for w in words}
    return brand in label or _skeleton(brand) in _skeleton(label) or levenshtein(_skeleton(label), _skeleton(brand)) <= 2


def check_link(url: str, official_domains: Mapping[str, str | Sequence[str]], claimed: list[str]) -> LinkCheck:
    """official_domains maps entity name -> its official domain or domains; claimed are the names the message uses."""
    host = urlsplit(url).hostname or ""
    domain = registered_domain(host)
    check = LinkCheck(url=url, dominio=domain, punycode=any(p.startswith("xn--") for p in host.split(".")))
    sites = [(name, site) for name, value in official_domains.items() for site in ([value] if isinstance(value, str) else value)]
    for name, site in sites:
        if domain == site:
            check.oficial_de = name
            return check
    label = domain.split(".")[0]
    check.imita_a = (next((name for name, site in sites if _looks_alike(label, site.split(".")[0])), None)
                     or next((name for name in claimed if name in official_domains), None))
    return check


async def domain_age(domain: str) -> DomainAge:
    cached = _age_cache.get(domain)
    if cached and time.monotonic() - cached[0] < 6 * 3600:
        return cached[1]
    try:
        async with httpx.AsyncClient(timeout=RDAP_TIMEOUT, follow_redirects=True) as client:
            response = await client.get(RDAP_URL.format(domain), headers={"Accept": "application/rdap+json"})
    except httpx.HTTPError:
        return DomainAge(domain, None)
    if response.status_code == 404:
        result = DomainAge(domain, False)
    elif response.status_code == 200:
        result = DomainAge(domain, True, _registration_days(response.json()))
    else:
        return DomainAge(domain, None)
    _age_cache[domain] = (time.monotonic(), result)
    return result


def _registration_days(rdap: dict) -> int | None:
    for event in rdap.get("events", []):
        if event.get("eventAction") == "registration" and event.get("eventDate"):
            created = datetime.fromisoformat(event["eventDate"].replace("Z", "+00:00"))
            return max(0, (datetime.now(timezone.utc) - created).days)
    return None


async def safe_browsing(urls: list[str]) -> set[str]:
    """Links Google already lists as dangerous. Off unless GOOGLE_SAFE_BROWSING_KEY is set."""
    if not settings.GOOGLE_SAFE_BROWSING_KEY or not urls:
        return set()
    body = {
        "client": {"clientId": "desenmascara", "clientVersion": settings.VERSION},
        "threatInfo": {
            "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE"],
            "platformTypes": ["ANY_PLATFORM"],
            "threatEntryTypes": ["URL"],
            "threatEntries": [{"url": u} for u in urls],
        },
    }
    try:
        async with httpx.AsyncClient(timeout=RDAP_TIMEOUT) as client:
            response = await client.post(SAFE_BROWSING_URL, params={"key": settings.GOOGLE_SAFE_BROWSING_KEY}, json=body)
            response.raise_for_status()
    except httpx.HTTPError:
        return set()
    return {m["threat"]["url"] for m in response.json().get("matches", [])}


async def urlhaus(urls: list[str]) -> set[str]:
    """Links abuse.ch's URLhaus lists as malware sites. Off unless URLHAUS_AUTH_KEY is set (free at auth.abuse.ch)."""
    if not settings.URLHAUS_AUTH_KEY or not urls:
        return set()

    async def listed(client: httpx.AsyncClient, url: str) -> bool:
        try:
            response = await client.post(URLHAUS_URL, data={"url": url})
            response.raise_for_status()
            return response.json().get("query_status") == "ok"
        except (httpx.HTTPError, ValueError):
            return False

    async with httpx.AsyncClient(timeout=RDAP_TIMEOUT, headers={"Auth-Key": settings.URLHAUS_AUTH_KEY}) as client:
        found = await asyncio.gather(*(listed(client, u) for u in urls))
    return {u for u, hit in zip(urls, found) if hit}


async def reputation(urls: list[str]) -> set[str]:
    """Links already reported as dangerous by Google Safe Browsing or URLhaus."""
    google, abuse = await asyncio.gather(safe_browsing(urls), urlhaus(urls))
    return google | abuse


async def domain_ages(domains: list[str]) -> dict[str, DomainAge]:
    results = await asyncio.gather(*(domain_age(d) for d in domains[:3]))
    return {r.dominio: r for r in results}
