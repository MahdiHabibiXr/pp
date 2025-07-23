# Use a slim and efficient Python base image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Set the PYTHONPATH environment variable
# This tells Python to look for modules in the /app directory
ENV PYTHONPATH=/app

# Copy the requirements file first to leverage Docker's layer caching
COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code into the container
COPY . .

# Run the application as a module, which is the standard way
# The -u flag ensures that logs are sent straight to the terminal
CMD ["python", "-u", "-m", "src.main"]