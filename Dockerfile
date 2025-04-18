FROM python:3.13-slim

RUN apt update && apt install -y libreoffice poppler-utils --no-install-recommends
RUN apt install -y pandoc git ssh

COPY ./requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY ./src/pdferret /app/pdferret
CMD ["fastapi", "run", "/app/pdferret/api/server.py", "--port", "80", "--workers", "4"]
