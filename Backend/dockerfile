FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download Vosk model
RUN apt-get update && apt-get install -y curl unzip
RUN mkdir -p vosk-model-small-en-us-0.15
RUN curl -L https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip -o model.zip \
    && unzip model.zip \
    && mv vosk-model-small-en-us-0.15/* vosk-model-small-en-us-0.15/ \
    && rm model.zip

# Copy application
COPY . .

# Run the application
CMD ["python", "app.py"]