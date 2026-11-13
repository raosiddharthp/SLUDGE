FROM python:3.11-slim
WORKDIR /srv
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app ./app
# One image, many services: SLUDGE_AGENT picks an agent; SLUDGE_APP overrides with any ASGI app path.
CMD ["sh", "-c", "exec python -m uvicorn ${SLUDGE_APP:-app.agents.${SLUDGE_AGENT}.agent:a2a_app} --host 0.0.0.0 --port ${PORT:-8080}"]
