# Production-grade Containerfile for OpsAgent
# Using Red Hat Universal Base Image 9 with Python 3.11
FROM registry.redhat.io/ubi9/python-311:1-77

# Production environment variables
ENV APP_HOME=/opt/app-root/src/ops-agent \
    PYTHONPATH=/opt/app-root/src/ops-agent \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create application user (OpenShift compatible - random UID, GID 0)
USER root
RUN mkdir -p ${APP_HOME} && \
    chgrp -R 0 ${APP_HOME} && \
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
COPY --chown=1001:0 config.yaml ./config-template.yaml
COPY --chown=1001:0 langgraph.json ./langgraph.json

# Create directories for runtime data with proper permissions
RUN mkdir -p ./data ./logs && \
    chgrp -R 0 ./data ./logs && \
    chmod -R g=u ./data ./logs

# Set proper permissions for OpenShift SCC compatibility
RUN chgrp -R 0 /opt/app-root && \
    chmod -R g=u /opt/app-root

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
