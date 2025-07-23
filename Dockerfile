# Use a slim and efficient Python base image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt requirements.txt
RUN python -m pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code into the container
COPY ./src /app/src

# This is the command that will run when the container starts
CMD ["python", "-u", "src/main.py"]