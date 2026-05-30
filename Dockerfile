FROM python:3.11-slim

WORKDIR /app

# 1. Install WeasyPrint and SpaCy system dependencies (using correct Debian package names)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libmagic1 \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libglib2.0-0 \
    libffi-dev \
    shared-mime-info \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# 2. Copy requirements and install python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. Download the SpaCy model
RUN python -m spacy download en_core_web_sm

# 4. Copy the rest of the application files
COPY . .

# 5. Expose Hugging Face Space port
EXPOSE 7860

# 6. Start FastAPI using Uvicorn
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]