-- MySQL Privilege Setup for testuser
-- Run this as root user: mysql -u root -p < setup_privileges.sql

-- Grant access to INFORMATION_SCHEMA (fixes the main issue)
GRANT SELECT ON information_schema.* TO 'testuser'@'%';
GRANT SELECT ON information_schema.* TO 'testuser'@'localhost';

-- Grant database visibility privileges
GRANT SHOW DATABASES ON *.* TO 'testuser'@'%';
GRANT SHOW DATABASES ON *.* TO 'testuser'@'localhost';

-- Grant read/write access to all databases (adjust as needed)
GRANT SELECT, INSERT, UPDATE, DELETE ON *.* TO 'testuser'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON *.* TO 'testuser'@'localhost';

-- Apply the changes
FLUSH PRIVILEGES;

-- Show the grants to verify
SHOW GRANTS FOR 'testuser'@'%';
SHOW GRANTS FOR 'testuser'@'localhost';