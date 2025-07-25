-- Sample data for testing the MySQL MCP Server
-- This file will be automatically loaded when using Docker Compose

-- Create schemas
CREATE SCHEMA IF NOT EXISTS ecommerce;
CREATE SCHEMA IF NOT EXISTS iot;

-- ========================================
-- ECOMMERCE SCHEMA
-- ========================================

-- Create ecommerce tables
CREATE TABLE IF NOT EXISTS ecommerce.users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS ecommerce.products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    category VARCHAR(50),
    stock_quantity INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ecommerce.orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    total_amount DECIMAL(10, 2) NOT NULL,
    status ENUM('pending', 'processing', 'shipped', 'delivered', 'cancelled') DEFAULT 'pending',
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    shipped_date TIMESTAMP NULL,
    FOREIGN KEY (user_id) REFERENCES ecommerce.users(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS ecommerce.order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT,
    product_id INT,
    quantity INT NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES ecommerce.orders(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES ecommerce.products(id) ON DELETE CASCADE
);

-- Insert sample ecommerce data
INSERT INTO ecommerce.users (username, email, first_name, last_name) VALUES
('john_doe', 'john.doe@email.com', 'John', 'Doe'),
('jane_smith', 'jane.smith@gmail.com', 'Jane', 'Smith'),
('bob_wilson', 'bob.wilson@yahoo.com', 'Bob', 'Wilson'),
('alice_brown', 'alice.brown@hotmail.com', 'Alice', 'Brown'),
('charlie_davis', 'charlie.davis@gmail.com', 'Charlie', 'Davis');

INSERT INTO ecommerce.products (name, description, price, category, stock_quantity) VALUES
('Laptop Pro', 'High-performance laptop for professionals', 1299.99, 'Electronics', 25),
('Wireless Mouse', 'Ergonomic wireless mouse with long battery life', 29.99, 'Electronics', 150),
('Office Chair', 'Comfortable ergonomic office chair', 199.99, 'Furniture', 45),
('Coffee Mug', 'Ceramic coffee mug with company logo', 12.99, 'Office Supplies', 200),
('Notebook Set', 'Set of 3 premium notebooks', 24.99, 'Office Supplies', 75),
('Desk Lamp', 'LED desk lamp with adjustable brightness', 49.99, 'Furniture', 30),
('Keyboard', 'Mechanical keyboard with RGB lighting', 89.99, 'Electronics', 60),
('Water Bottle', 'Insulated stainless steel water bottle', 19.99, 'Office Supplies', 120);

INSERT INTO ecommerce.orders (user_id, total_amount, status) VALUES
(1, 1329.98, 'delivered'),
(2, 42.98, 'shipped'),
(3, 249.98, 'processing'),
(1, 89.99, 'pending'),
(4, 32.98, 'delivered');

INSERT INTO ecommerce.order_items (order_id, product_id, quantity, unit_price) VALUES
-- Order 1 (John's order)
(1, 1, 1, 1299.99),  -- Laptop Pro
(1, 2, 1, 29.99),    -- Wireless Mouse
-- Order 2 (Jane's order)
(2, 4, 1, 12.99),    -- Coffee Mug
(2, 2, 1, 29.99),    -- Wireless Mouse
-- Order 3 (Bob's order)
(3, 3, 1, 199.99),   -- Office Chair
(3, 6, 1, 49.99),    -- Desk Lamp
-- Order 4 (John's second order)
(4, 7, 1, 89.99),    -- Keyboard
-- Order 5 (Alice's order)
(5, 4, 1, 12.99),    -- Coffee Mug
(5, 8, 1, 19.99);    -- Water Bottle

-- Create ecommerce indexes for better performance
CREATE INDEX idx_ecommerce_users_email ON ecommerce.users(email);
CREATE INDEX idx_ecommerce_products_category ON ecommerce.products(category);
CREATE INDEX idx_ecommerce_orders_user_id ON ecommerce.orders(user_id);
CREATE INDEX idx_ecommerce_orders_status ON ecommerce.orders(status);
CREATE INDEX idx_ecommerce_order_items_order_id ON ecommerce.order_items(order_id);
CREATE INDEX idx_ecommerce_order_items_product_id ON ecommerce.order_items(product_id);

-- ========================================
-- IOT SCHEMA
-- ========================================

-- Create IoT tables
CREATE TABLE IF NOT EXISTS iot.organizations (
    org_id INT PRIMARY KEY,
    org_name VARCHAR(100),
    org_type ENUM('FUEL_BRAND', 'RETAILER', 'MANUFACTURER'),
    headquarters VARCHAR(100),
    contact_email VARCHAR(100),
    contact_phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS iot.sites (
    site_id INT PRIMARY KEY,
    org_id INT,
    site_name VARCHAR(100),
    site_code VARCHAR(50),
    address VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(50),
    postal_code VARCHAR(10),
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    operating_hours VARCHAR(100),
    site_manager VARCHAR(100),
    contact_phone VARCHAR(20),
    FOREIGN KEY (org_id) REFERENCES iot.organizations(org_id)
);

CREATE TABLE IF NOT EXISTS iot.devices (
    device_id VARCHAR(50) PRIMARY KEY,
    site_id INT,
    manufacturer_org_id INT,
    model_number VARCHAR(50),
    serial_number VARCHAR(50),
    device_type VARCHAR(50),
    installation_date DATE,
    last_maintenance_date DATE,
    warranty_expiry_date DATE,
    firmware_version VARCHAR(50),
    FOREIGN KEY (site_id) REFERENCES iot.sites(site_id),
    FOREIGN KEY (manufacturer_org_id) REFERENCES iot.organizations(org_id)
);

CREATE TABLE IF NOT EXISTS iot.nozzles (
    nozzle_id VARCHAR(50) PRIMARY KEY,
    device_id VARCHAR(50),
    fuel_type VARCHAR(50),
    installation_date DATE,
    last_calibration_date DATE,
    FOREIGN KEY (device_id) REFERENCES iot.devices(device_id)
);

-- Insert sample IoT data
INSERT INTO iot.organizations VALUES
(1, 'Shell', 'FUEL_BRAND', 'The Hague, Netherlands', 'contact@shell.com', '+1-888-467-4355', NOW()),
(2, '7-Eleven', 'RETAILER', 'Dallas, TX', 'contact@7eleven.com', '+1-800-255-0711', NOW()),
(3, 'Costco', 'RETAILER', 'Issaquah, WA', 'contact@costco.com', '+1-800-774-2678', NOW()),
(4, 'Wayne Fueling Systems', 'MANUFACTURER', 'Austin, TX', 'contact@wayne.com', '+1-512-388-8311', NOW()),
(5, 'Gilbarco Veeder-Root', 'MANUFACTURER', 'Greensboro, NC', 'contact@gilbarco.com', '+1-336-547-5000', NOW());

INSERT INTO iot.sites VALUES
(1001, 1, 'Shell Downtown Phoenix', 'SHL001', '1501 N Central Ave', 'Phoenix', 'Arizona', '85004', 33.448376, -112.074036, '24/7', 'Michael Rodriguez', '+1-602-555-0101'),
(1002, 1, 'Shell Scottsdale Station', 'SHL002', '7350 E McDowell Rd', 'Scottsdale', 'Arizona', '85257', 33.494170, -111.926064, '24/7', 'Sarah Chen', '+1-480-555-0102'),
(1003, 1, 'Shell Austin Downtown', 'SHL003', '1001 Congress Ave', 'Austin', 'Texas', '78701', 30.267153, -97.743060, '24/7', 'Jennifer Martinez', '+1-512-555-0103'),
(1004, 2, '7-Eleven Tucson East', '7EL001', '1234 E Speedway Blvd', 'Tucson', 'Arizona', '85719', 32.221743, -110.926479, '24/7', 'Patricia Brown', '+1-520-555-0104'),
(1005, 2, '7-Eleven Houston Galleria', '7EL002', '5000 Westheimer Rd', 'Houston', 'Texas', '77056', 29.760427, -95.369804, '24/7', 'Thomas Anderson', '+1-713-555-0105'),
(1006, 3, 'Costco Fuel Station Mesa', 'CST001', '1840 S Signal Butte Rd', 'Mesa', 'Arizona', '85209', 33.415184, -111.831472, '6AM-10PM', 'Daniel Miller', '+1-480-555-0106');

-- Device types: DISPENSER, POS, TANK-GAUGE
INSERT INTO iot.devices VALUES
('DEV_001', 1001, 4, 'Wayne-500', 'SN001234', 'DISPENSER', '2022-01-15', '2023-06-10', '2025-01-15', 'v2.1.0'),
('DEV_002', 1001, 4, 'Wayne-500', 'SN001235', 'DISPENSER', '2022-01-15', '2023-06-10', '2025-01-15', 'v2.1.0'),
('DEV_003', 1001, 5, 'Gilbarco-600', 'SN001236', 'POS', '2022-01-15', '2023-06-10', '2025-01-15', 'v3.0.1'),
('DEV_004', 1001, 5, 'Gilbarco-700', 'SN001237', 'TANK-GAUGE', '2022-01-15', '2023-06-10', '2025-01-15', 'v1.5.2'),
('DEV_005', 1002, 4, 'Wayne-500', 'SN001238', 'DISPENSER', '2022-02-20', '2023-07-15', '2025-02-20', 'v2.1.0'),
('DEV_006', 1002, 5, 'Gilbarco-600', 'SN001239', 'POS', '2022-02-20', '2023-07-15', '2025-02-20', 'v3.0.1'),
('DEV_007', 1003, 4, 'Wayne-500', 'SN001240', 'DISPENSER', '2022-03-10', '2023-08-05', '2025-03-10', 'v2.1.0'),
('DEV_008', 1003, 5, 'Gilbarco-600', 'SN001241', 'POS', '2022-03-10', '2023-08-05', '2025-03-10', 'v3.0.1'),
('DEV_009', 1004, 4, 'Wayne-500', 'SN001242', 'DISPENSER', '2022-04-05', '2023-09-20', '2025-04-05', 'v2.1.0'),
('DEV_010', 1004, 5, 'Gilbarco-600', 'SN001243', 'POS', '2022-04-05', '2023-09-20', '2025-04-05', 'v3.0.1'),
('DEV_011', 1005, 4, 'Wayne-500', 'SN001244', 'DISPENSER', '2022-05-12', '2023-10-15', '2025-05-12', 'v2.1.0'),
('DEV_012', 1005, 5, 'Gilbarco-600', 'SN001245', 'POS', '2022-05-12', '2023-10-15', '2025-05-12', 'v3.0.1'),
('DEV_013', 1006, 4, 'Wayne-500', 'SN001246', 'DISPENSER', '2022-06-18', '2023-11-30', '2025-06-18', 'v2.1.0'),
('DEV_014', 1006, 5, 'Gilbarco-600', 'SN001247', 'POS', '2022-06-18', '2023-11-30', '2025-06-18', 'v3.0.1');

-- Fuel types: REGULAR, PREMIUM, DIESEL
INSERT INTO iot.nozzles VALUES
('NOZ_001', 'DEV_001', 'REGULAR', '2022-01-15', '2023-06-10'),
('NOZ_002', 'DEV_001', 'PREMIUM', '2022-01-15', '2023-06-10'),
('NOZ_003', 'DEV_002', 'DIESEL', '2022-01-15', '2023-06-10'),
('NOZ_004', 'DEV_002', 'REGULAR', '2022-01-15', '2023-06-10'),
('NOZ_005', 'DEV_005', 'REGULAR', '2022-02-20', '2023-07-15'),
('NOZ_006', 'DEV_005', 'PREMIUM', '2022-02-20', '2023-07-15'),
('NOZ_007', 'DEV_007', 'REGULAR', '2022-03-10', '2023-08-05'),
('NOZ_008', 'DEV_007', 'PREMIUM', '2022-03-10', '2023-08-05'),
('NOZ_009', 'DEV_009', 'REGULAR', '2022-04-05', '2023-09-20'),
('NOZ_010', 'DEV_009', 'PREMIUM', '2022-04-05', '2023-09-20'),
('NOZ_011', 'DEV_011', 'REGULAR', '2022-05-12', '2023-10-15'),
('NOZ_012', 'DEV_011', 'PREMIUM', '2022-05-12', '2023-10-15'),
('NOZ_013', 'DEV_013', 'REGULAR', '2022-06-18', '2023-11-30'),
('NOZ_014', 'DEV_013', 'PREMIUM', '2022-06-18', '2023-11-30');

-- Create IoT indexes for better performance
CREATE INDEX idx_iot_sites_org_id ON iot.sites(org_id);
CREATE INDEX idx_iot_sites_city ON iot.sites(city);
CREATE INDEX idx_iot_sites_state ON iot.sites(state);
CREATE INDEX idx_iot_devices_site_id ON iot.devices(site_id);
CREATE INDEX idx_iot_devices_manufacturer_org_id ON iot.devices(manufacturer_org_id);
CREATE INDEX idx_iot_devices_device_type ON iot.devices(device_type);
CREATE INDEX idx_iot_nozzles_device_id ON iot.nozzles(device_id);
CREATE INDEX idx_iot_nozzles_fuel_type ON iot.nozzles(fuel_type);