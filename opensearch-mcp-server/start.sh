#!/bin/bash

# OpenSearch MCP Server Start Script

# disable performance analyzer
# Opensearch installed at cd /usr/share/opensearch/
# https://docs.opensearch.org/docs/latest/monitoring-your-cluster/pa/index/#disable-performance-analyzer
# curl -XPOST localhost:9200/_plugins/_performanceanalyzer/rca/cluster/config -H 'Content-Type: application/json' -d '{"enabled": false}'
# curl -XPOST localhost:9200/_plugins/_performanceanalyzer/cluster/config -H 'Content-Type: application/json' -d '{"enabled": false}'
# sh opensearch-plugin remove opensearch-performance-analyzer

echo "🔍 Starting OpenSearch MCP Server..."
echo "=================================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed or not in PATH"
    exit 1
fi

# Check if requirements are installed
if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt not found"
    exit 1
fi

# Install requirements if needed
echo "📦 Checking dependencies..."
pip install -r requirements.txt

# Set OpenSearch configuration from environment variables
export OPENSEARCH_HOST=${OPENSEARCH_HOST:-localhost}
export OPENSEARCH_PORT=${OPENSEARCH_PORT:-9200}
export OPENSEARCH_USER=${OPENSEARCH_USER:-admin}
export OPENSEARCH_PASSWORD=${OPENSEARCH_PASSWORD:-admin}
export OPENSEARCH_USE_SSL=${OPENSEARCH_USE_SSL:-false}
export OPENSEARCH_VERIFY_CERTS=${OPENSEARCH_VERIFY_CERTS:-false}

# Test OpenSearch connection
echo "🔗 Testing OpenSearch connection..."
python3 -c "
from database import opensearch_client
if opensearch_client.test_connection():
    print('✅ OpenSearch connection successful')
else:
    print('❌ OpenSearch connection failed')
    print('Please ensure OpenSearch is running and .env is configured correctly')
"

# Start OpenSearch in background
echo "🔍 Starting OpenSearch..."
export OPENSEARCH_JAVA_OPTS="-Dopensearch_performance_analyzer.enabled=false"
/usr/share/opensearch/bin/opensearch &

# Wait for OpenSearch to be ready
echo "⏳ Waiting for OpenSearch to start..."
until curl -f http://localhost:9200/_cluster/health 2>/dev/null; do
    echo "Waiting for OpenSearch to be ready..."
    sleep 5
done

echo "✅ OpenSearch is ready!"


# Optional: Run sample data script to populate with test data
if [ "$POPULATE_SAMPLE_DATA" = "true" ]; then
    echo "📝 Populating sample data..."
    cd /app && python3 sample_data.py
fi

# Start the MCP server
echo "🚀 Starting OpenSearch MCP server..."
cd /app && python3 opensearch_mcp_server.py 