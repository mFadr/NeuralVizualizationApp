# 1. Use an official, lightweight Python image
FROM python:3.10-slim

# 2. Prevent Python from writing .pyc files to disk and keep stdout unbuffered for logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3. Set the working directory inside the container
WORKDIR /app

# 4. Copy your requirements file first (this helps with caching)
COPY requirements.txt /app/

# 5. Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copy the rest of your project files (Python scripts, CSVs, etc.) into the container
COPY . /app/

# 7. Expose the port that your app runs on (Dash usually defaults to 8050)
EXPOSE 8050

# 8. Command to run the application using Gunicorn
# Note: "chartActive_5datasets:server" means look in chartActive_5datasets.py for the 'server' variable
CMD ["gunicorn", "--bind", "0.0.0.0:8050", "--workers", "3", "--timeout", "120", "chartActive_5datasets:server"]