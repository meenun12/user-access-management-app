# Use an official Python runtime as a parent image
FROM python:3.9-slim-buster

ENV APP_HOME /app
WORKDIR /app

# Copy application dependency manifests to the container image.
# Copying this separately prevents re-running pip install on every code change.
COPY requirements.txt /app

# Install production dependencies.
RUN pip install -r requirements.txt

# Copy local code to the container image.
COPY . /app

# Expose port 5000 for the Flask app
EXPOSE 5004

# Run app.py when the container launches
CMD ["python", "app.py"]
