FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY templates ./templates
COPY static ./static

ENV PYTHONUNBUFFERED=1

CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5050", "app:create_app()"]
