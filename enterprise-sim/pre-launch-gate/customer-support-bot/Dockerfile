# SupportBot runtime image.
FROM python:3.11-slim AS build
WORKDIR /app
COPY pyproject.toml ./
COPY src/ ./src/
RUN pip install --no-cache-dir .

FROM python:3.11-slim
WORKDIR /app
COPY --from=build /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY src/ ./src/
# Run as non-root; the container still mounts /etc and /var/run/secrets,
# which is why raw-filesystem tools are a release-gate concern.
RUN useradd -r -u 10001 supportbot
USER supportbot
CMD ["support-bot"]
