
FROM python:3.14-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

ARG SERVICE

COPY ${SERVICE}/app.py ./app.py

CMD ["python", "app.py"]
