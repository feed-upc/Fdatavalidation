FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY validation_job.py .

ENTRYPOINT ["python", "validation_job.py"]
