FROM amazonlinux:2023

# Install Java and other dependencies
RUN dnf update -y && dnf install -y java-21-amazon-corretto-devel shadow-utils
ENV JAVA_HOME=/usr/lib/jvm/java-21-amazon-corretto 
ENV PATH=$PATH:$JAVA_HOME/bin

RUN curl -SL https://artifacts.opensearch.org/releases/bundle/opensearch/3.x/opensearch-3.x.repo -o /etc/yum.repos.d/opensearch-3.x.repo
RUN yum clean all
RUN yum repolist
RUN yum list opensearch --showduplicates -y
RUN env OPENSEARCH_INITIAL_ADMIN_PASSWORD=admin yum install opensearch -y

# Create opensearch user and set permissions
RUN chown -R opensearch:opensearch /usr/share/opensearch /etc/opensearch /var/log/opensearch /var/lib/opensearch

# Configure OpenSearch for single-node setup without security
RUN echo "plugins.security.disabled: true" >> /etc/opensearch/opensearch.yml && \
    echo "discovery.type: single-node" >> /etc/opensearch/opensearch.yml

# Install Python 3.12 and other dependencies
RUN dnf install -y \
    python3.12 \
    python3.12-pip \
    python3.12-devel \
    gcc \
    gcc-c++ \
    wget \
    && dnf clean all

# Create symbolic links for python3 and pip
RUN ln -sf /usr/bin/python3.12 /usr/bin/python3 && \
    ln -sf /usr/bin/pip3.12 /usr/bin/pip


# Set working directory for the MCP server
WORKDIR /app
RUN chown -R opensearch:opensearch /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN python3 -m pip install --no-cache-dir -r requirements.txt
COPY opensearch_mcp_server.py .
COPY sample_data.py .
COPY database.py .

# Create .env file from template if it doesn't exist
COPY env.example .env

# Copy the startup script to the correct location
COPY start.sh /start.sh
RUN chmod +x /start.sh && chown opensearch:opensearch /start.sh

# Switch to opensearch user
USER opensearch

# Expose ports
EXPOSE 8000
EXPOSE 9200

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

CMD ["/start.sh"]
    
