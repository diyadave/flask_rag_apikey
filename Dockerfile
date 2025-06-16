# Use a lightweight Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .

# Install Python packages (ignoring pywin32 which is for Windows)
RUN pip install --no-cache-dir -r requirements.txt

# Copy your entire project to the image
COPY . .

# Expose the port your Flask app runs on
EXPOSE 5000

# Run the app
CMD ["python", "run.py"]
