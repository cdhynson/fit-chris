FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ./app .

# Command to run the application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]


# # Use the official Python image as the base
# FROM python:3.12-slim

# # Set the working directory inside the container
# WORKDIR /app

# # Copy and install dependencies
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# # Copy the entire application code
# COPY . .

# # Expose the port for FastAPI
# EXPOSE 8000

# # Run FastAPI using Uvicorn
# CMD ["uvicorn", "app.app:app", "--host", "0.0.0.0", "--port", "8000"]



# # Use the official Python image
# FROM python:3.12-slim

# # Change WORKDIR to /app/app so "static" is found at /app/app/static
# WORKDIR /app/app

# COPY requirements.txt ../
# RUN pip install --no-cache-dir -r ../requirements.txt

# # Copy everything so /app/app has app.py, static, etc.
# COPY . ..

# ENV PYTHONPATH="/app/app"


# CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "80"]

