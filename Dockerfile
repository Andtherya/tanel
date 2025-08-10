FROM python:3.11-alpine

WORKDIR /app
COPY app.py /app/app.py
COPY templates /app/templates
COPY events.json /app/events.json

RUN pip install --no-cache-dir flask gunicorn

EXPOSE 5000
ENV PORT=5000

# gunicorn will bind to the chosen PORT env var via a tiny shell wrapper
CMD ["sh", "-c", "exec gunicorn -w 2 -b 0.0.0.0:${PORT} app:app"]
