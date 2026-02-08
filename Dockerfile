FROM python:3

WORKDIR /app

COPY . .
RUN pip install --no-cache-dir -r requirements.txt

ENV PORT=8000
EXPOSE 8000