# Production-grade Containerfile for OpsAgent
# Using Python 3.11 slim image
FROM python:3.11-slim

# Production environment variables
ENV APP_HOME=/opt/app-root/src/ops-agent \
    PYTHONPATH=/opt/app-root/src/ops-agent \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create application directory and user
RUN mkdir -p ${APP_HOME} && \
    useradd -u 1001 -g 0 -d ${APP_HOME} appuser && \
    chown -R 1001:0 ${APP_HOME} && \
    chmod -R g=u ${APP_HOME}

# Set working directory
WORKDIR ${APP_HOME}

# Copy pyproject.toml for dependency installation
COPY --chown=1001:0 pyproject.toml ./

# Install Python dependencies
# Extract dependencies from pyproject.toml and install them
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    "langgraph>=0.2.59" \
    "langchain-openai>=0.2.14" \
    "langchain-mcp-adapters>=0.1.0" \
    "pyyaml>=6.0.1" \
    "pydantic>=2.0.0" \
    "httpx>=0.25.0" \
    "python-dotenv>=1.0.0" \
    "langgraph-cli[inmem]>=0.1.56"

# Copy application code
COPY --chown=1001:0 app/ ./app/
COPY --chown=1001:0 config.yaml.example ./config.yaml
COPY --chown=1001:0 langgraph.json ./langgraph.json

# Create directories for runtime data with proper permissions
RUN mkdir -p ./data ./logs && \
    chown -R 1001:0 ./data ./logs && \
    chmod -R g=u ./data ./logs

# Switch to non-root user
USER 1001

# Working directory should be root (where langgraph.json is)
WORKDIR ${APP_HOME}

# Health check endpoint (LangGraph dev server provides health check)
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:2024/ok')" || exit 1

# Expose port for LangGraph server
EXPOSE 2024

# Default command (can be overridden in OpenShift deployment)
CMD ["langgraph", "dev", "--host", "0.0.0.0", "--port", "2024", "--no-browser"]
