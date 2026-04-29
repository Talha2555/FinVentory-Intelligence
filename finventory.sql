-- =========================================
-- 1. CREATE DATABASE
-- =========================================
CREATE DATABASE finventory_db;

-- Connect to DB (run separately in psql)
-- \c finventory_db;


-- =========================================
-- 2. PRODUCTS TABLE
-- =========================================
CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    cost_price NUMERIC(10,2) NOT NULL,
    selling_price NUMERIC(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_price CHECK (selling_price >= cost_price)
);


-- =========================================
-- 3. INVENTORY TABLE
-- =========================================
CREATE TABLE inventory (
    inventory_id SERIAL PRIMARY KEY,
    product_id INT UNIQUE,
    quantity INT NOT NULL DEFAULT 0,
    reorder_level INT DEFAULT 10,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (product_id)
    REFERENCES products(product_id)
    ON DELETE CASCADE,

    CONSTRAINT check_quantity CHECK (quantity >= 0)
);


-- =========================================
-- 4. SALES TABLE
-- =========================================
CREATE TABLE sales (
    sale_id SERIAL PRIMARY KEY,
    sale_date DATE NOT NULL,
    total_amount NUMERIC(10,2) DEFAULT 0
);


-- =========================================
-- 5. SALES ITEMS (JUNCTION TABLE)
-- =========================================
CREATE TABLE sales_items (
    sale_item_id SERIAL PRIMARY KEY,
    sale_id INT,
    product_id INT,
    quantity INT NOT NULL,
    price NUMERIC(10,2) NOT NULL,

    FOREIGN KEY (sale_id)
    REFERENCES sales(sale_id)
    ON DELETE CASCADE,

    FOREIGN KEY (product_id)
    REFERENCES products(product_id),

    CONSTRAINT check_sales_qty CHECK (quantity > 0)
);


-- =========================================
-- 6. PURCHASES TABLE
-- =========================================
CREATE TABLE purchases (
    purchase_id SERIAL PRIMARY KEY,
    purchase_date DATE NOT NULL,
    supplier VARCHAR(100),
    total_cost NUMERIC(10,2) DEFAULT 0
);


-- =========================================
-- 7. PURCHASE ITEMS TABLE
-- =========================================
CREATE TABLE purchase_items (
    purchase_item_id SERIAL PRIMARY KEY,
    purchase_id INT,
    product_id INT,
    quantity INT NOT NULL,
    cost NUMERIC(10,2) NOT NULL,

    FOREIGN KEY (purchase_id)
    REFERENCES purchases(purchase_id)
    ON DELETE CASCADE,

    FOREIGN KEY (product_id)
    REFERENCES products(product_id),

    CONSTRAINT check_purchase_qty CHECK (quantity > 0)
);


-- =========================================
-- 8. EXPENSES TABLE
-- =========================================
CREATE TABLE expenses (
    expense_id SERIAL PRIMARY KEY,
    expense_type VARCHAR(50),
    amount NUMERIC(10,2) NOT NULL,
    expense_date DATE NOT NULL,
    CONSTRAINT check_expense CHECK (amount > 0)
);


-- =========================================
-- 9. ALERTS TABLE
-- =========================================
CREATE TABLE alerts (
    alert_id SERIAL PRIMARY KEY,
    message TEXT,
    alert_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'UNREAD'
);


-- =========================================
-- 10. DEMAND PREDICTIONS
-- =========================================
CREATE TABLE demand_predictions (
    prediction_id SERIAL PRIMARY KEY,
    product_id INT,
    prediction_date DATE,
    predicted_quantity NUMERIC(10,2),

    FOREIGN KEY (product_id)
    REFERENCES products(product_id)
);


-- =========================================
-- 11. ROLES TABLE
-- =========================================
CREATE TABLE roles (
    role_id SERIAL PRIMARY KEY,
    role_name VARCHAR(50) UNIQUE NOT NULL
);


-- =========================================
-- 12. USERS TABLE
-- =========================================
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role_id INT,

    FOREIGN KEY (role_id)
    REFERENCES roles(role_id)
);


-- =========================================
-- 13. INSERT DEFAULT ROLES
-- =========================================
INSERT INTO roles (role_name)
VALUES ('Admin'), ('Manager'), ('Staff');


-- =========================================
-- 14. TRIGGER FUNCTIONS
-- =========================================

-- Inventory decrease after sale
CREATE OR REPLACE FUNCTION update_inventory_after_sale()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE inventory
    SET quantity = quantity - NEW.quantity,
        last_updated = CURRENT_TIMESTAMP
    WHERE product_id = NEW.product_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- Inventory increase after purchase
