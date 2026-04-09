FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/uploads /app/outputs /app/plugins

EXPOSE 5000

CMD ["python", "main.py", "--web", "--host", "0.0.0.0", "--port", "5000"]
