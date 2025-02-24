FROM python:3.9-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose ports for both FastAPI and Streamlit
EXPOSE 8000 8501

# Create a script to run both services
COPY start.sh .
RUN chmod +x start.sh

# Run both services using the start script
CMD ["./start.sh"] 