CREATE OR REPLACE FUNCTION update_inventory_after_purchase()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE inventory
    SET quantity = quantity + NEW.quantity,
        last_updated = CURRENT_TIMESTAMP
    WHERE product_id = NEW.product_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- Low stock alert
CREATE OR REPLACE FUNCTION check_low_stock()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.quantity < NEW.reorder_level THEN
        INSERT INTO alerts (message, alert_type)
        VALUES ('Low stock for product ID: ' || NEW.product_id, 'LOW_STOCK');
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- High expense alert
CREATE OR REPLACE FUNCTION check_high_expense()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.amount > 50000 THEN
        INSERT INTO alerts (message, alert_type)
        VALUES ('High expense: ' || NEW.amount, 'HIGH_EXPENSE');
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- Prevent negative stock
CREATE OR REPLACE FUNCTION prevent_negative_stock()
RETURNS TRIGGER AS $$
DECLARE current_qty INT;
BEGIN
    SELECT quantity INTO current_qty
    FROM inventory
    WHERE product_id = NEW.product_id;

    IF current_qty < NEW.quantity THEN
        RAISE EXCEPTION 'Not enough stock!';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- =========================================
-- 15. TRIGGERS
-- =========================================

CREATE TRIGGER trg_after_sale
AFTER INSERT ON sales_items
FOR EACH ROW
EXECUTE FUNCTION update_inventory_after_sale();


CREATE TRIGGER trg_after_purchase
AFTER INSERT ON purchase_items
FOR EACH ROW
EXECUTE FUNCTION update_inventory_after_purchase();


CREATE TRIGGER trg_low_stock
AFTER UPDATE ON inventory
FOR EACH ROW
EXECUTE FUNCTION check_low_stock();


CREATE TRIGGER trg_high_expense
AFTER INSERT ON expenses
FOR EACH ROW
EXECUTE FUNCTION check_high_expense();


CREATE TRIGGER trg_check_stock
BEFORE INSERT ON sales_items
FOR EACH ROW
EXECUTE FUNCTION prevent_negative_stock();


-- =========================================
-- 16. VIEWS (FOR DASHBOARD)
-- =========================================

-- Monthly Sales
CREATE VIEW monthly_sales_view AS
SELECT 
    DATE_TRUNC('month', sale_date) AS month,
    SUM(total_amount) AS revenue
FROM sales
GROUP BY month;


-- Inventory Status
CREATE VIEW inventory_status_view AS
SELECT 
    p.name,
    i.quantity,
    i.reorder_level,
    CASE 
        WHEN i.quantity < i.reorder_level THEN 'LOW'
        ELSE 'OK'
    END AS status
FROM inventory i
JOIN products p ON i.product_id = p.product_id;


-- Product Performance
CREATE VIEW product_performance_view AS
SELECT 
    p.name,
    SUM(si.quantity) AS total_sold,
    SUM(si.quantity * si.price) AS revenue
FROM sales_items si
JOIN products p ON si.product_id = p.product_id
GROUP BY p.name;


-- Profit Summary
CREATE VIEW profit_summary AS
SELECT 
    (SELECT SUM(total_amount) FROM sales) AS total_revenue,
    (SELECT SUM(total_cost) FROM purchases) AS total_cost,
    (SELECT SUM(amount) FROM expenses) AS total_expenses;


-- =========================================
-- 17. INDEXES (PERFORMANCE)
-- =========================================

CREATE INDEX idx_product_id ON inventory(product_id);
CREATE INDEX idx_sale_date ON sales(sale_date);
CREATE INDEX idx_purchase_date ON purchases(purchase_date);


CREATE TABLE retailers (
    retailer_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    contact VARCHAR(50),
    address TEXT
);

CREATE TABLE suppliers (
    supplier_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    contact VARCHAR(50),
    address TEXT
);

CREATE TABLE transactions (
    transaction_id SERIAL PRIMARY KEY,
    transaction_type VARCHAR(20) NOT NULL, -- SALE or PURCHASE
    reference_id INT, -- sale_id or purchase_id
    retailer_id INT,
    supplier_id INT,
    amount NUMERIC(10,2) NOT NULL,
    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT check_type CHECK (transaction_type IN ('SALE', 'PURCHASE')),

    FOREIGN KEY (retailer_id) REFERENCES retailers(retailer_id),
    FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)
);

