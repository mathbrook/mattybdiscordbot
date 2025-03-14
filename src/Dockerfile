# Use a lightweight Python image
FROM python:3.11-slim

# Set the working directory
WORKDIR /bot

# Copy only requirements first to leverage caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot files
COPY . .

# Run the bot
CMD ["bash", "-c", "python main.py & python webserver.py"]