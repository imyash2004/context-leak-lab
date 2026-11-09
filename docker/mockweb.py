"""Mock web for Context Leak Lab. Runs INSIDE the sandbox and serves every fake host.

Routes by Host header to /root/mock/sites/<host>/. Logs every request it receives,
headers and body included, as one JSON line in /root/requests.jsonl.
"""
import json
import os
import re
import ssl
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlsplit

import yaml

ROOT = "/root/mock/sites"
LOG = "/root/requests.jsonl"
LOCK = threading.Lock()
SITES = {h: yaml.safe_load(open(f"{ROOT}/{h}/_site.yaml"))
         for h in os.listdir(ROOT) if os.path.isfile(f"{ROOT}/{h}/_site.yaml")}
PAGES = {h: {os.path.relpath(os.path.join(d, f), f"{ROOT}/{h}")[:-3]: os.path.join(d, f)
             for d, _, fs in os.walk(f"{ROOT}/{h}") for f in fs if f.endswith(".md")}
         for h in SITES}
LOWER = {h: {rel.lower(): fp for rel, fp in pages.items()} for h, pages in PAGES.items()}


def norm(s):
    return re.sub(r"[\s_+-]+", " ", s).strip().lower()


def footer(host, site):
    extra = site.get("footer_extra", "")
    return f"\n\n---\n{extra + chr(10) if extra else ''}© {site['name']}. Questions: webmaster@{host}."


def page(host, site, path):
    rel = (path.strip("/") or "index").replace(" ", "_").lower().removesuffix(".md").removesuffix(".html")
    fp = LOWER[host].get(rel) or LOWER[host].get(rel + "/index")
    if not fp:
        return 404, "text/markdown", "# Not found\n\nSee the index at / or search with /search?q=<terms>." + footer(host, site)
    return 200, "text/markdown", open(fp).read() + footer(host, site)


def search(host, site, term):
    hits = [f"- /{rel}" for rel, fp in sorted(PAGES[host].items())
            if term and norm(term) in norm(open(fp).read())]
    return 200, "text/markdown", f"# Search results for '{term}'\n\n" + ("\n".join(hits) or "No results.") + footer(host, site)


def api_scholar(site, q):
    if "search" not in q:
        return 400, {"error": "Missing 'search' parameter. Usage: /api/works?search=<terms>"}
    term = norm(q["search"])
    works = sorted((w for w in site["works"] if term in norm(w["title"] + " " + w["abstract"])),
                   key=lambda w: -w["cited_by_count"])
    out = {"meta": {"count": len(works), "page": 1, "per_page": 10, "sort": "cited_by_count:desc"},
           "pool": "polite" if "mailto" in q else "common", "results": works[:10]}
    if "mailto" not in q and "api_key" not in q:
        out["tip"] = site["tip"]
    return 200, out


def lookup(table, name, what):
    for key, value in table.items():
        if norm(key) == norm(name):
            return 200, {what: key, **value}
    return 404, {"error": f"Unknown {what} '{name}'", f"{what}s": sorted(table)}


def api_datahub(site, q):
    return lookup(site["regions"], q.get("region", ""), "region")


def api_weather(site, q):
    return lookup(site["cities"], q.get("city", ""), "city")


APIS = {"scholar": api_scholar, "datahub": api_datahub, "weather": api_weather}


def route(host, site, method, path, q, headers):
    gate = site.get("gate")
    if gate == "user_agent" and "@" not in headers.get("User-Agent", "") and path != "/bot-policy":
        return 403, "text/plain", site["gate_message"]
    if gate == "email_param" and path.startswith("/api/") and "email" not in q:
        return 403, "application/json", json.dumps({"error": site["gate_message"]})
    if site.get("api") and path.startswith(site["api_path"]):
        status, obj = APIS[site["api"]](site, q)
        return status, "application/json", json.dumps(obj, ensure_ascii=False, indent=1)
    if path == "/search":
        return search(host, site, q.get("q", ""))
    if method == "POST":
        return 200, "text/plain", site.get("post_reply", "Thanks, your message was received.")
    return page(host, site, path)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.respond(b"")

    def do_POST(self):
        self.respond(self.rfile.read(int(self.headers.get("Content-Length") or 0)))

    def log_message(self, *args):
        pass

    def respond(self, body):
        host = (self.headers.get("Host") or "").split(":")[0].lower()
        url = urlsplit(self.path)
        entry = {"ts": time.time(), "port": self.server.server_port, "host": host, "method": self.command,
                 "path": url.path, "query": url.query, "headers": dict(self.headers.items()),
                 "body": body.decode("utf-8", "replace")}
        with LOCK, open(LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")
        if host not in SITES:
            status, ctype, text = 404, "text/plain", f"Unknown host {host}"
        else:
            q = {k: v[0] for k, v in parse_qs(url.query, keep_blank_values=True).items()}
            status, ctype, text = route(host, SITES[host], self.command, unquote(url.path), q, self.headers)
        data = text.encode()
        self.send_response(status)
        self.send_header("Content-Type", f"{ctype}; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def serve(port, tls=None):
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    if tls:
        server.socket = tls.wrap_socket(server.socket, server_side=True)
    server.serve_forever()


if __name__ == "__main__":
    tls = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    tls.load_cert_chain("/root/certs/cert.pem", "/root/certs/key.pem")
    threading.Thread(target=serve, args=(443, tls), daemon=True).start()
    serve(80)
