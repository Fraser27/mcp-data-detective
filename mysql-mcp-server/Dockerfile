# Use Ubuntu as base image
FROM ubuntu:22.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Set build arguments for MySQL (more secure than ENV)
ARG MYSQL_ROOT_PASSWORD=rootpassword
ARG MYSQL_DATABASE=testdb
ARG MYSQL_USER=testuser
ARG MYSQL_PASSWORD=testpassword

# Set environment variables for MySQL (non-sensitive ones)
ENV MYSQL_DATABASE=testdb
ENV MYSQL_USER=testuser

# Update package list and install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    python3-venv \
    mysql-server \
    mysql-client \
    default-libmysqlclient-dev \
    pkg-config \
    gcc \
    g++ \
    curl \
    wget \
    gnupg \
    lsb-release \
    && rm -rf /var/lib/apt/lists/*

# Set working directory for the MCP server
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN python3 -m pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY mysql_mcp_server.py .
COPY database.py .
COPY __init__.py .
COPY .env .

# Copy sample data for MySQL initialization
COPY sample_data.sql /docker-entrypoint-initdb.d/

# Copy the startup script
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Create directories for MySQL and set permissions
RUN mkdir -p /var/run/mysqld && \
    mkdir -p /var/lib/mysql && \
    chown -R mysql:mysql /var/run/mysqld && \
    chown -R mysql:mysql /var/lib/mysql && \
    chmod 755 /var/run/mysqld && \
    chmod 755 /var/lib/mysql

# Expose ports
EXPOSE 3306 8000

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD mysqladmin ping -h"localhost" && python3 -c "import mysql_mcp_server; print('MCP server is healthy')" || exit 1

# Start the combined services
CMD ["/start.sh"] 