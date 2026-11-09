FROM python:3.12-slim
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl openssl ca-certificates \
 && rm -rf /var/lib/apt/lists/* \
 && pip install --no-cache-dir pyyaml \
 && useradd -m agent
# The agent's tools run as `agent`; mock-web files live under /root, which `agent` cannot read.
