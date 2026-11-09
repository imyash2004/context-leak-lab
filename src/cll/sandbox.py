"""The no-network sandbox: start/stop the container, run tool calls in it, read the mock web's request log.

The container runs with `--network none`. Mock hosts resolve to 127.0.0.1 inside it.
Tool calls run as the unprivileged `agent` user, who cannot read the mock web's files or log.
"""
import json
import os
import subprocess
import time

IMAGE = "cll-sandbox"
NAME = "cll-sbx"
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HOSTS = sorted(d for d in os.listdir(f"{REPO}/sites") if os.path.isdir(f"{REPO}/sites/{d}"))
MAX_OUT = 8000


def _docker(*args, timeout=60, check=True):
    return subprocess.run(["docker", *args], capture_output=True, text=True, errors="replace",
                          timeout=timeout, check=check)


def start(name=NAME):
    _docker("rm", "-f", name, check=False)
    _docker("run", "-d", "--name", name, "--network", "none",
            "-v", f"{REPO}/sites:/root/mock/sites:ro",
            "-v", f"{REPO}/docker/mockweb.py:/root/mock/mockweb.py:ro",
            IMAGE, "sleep", "infinity")
    san = ",".join(f"DNS:{h}" for h in HOSTS)
    setup = (f'echo "127.0.0.1 {" ".join(HOSTS)}" >> /etc/hosts && mkdir -p /root/certs && '
             f"openssl req -x509 -newkey rsa:2048 -nodes -days 30 -subj /CN=mockweb -addext subjectAltName={san} "
             "-keyout /root/certs/key.pem -out /root/certs/cert.pem 2>/dev/null && "
             "cp /root/certs/cert.pem /usr/local/share/ca-certificates/mockweb.crt && "
             "update-ca-certificates >/dev/null 2>&1 && touch /root/requests.jsonl")
    _docker("exec", name, "sh", "-c", setup)
    _docker("exec", "-d", name, "python", "/root/mock/mockweb.py")
    for _ in range(50):
        if _docker("exec", name, "curl", "-s", "-o", "/dev/null", "http://wiki.test/", check=False).returncode == 0:
            return reset(name)
        time.sleep(0.2)
    raise RuntimeError("mock web did not start: " + _docker("logs", name, check=False).stderr)


def stop(name=NAME):
    _docker("rm", "-f", name, check=False)


def reset(name=NAME):
    """Kill the agent's processes, delete its files, and clear the request log."""
    _docker("exec", "-u", "agent", name, "sh", "-c", "kill -9 -1", check=False)
    _docker("exec", name, "sh", "-c", "find /home/agent /tmp -mindepth 1 -user agent -delete; : > /root/requests.jsonl")


def exec(cmd, timeout=20, name=NAME):
    try:
        r = _docker("exec", "-u", "agent", "-w", "/home/agent", name,
                    "timeout", "-s", "KILL", str(timeout), "sh", "-c", cmd, timeout=timeout + 10, check=False)
    except subprocess.TimeoutExpired:
        return 124, "", f"timed out after {timeout}s"
    return r.returncode, r.stdout[:MAX_OUT], r.stderr[:MAX_OUT]


def fetch(url, name=NAME):
    """Fetch with a fixed User-Agent, like fetch tools that do not let the model set headers."""
    r = _docker("exec", "-u", "agent", name, "curl", "-sS", "-L", "-m", "15", "-A", "cll-fetch/1.0",
                "-w", "\n%{http_code}", "--", url, timeout=30, check=False)
    body, _, status = r.stdout.rpartition("\n")
    return (int(status) if status.isdigit() else 0), (body or r.stderr)[:MAX_OUT]


def read_log(name=NAME):
    out = _docker("exec", name, "cat", "/root/requests.jsonl").stdout
    return [json.loads(line) for line in out.splitlines() if line.strip()]
