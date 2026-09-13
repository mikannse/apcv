# apcv-probe: minimal sandbox runtime for executing boundary-violation probes.
#
# Phase 1 (shell probes): the executor runs them via
#   `docker run --network=none --read-only --user=1000:1000 ... /bin/sh -c <cmd>`.
#
# Phase 2 (agent probes): the executor mounts the agent file at /agent and runs
#   entrypoint.py inside the container, which loads the agent, builds a
#   ProbeHost, execs the probe, and prints traces as JSON. Neither agent tool
#   code nor probe payloads ever execute on the host.
FROM python:3.11-slim

# Probe commands need a handful of standard tools to exercise boundary
# behavior (curl/nc for network, sudo/su/setcap for privilege escalation).
# They are NOT a privilege-escalation surface: the container runs as non-root
# with caps dropped by the executor's docker run flags.
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        netcat-openbsd \
        dnsutils \
        sudo \
        libcap2-bin \
        procps \
    && rm -rf /var/lib/apt/lists/*

# apcv execution machinery (probe_host, tracer, trace_model) needs pydantic +
# wrapt. Install them so entrypoint.py can import apcv inside the container.
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Create a non-root user matching the executor's --user=1000:1000.
RUN groupadd -g 1000 probe && useradd -m -u 1000 -g 1000 probe
USER probe

WORKDIR /app

# Ship the apcv package (for entrypoint.py imports) and the entrypoint itself.
# Build context is the project root (see build command), so source paths are
# relative to the project root.
COPY apcv /app/apcv
COPY docker/apcv-probe/entrypoint.py /app/entrypoint.py

ENV PYTHONPATH=/app

ENTRYPOINT ["python", "/app/entrypoint.py"]
