# Use the official Python image from Docker Hub
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y libpq-dev build-essential

# Copy the requirements.txt file into the container
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Python scripts into the container
COPY . .

# Expose any necessary ports (if the scripts run a server)
EXPOSE 8000

# Command to run the script (adjust based on how you want to run the files)
CMD ["python", "hotel_scrapper.py"]
