# iac/debug-tools/Dockerfile
# A lightweight, general-purpose debug image with common networking tools.
FROM debian:bookworm-slim

# Set non-interactive frontend to avoid prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install essential networking and troubleshooting tools
# - curl: for making HTTP requests
# - dnsutils: for nslookup and dig
# - inetutils-telnet: for checking port connectivity
# - procps: for `ps` to see running processes
# - net-tools: for `netstat`
# - iproute2: for `ip addr` and `ip route`
# - vim-tiny: a minimal text editor
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    dnsutils \
    inetutils-telnet \
    procps \
    net-tools \
    iproute2 \
    vim-tiny \
    && rm -rf /var/lib/apt/lists/*

# Keep the container running indefinitely for interactive sessions
CMD ["sleep", "infinity"]