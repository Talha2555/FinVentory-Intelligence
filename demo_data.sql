-- Optional demo data: run once on a fresh empty schema.
BEGIN;
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
CALL record_sale_transaction(1, 1, 390000);
CALL record_sale_transaction(2, 2, 1185000);
CALL record_sale_transaction(3, 1, 16000);
CALL record_purchase_transaction(1, 1, 1400000);
CALL record_purchase_transaction(2, 2, 2100000);
COMMIT;
