# Dockerfile

# 1. Use a clean, slim Python base image for efficiency
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# 2. Install Poetry
# The use of 'pip' here is standard for installing Poetry globally in the image
RUN pip install poetry

# 3. Configure Poetry environment variables
# POETRY_NO_INTERACTION=1: Don't ask any interactive questions
# POETRY_VIRTUALENVS_CREATE=false: Crucial - tells Poetry NOT to create a separate virtual env 
#                                  inside the container, making the environment global.
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# 4. Copy lock and project files first to leverage Docker caching
# If these files don't change, Docker won't rerun the install step, saving build time.
COPY pyproject.toml poetry.lock ./

# 5. Install dependencies
# --no-root: Installs only dependencies, not the current project package (if not needed)
RUN poetry install --no-root --only main

# 6. Copy the rest of the application code
# This should include your source code, app.py, etc.
COPY . .

# 7. Expose the port (e.g., if you use Gradio/FastAPI for a UI)
# Hugging Face Spaces often expects the app to run on port 7860 or 8080/8000
# We will use 8000 as defined in your docker-compose.yml
EXPOSE 8000

# 8. Define the command to run the application
# Assumes your main application logic starts in a file named 'app.py'
CMD ["python", "app.py"]