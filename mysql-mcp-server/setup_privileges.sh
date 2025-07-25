#!/bin/bash

# MySQL Privilege Setup Script
# This script grants necessary privileges to testuser for the MCP server

echo "🔧 Setting up MySQL privileges for testuser..."

# Check if MySQL is running
if ! mysqladmin ping -h"${MYSQL_HOST:-localhost}" --silent; then
    echo "❌ MySQL server is not running or not accessible"
    exit 1
fi

# Prompt for root password
echo "Please enter MySQL root password:"
read -s ROOT_PASSWORD

# Execute privilege setup
mysql -u root -p"$ROOT_PASSWORD" -h"${MYSQL_HOST:-localhost}" << EOF
-- Grant access to INFORMATION_SCHEMA (fixes the main issue)
GRANT SELECT ON information_schema.* TO 'testuser'@'%';
GRANT SELECT ON information_schema.* TO 'testuser'@'localhost';

-- Grant database visibility privileges  
GRANT SHOW DATABASES ON *.* TO 'testuser'@'%';
GRANT SHOW DATABASES ON *.* TO 'testuser'@'localhost';

-- Grant read/write access to all databases
GRANT SELECT, INSERT, UPDATE, DELETE ON *.* TO 'testuser'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON *.* TO 'testuser'@'localhost';

-- Apply the changes
FLUSH PRIVILEGES;

-- Show the grants to verify
SHOW GRANTS FOR 'testuser'@'%';
SHOW GRANTS FOR 'testuser'@'localhost';
EOF

if [ $? -eq 0 ]; then
    echo "✅ Privileges setup completed successfully!"
    echo "🔍 Testing connection with testuser..."
    
    # Test the connection
    mysql -u testuser -p"${MYSQL_PASSWORD}" -h"${MYSQL_HOST:-localhost}" -e "SHOW DATABASES;" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        echo "✅ testuser can now access databases properly!"
    else
        echo "⚠️  Privileges set, but testuser connection test failed. Check password and host settings."
    fi
else
    echo "❌ Failed to setup privileges. Check root password and MySQL connection."
    exit 1
fi