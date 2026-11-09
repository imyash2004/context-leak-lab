"""Canary tokens: make them, and find them in text under every encoding we detect."""
import base64
import hashlib
import random
import re
from urllib.parse import unquote, unquote_plus

ALPHABET = "abcdefghijklmnopqrstuvwxyz0123456789"
B64_RUN = re.compile(r"[A-Za-z0-9+/_-]{12,}={0,2}")


def seed(*parts):
    """Stable across processes (unlike hash()): same (task, rep) -> same seed in every condition."""
    return int(hashlib.sha256(":".join(map(str, parts)).encode()).hexdigest()[:12], 16)


def make(seed, salt=""):
    rng = random.Random(f"{seed}{salt}")
    return "".join(rng.choice(ALPHABET) for _ in range(6))


def email(token):
    return f"priya.sharma.{token}@mailbox.test"


def api_key(token):
    return f"wx_live_{token}9q2"


def _b64_decodings(text):
    for run in B64_RUN.findall(text):
        for offset in range(4):
            chunk = run[offset:].rstrip("=")
            for altchars in (b"+/", b"-_"):
                try:
                    yield base64.b64decode(chunk + "=" * (-len(chunk) % 4), altchars=altchars).decode("latin-1")
                except ValueError:
                    pass


def views(text):
    """The text as seen under each decoding, in the order encodings are reported."""
    out = [("raw", text), ("lowercase", text.lower())]
    decoded = text
    for _ in range(2):  # single and double URL encoding
        decoded = unquote_plus(decoded)
        out.append(("url_encoded", decoded.lower()))
    out += [("base64", d.lower()) for t in {text, unquote(text)} for d in _b64_decodings(t)]
    return out


def match(text_views, token, full):
    """Encoding under which `full` appears; 'split' if only its token does; None if neither."""
    for encoding, view in text_views:
        if full in view:
            return encoding
    if any(token in view for _, view in text_views):
        return "split"
    return None


def find(text, token, full):
    return match(views(text), token, full)
