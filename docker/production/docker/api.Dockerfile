# Build stage
FROM python:3.11-slim-bullseye as builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    PYTHONHASHSEED=random \
    APP_HOME=/home/app/api
#    PIP_INDEX_URL=https://mirrors.sustech.edu.cn/pypi/web/simple/

RUN mkdir -p $APP_HOME
WORKDIR $APP_HOME

# Install system dependencies required for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    libc6-dev \
    libffi-dev \
    libmagic1 \
    libmagic-dev \
    && rm -rf /var/lib/apt/lists/*

# Install pip dependencies
COPY ./requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /usr/src/app/wheels -r requirements.txt

# Final stage
FROM python:3.11-slim-bullseye

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_HOME=/home/app/api \
    PYTHONHASHSEED=random \
    DJANGO_SETTINGS_MODULE=config.settings \
    HOME=/home/app
#    PIP_INDEX_URL=https://mirrors.sustech.edu.cn/pypi/web/simple/

RUN mkdir -p $APP_HOME

# Set work directory
WORKDIR $APP_HOME

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    libpq5 \
    libmagic1 \
    libpq-dev \
    libc6-dev \
    libffi-dev \
    libmagic1 \
    libmagic-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create appropriate directories and user
RUN mkdir -p $APP_HOME/staticfiles \
    && mkdir -p $APP_HOME/media \
    && mkdir -p $APP_HOME/logs \
    && groupadd -r app \
    && useradd -r -g app app -d $HOME \
    && chown -R app:app $HOME

# Copy wheels from builder stage
COPY --from=builder /usr/src/app/wheels /wheels
COPY --from=builder /home/app/api/requirements.txt .

# Install dependencies
RUN pip install --no-cache /wheels/*

# Copy project code
COPY --chown=app:app . $APP_HOME/

# Create and set permissions for required directories
RUN chmod +x $APP_HOME/docker/entrypoint.sh \
    && chown -R app:app $APP_HOME

# Switch to non-root user
USER app

# Expose application port
EXPOSE 8089

# Run entrypoint script
CMD ["/home/app/api/docker/entrypoint.sh"]
