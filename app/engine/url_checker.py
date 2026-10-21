"""Safe URL inspection. This module never fetches user supplied URLs."""
from urllib.parse import urlsplit

from app.schemas.contract import LinkAnalysis, LinkStatus

EXTERNAL_TIMEOUT_SECONDS = 3.0


def check_url_reputation(urls: list[str]) -> list[LinkAnalysis]:
    """Return local URL metadata without making HTTP requests (SSRF safe).

    No reputation provider is configured. Provider failures/timeouts, when an
    integration is added, must degrade to ``unchecked`` within 3 seconds.
    """
    results: list[LinkAnalysis] = []
    for url in urls:
        try:
            parsed = urlsplit(url)
            if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
                results.append(LinkAnalysis(url=url, status=LinkStatus.SUSPICIOUS,
                                           reason="URL sin esquema HTTP(S) o dominio válido."))
                continue
            results.append(LinkAnalysis(url=url, status=LinkStatus.UNCHECKED,
                                       reason=f"Dominio {parsed.hostname} extraído localmente; reputación externa no disponible."))
        except (ValueError, UnicodeError):
            results.append(LinkAnalysis(url=url, status=LinkStatus.SUSPICIOUS,
                                       reason="No fue posible interpretar la URL de forma segura."))
    return results
