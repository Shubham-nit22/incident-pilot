FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
PYTHONUNBUFFERED=1

WORKDIR /code

#install packages first, so Docker can resuse this layer when only your code changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Run as a normal user instead of root, and give it a place to write its log
RUN useradd --create-home appuser \
    && mkdir -p /code/logs \
    && chown -R appuser:appuser /code
USER appuser

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')" || exist 1

CMD [ "uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8000" ]
