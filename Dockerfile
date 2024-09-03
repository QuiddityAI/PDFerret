FROM downloads.unstructured.io/unstructured-io/unstructured:latest

COPY ./requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY ./src/pdferret /app/pdferret
CMD ["fastapi", "run", "/app/pdferret/api/server.py", "--port", "80", "--workers", "4"]