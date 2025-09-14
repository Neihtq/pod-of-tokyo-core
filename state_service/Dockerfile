FROM python:3.13-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 12000

COPY . .
CMD ["python", "main.py"]