CREATE OR REPLACE PROCEDURE record_sale_transaction(
    p_sale_id INT,
    p_retailer_id INT,
    p_amount NUMERIC
)
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO transactions (
        transaction_type,
        reference_id,
        retailer_id,
        amount
    )
    VALUES (
        'SALE',
        p_sale_id,
        p_retailer_id,
        p_amount
    );
END;
$$;

CREATE OR REPLACE PROCEDURE record_purchase_transaction(
    p_purchase_id INT,
    p_supplier_id INT,
    p_amount NUMERIC
)
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO transactions (
        transaction_type,
        reference_id,
        supplier_id,
        amount
    )
    VALUES (
        'PURCHASE',
        p_purchase_id,
        p_supplier_id,
        p_amount
    );
END;
$$;

-- =========================================================
-- 1. INSERT TECH PRODUCTS
-- =========================================================
INSERT INTO products (name, category, cost_price, selling_price) VALUES
('iPhone 15 Pro (256GB)', 'Mobile', 280000.00, 315000.00),
('Samsung Galaxy S24 Ultra', 'Mobile', 310000.00, 345000.00),
('MacBook Air M3 (16GB/512GB)', 'Laptop', 350000.00, 395000.00),
('Dell XPS 15', 'Laptop', 420000.00, 460000.00),
('Apple AirPods Pro 2', 'Accessories', 65000.00, 75000.00),
('Anker 65W GaN Charger', 'Accessories', 12000.00, 16000.00);

-- =========================================================
-- 2. INITIALIZE INVENTORY
-- Setting the base stock so triggers don't block sales
-- =========================================================
INSERT INTO inventory (product_id, quantity, reorder_level) VALUES
(1, 15, 5),   -- iPhones
(2, 12, 4),   -- Samsungs
(3, 8,  2),   -- MacBooks
(4, 5,  2),   -- Dell XPS
(5, 30, 10),  -- AirPods
(6, 45, 15);  -- Chargers

-- =========================================================
-- 3. INSERT SUPPLIERS & RETAILERS
-- =========================================================
INSERT INTO suppliers (name, contact, address) VALUES
('TechBridge Distributions', '0300-1112223', 'I.I Chundrigar Road'),
('Global Silicon Importers', '0321-4445556', 'Saddar Electronics Market');

INSERT INTO retailers (name, contact, address) VALUES
('Walk-in Customer', 'N/A', 'N/A'),
('Corporate Client XYZ', '0333-7778889', 'Tech Park, Shahrah-e-Faisal');

-- =========================================================
-- 4. RECORD PURCHASES (Restocking)
-- =========================================================
INSERT INTO purchases (purchase_date, supplier, total_cost) VALUES
('2026-04-01', 'TechBridge Distributions', 1400000.00),
('2026-04-10', 'Global Silicon Importers', 2100000.00);

-- Insert Purchase Items (Triggers will ADD to inventory)
INSERT INTO purchase_items (purchase_id, product_id, quantity, cost) VALUES
(1, 1, 5, 280000.00), -- Restocked 5 iPhones
(2, 3, 6, 350000.00); -- Restocked 6 MacBooks

-- =========================================================
-- 5. RECORD SALES (Revenue)
-- =========================================================
INSERT INTO sales (sale_date, total_amount) VALUES
('2026-04-12', 390000.00),
('2026-04-18', 1185000.00),
('2026-04-25', 16000.00);

-- Insert Sales Items (Triggers will SUBTRACT from inventory)
INSERT INTO sales_items (sale_id, product_id, quantity, price) VALUES
(1, 1, 1, 315000.00), -- Sold 1 iPhone
(1, 5, 1, 75000.00),  -- Sold 1 AirPods Pro
(2, 3, 3, 395000.00), -- Sold 3 MacBooks (Corporate Order)
(3, 6, 1, 16000.00);  -- Sold 1 Charger

-- =========================================================
-- 6. RECORD EXPENSES
-- =========================================================
INSERT INTO expenses (expense_type, amount, expense_date) VALUES
('Shop Rent', 120000.00, '2026-04-01'),
('Electricity & Internet', 45000.00, '2026-04-05'),
('Software Subscriptions', 15000.00, '2026-04-15');
CALL record_sale_transaction(1, 2, 5000);

CALL record_purchase_transaction(3, 1, 8000);

SELECT * FROM transactions;

SELECT * FROM transactions
WHERE transaction_type = 'SALE';

SELECT * FROM transactions
WHERE transaction_type = 'PURCHASE';

SELECT 
    transaction_type,
    SUM(amount) AS total_amount
FROM transactions
GROUP BY transaction_type;