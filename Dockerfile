# Use official Python base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the bot code
COPY . .

# Run the bot
CMD ["python", "bot.py"]
