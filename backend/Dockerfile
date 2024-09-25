# Pull official Python base image
FROM python:3.11

# Configure Python logs to stream to stdout without buffering
ENV PYTHONUNBUFFERED 1

# Set working directory in container
WORKDIR /shareholder-tracker/backend

# Install requirements based on declared environment
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy remaining application code to container
COPY . .

# Run the pipeline
CMD ["bash", "setup.sh", "--migrate", "--load-fixtures", "--sync-views",  "--run-server"]