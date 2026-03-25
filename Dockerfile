# Specify base image with Python runtime for Apify
FROM apify/actor-python:3.11

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy remaining files
COPY . .

# Run the main script
CMD ["python", "main.py"]
