FROM python:3.11-slim
WORKDIR /srv
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app ./app
# One image, many agents: SLUDGE_AGENT picks which agent package to serve.
CMD ["sh", "-c", "exec python -m uvicorn app.agents.${SLUDGE_AGENT}.agent:a2a_app --host 0.0.0.0 --port ${PORT:-8080}"]
