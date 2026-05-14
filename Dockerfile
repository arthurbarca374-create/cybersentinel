FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    nmap \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN wget -q https://github.com/projectdiscovery/nuclei/releases/download/v3.3.9/nuclei_3.3.9_linux_amd64.deb -O /tmp/nuclei.deb \
    && dpkg -i /tmp/nuclei.deb \
    && rm /tmp/nuclei.deb \
    && nuclei -update-templates 2>/dev/null || echo "Nuclei templates update skipped (offline build)"

COPY requirements.txt .
COPY requirements-mcp.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements-mcp.txt 2>/dev/null || true

COPY . .

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
