FROM python:3.11-alpine

WORKDIR /app
COPY app.py /app/app.py
COPY templates /app/templates
COPY events.json /app/events.json

RUN pip install flask --no-cache-dir

EXPOSE 5000
CMD ["python", "app.py"]
