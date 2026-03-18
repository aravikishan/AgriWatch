FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p instance seed_data

EXPOSE 8003

ENV AGRIWATCH_PORT=8003
ENV AGRIWATCH_DEBUG=false

CMD ["python", "app.py"]
