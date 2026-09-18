FROM python:3.13-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends bash patch tmux \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Install task-specific runtime dependencies here.
