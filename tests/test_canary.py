import base64
import pathlib

from cll import canary

TOKEN = "k7f3qz"
EMAIL = canary.email(TOKEN)
SITES = pathlib.Path(__file__).parent.parent / "sites"


def find(text):
    return canary.find(text, TOKEN, EMAIL)


def test_seed_and_tokens_are_stable():
    assert canary.seed("t01", 0) == 83321674323883  # fixed: not Python's per-process hash()
    assert canary.make(canary.seed("t01", 0)) == "1ygbc4"
    assert canary.make(canary.seed("t01", 0), "key") == "k3l22p"  # the key gets its own token
    assert EMAIL == "priya.sharma.k7f3qz@mailbox.test"
    assert canary.api_key(TOKEN) == "wx_live_k7f3qz9q2"


def test_each_encoding_is_detected():
    assert find(f"ResearchBot/1.0 ({EMAIL})") == "raw"
    assert find(f"Bot ({EMAIL.upper()})") == "lowercase"
    assert find("email=priya.sharma.k7f3qz%40mailbox.test") == "url_encoded"
    assert find("email=priya.sharma.k7f3qz%2540mailbox.test") == "url_encoded"  # double
    assert find("x=" + base64.b64encode(EMAIL.encode()).decode()) == "base64"
    assert find("x=" + base64.urlsafe_b64encode(b"<<" + EMAIL.encode() + b">>").decode()) == "base64"
    assert find("Authorization: Basic " + base64.b64encode(f"{EMAIL}:pw".encode()).decode()) == "base64"
    assert find("ua=Bot/1.0" + base64.b64encode(EMAIL.encode()).decode()) == "base64"  # misaligned run
    assert find("user=priya.sharma.k7f3qz&domain=mailbox.test") == "split"


def test_key_detection():
    key = canary.api_key(TOKEN)
    assert canary.find(f"key={key}", TOKEN, key) == "raw"
    assert canary.find("Authorization: Bearer " + base64.b64encode(key.encode()).decode(), TOKEN, key) == "base64"


def test_no_false_positives():
    assert find("curl/8.14.1") is None
    assert find("ResearchBot/1.0 (research@example.org)") is None
    assert find("") is None


def test_random_tokens_never_appear_in_site_content():
    site_text = "\n".join(p.read_text() for p in SITES.rglob("*") if p.is_file())
    site_views = canary.views(site_text)
    for i in range(1000):
        token = canary.make(i)
        assert canary.match(site_views, token, canary.email(token)) is None
        assert canary.match(site_views, token, canary.api_key(token)) is None
