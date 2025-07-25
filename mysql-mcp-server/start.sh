#!/bin/bash

# Set MySQL passwords from build args
export MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD:-rootpassword}
export MYSQL_PASSWORD=${MYSQL_PASSWORD:-testpassword}
export MYSQL_DATABASE=${MYSQL_DATABASE:-testdb}
export MYSQL_USER=${MYSQL_USER:-testuser}

# Start MySQL service
service mysql start

# Wait for MySQL to be ready
until mysqladmin ping -h"localhost" --silent; do
    echo "Waiting for MySQL to be ready..."
    sleep 2
done

# Set MySQL root password
mysql -e "ALTER USER 'root'@'localhost' IDENTIFIED BY '$MYSQL_ROOT_PASSWORD';"

# Create database and user if they don't exist
mysql -u root -p$MYSQL_ROOT_PASSWORD -e "CREATE DATABASE IF NOT EXISTS $MYSQL_DATABASE;"
mysql -u root -p$MYSQL_ROOT_PASSWORD -e "CREATE USER IF NOT EXISTS '$MYSQL_USER'@'%' IDENTIFIED BY '$MYSQL_PASSWORD';"
mysql -u root -p$MYSQL_ROOT_PASSWORD -e "CREATE USER IF NOT EXISTS '$MYSQL_USER'@'localhost' IDENTIFIED BY '$MYSQL_PASSWORD';"

# Grant comprehensive privileges to testuser for MCP server functionality
echo "🔧 Setting up comprehensive privileges for $MYSQL_USER..."

# Grant database-specific privileges
mysql -u root -p$MYSQL_ROOT_PASSWORD -e "GRANT ALL PRIVILEGES ON $MYSQL_DATABASE.* TO '$MYSQL_USER'@'%';"
mysql -u root -p$MYSQL_ROOT_PASSWORD -e "GRANT ALL PRIVILEGES ON $MYSQL_DATABASE.* TO '$MYSQL_USER'@'localhost';"

# Grant INFORMATION_SCHEMA access (fixes the main issue)
mysql -u root -p$MYSQL_ROOT_PASSWORD -e "GRANT SELECT ON information_schema.* TO '$MYSQL_USER'@'%';"
mysql -u root -p$MYSQL_ROOT_PASSWORD -e "GRANT SELECT ON information_schema.* TO '$MYSQL_USER'@'localhost';"

# Grant database visibility privileges
mysql -u root -p$MYSQL_ROOT_PASSWORD -e "GRANT SHOW DATABASES ON *.* TO '$MYSQL_USER'@'%';"
mysql -u root -p$MYSQL_ROOT_PASSWORD -e "GRANT SHOW DATABASES ON *.* TO '$MYSQL_USER'@'localhost';"

# Grant read/write access to all databases (for MCP server functionality)
mysql -u root -p$MYSQL_ROOT_PASSWORD -e "GRANT SELECT, INSERT, UPDATE, DELETE ON *.* TO '$MYSQL_USER'@'%';"
mysql -u root -p$MYSQL_ROOT_PASSWORD -e "GRANT SELECT, INSERT, UPDATE, DELETE ON *.* TO '$MYSQL_USER'@'localhost';"

# Apply all privilege changes
mysql -u root -p$MYSQL_ROOT_PASSWORD -e "FLUSH PRIVILEGES;"

# Verify privileges were set correctly
echo "✅ Verifying privileges for $MYSQL_USER..."
mysql -u root -p$MYSQL_ROOT_PASSWORD -e "SHOW GRANTS FOR '$MYSQL_USER'@'%';" || echo "⚠️ Could not show grants for '%' host"
mysql -u root -p$MYSQL_ROOT_PASSWORD -e "SHOW GRANTS FOR '$MYSQL_USER'@'localhost';" || echo "⚠️ Could not show grants for 'localhost' host"

# Import sample data if it exists
# Don't rerun this script when container is restarted
if [ -f /docker-entrypoint-initdb.d/sample_data.sql ]; then
    echo "📊 Loading sample data..."
    mysql -u root -p$MYSQL_ROOT_PASSWORD $MYSQL_DATABASE < /docker-entrypoint-initdb.d/sample_data.sql
    echo "✅ Sample data loaded successfully"
fi

# Set environment variables for the MCP server
export MYSQL_HOST=localhost
export MYSQL_PORT=3306
export MYSQL_USER=$MYSQL_USER
export MYSQL_PASSWORD=$MYSQL_PASSWORD
export MYSQL_DATABASE=$MYSQL_DATABASE

# Start the MCP server
cd /app && python3 mysql_mcp_server.py 