"""Revisión 5 · El archivista: a MinHash fingerprint per message, so variants of a campaign match.

It compares word triples, not exact text: changing a name, an amount or the link keeps most
of the fingerprint. Stored as JSON in SQLite; with Supabase this would move to pgvector.
"""

import hashlib
import random
import re

from app.engine.pistas import URL_PATTERN, plain

NUM_PERM = 64
_PRIME = (1 << 61) - 1
_rng = random.Random(20261016)  # fixed seed: fingerprints must not change between restarts
_PERMS = [(_rng.randrange(1, _PRIME), _rng.randrange(0, _PRIME)) for _ in range(NUM_PERM)]


def _normalize(text: str) -> list[str]:
    text = URL_PATTERN.sub(" enlace ", plain(text))
    text = re.sub(r"\d+", "0", text)
    return re.findall(r"[a-zñ0]+", text)


def _shingles(words: list[str]) -> set[str]:
    if len(words) < 3:
        return {" ".join(words)} if words else set()
    return {" ".join(words[i:i + 3]) for i in range(len(words) - 2)}


def fingerprint(text: str) -> list[int] | None:
    shingles = _shingles(_normalize(text))
    if len(shingles) < 3:
        return None  # too short to say anything about campaigns
    hashes = [int.from_bytes(hashlib.blake2b(s.encode(), digest_size=8).digest(), "big") for s in shingles]
    return [min((a * h + b) % _PRIME for h in hashes) for a, b in _PERMS]


def similarity(a: list[int] | None, b: list[int] | None) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    return sum(x == y for x, y in zip(a, b)) / len(a)
