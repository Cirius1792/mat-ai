FROM python:3.12-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app


# Copy application code and install dependencies
COPY . .
RUN uv sync 

# Create directory for configuration
RUN mkdir -p /config

# Set environment variables
ENV PMAI_CONFIG_PATH=/config/config.yaml

# Expose the port NiceGUI runs on
EXPOSE 8080

# Run the application
CMD ["uv", "run", "src/gui/main_gui.py"]
